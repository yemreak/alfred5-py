from __future__ import annotations

import json
import sys
from asyncio import run
from collections.abc import Callable, Coroutine
from logging import Logger, StreamHandler
from pathlib import Path
from plistlib import load as plist_load
from shutil import copy2, move
from tempfile import TemporaryDirectory
from traceback import format_exc
from typing import NoReturn
from zipfile import ZIP_DEFLATED, ZipFile

import pkg_resources
from yaml import safe_dump, safe_load

from .errors import WorkflowError
from .models import SNIPPET_INFO_TEMPLATE, Result, Snippet


class SnippetClient:
    snippets: list[Snippet]

    def __init__(self) -> None:
        self.snippets: list[Snippet] = []

    def insert_snippet(self, snippet: str, name: str, keyword: str):
        self.snippets.append(Snippet(snippet, name, keyword))

    def package(
        self,
        name: str,
        dst: str = "",
        prefix: str = "",
        suffix: str = "",
        iconpath: str = "",
    ):
        """Package snippets into a .alfredsnippets file"""
        with TemporaryDirectory() as tempdir:
            workdir = Path(tempdir)
            infopath = workdir / "info.plist"
            infopath.write_text(SNIPPET_INFO_TEMPLATE.format(prefix, suffix))

            snippet_path = workdir / f"{name}.alfredsnippets"
            with ZipFile(snippet_path, "w", ZIP_DEFLATED) as zipfile:
                for snippet in self.snippets:
                    path = snippet.save(workdir)
                    zipfile.write(path, path.name)
                zipfile.write(infopath, infopath.name)
                if iconpath:
                    snippet_iconpath = workdir / "icon.png"
                    copy2(iconpath, snippet_iconpath)
                    zipfile.write(snippet_iconpath, snippet_iconpath.name)

            destination = (Path(dst) if dst else Path.cwd()) / f"{name}.alfredsnippets"
            move(snippet_path, destination)


class WorkflowClient:
    bare_query: str | None
    query: str | None
    page_count: int

    bundleid: str
    package_dir: Path
    icondir: Path
    datadir: Path
    db_results: Path
    results: list[Result]

    logger: Logger

    def __init__(self, package_dir: str = "src/libs") -> None:
        self.logger = Logger("alfred5")
        self.logger.addHandler(StreamHandler(sys.stderr))
        self.log(f"logger initted")

        if len(sys.argv) > 1:
            self.bare_query = sys.argv[1]
            self.page_count = self.bare_query.count("+") + 1
            self.query = self.bare_query.replace("+", "")
        else:
            self.bare_query = None
            self.page_count = 0
            self.query = None

        self.log(
            f"sys.argv: {sys.argv} page_count: {self.page_count} query: {self.query}"
        )

        self.package_dir = Path(package_dir)
        self.icondir = Path(__file__).parent / "icons"

        self.log(f"bundleid reading from info.plist...")
        with Path("info.plist").open("rb") as f:
            self.bundleid = plist_load(f)["bundleid"]
            self.log(f"bundleid: {self.bundleid}")
        self.datadir = Path("db")
        self.datadir.mkdir(parents=True, exist_ok=True)

        self.log(f"datadir: {self.datadir.absolute()}")
        self.db_results = self.datadir / "results.yml"
        self.log(f"db_results: {self.db_results}")

        self.results = []

    def log(self, msg: str):
        self.logger.debug(msg)

    def install_requirements(self) -> None:
        """Check if requirements are met"""
        self.log(f"checking requirements...")
        req_file = self.package_dir / ".." / "requirements.txt"
        if req_file.exists():
            packages = req_file.read_text().splitlines()
            self.log(f"found requirements.txt: {packages}")

            try:
                pkg_resources.require(packages)
            except pkg_resources.DistributionNotFound:
                import subprocess

                command = [
                    "python3",
                    "-m",
                    "pip",
                    "install",
                    f"--target={self.package_dir}",
                    *packages,
                ]
                subprocess.Popen(
                    command,
                    start_new_session=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                self.add_result(
                    title="Requirements are installing (you can close alfred)",
                    subtitle=f"Executed command: {' '.join(command)}",
                    icon_path=self.icondir / "download.png",
                    arg=" ".join(command),
                )
                self.response_with_results()
        else:
            self.log(f"no requirements.txt found")

    def cache_response(self) -> None:
        """Cache response to workflow db_results"""
        if not self.db_results.exists():
            self.db_results.parent.mkdir(parents=True, exist_ok=True)
            self.db_results.touch()
        with self.db_results.open("r") as f:
            data = safe_load(f) or {}
        data[self.bare_query] = [
            {
                "title": result.title,
                "subtitle": result.subtitle,
                "icon_path": result.icon.path if result.icon else None,
                "arg": result.arg,
            }
            for result in self.results
        ]
        with self.db_results.open("w") as f:
            safe_dump(data, f)
            self.log(f"cached response to {self.db_results}")

    def load_cached_response(self) -> bool:
        """Load cached result from alfred"""
        if self.bare_query:
            self.log("skipped, bare_query is None")
            return False

        self.log(f"checking if `{self.bare_query}` exists in `{self.db_results}`")
        if self.db_results.exists():
            with self.db_results.open("r") as f:
                data: dict[str, list[dict[str, str]]] = safe_load(f)
                self.log(f"loaded data from {self.db_results} {len(data.keys())}")
                if self.bare_query and self.bare_query in data:
                    self.results = [
                        Result(
                            title=result["title"],
                            subtitle=result["subtitle"],
                            icon=Result.Icon(result["icon_path"])
                            if result["icon_path"]
                            else None,
                            arg=result["arg"],
                        )
                        for result in data[self.bare_query]
                    ]
                    self.log(f"found: {self.bare_query} in {self.db_results}")
                    return True
        self.log(f"not found `{self.bare_query}` in `{self.db_results}`")
        return False

    @classmethod
    def run(
        cls,
        func: Callable[[WorkflowClient], Coroutine[None, None, None]],
        cache: bool = False,
        package_dir: str = "src/libs",
    ) -> NoReturn:
        """Give async main function, no need to call `client.response` method

        Args:
            `func`: async main function that takes `client` as argument
            `cache`: cache response to workflow db_results, if cache exists, it will be loaded instead of executing `func`
            `package_dir`: directory to install `requirements.txt` packages

        - To install `from requirements.txt` do all import packages inside it
            - Use `global` keyword to access imported packages globally
        - `client.bare_query` is the bare query string
        - `client.query` is the query string without `+` (page count)
        - `client.page_count` is the page count for pagination results

        Example:
            ```
            from alfred import WorkflowClient

            async def main(client: WorkflowClient, cache=True):
                global get
                from requests import get
                pass

            if __name__ == "__main__":
                WorkflowClient.run(main)
            ```
        """
        client = cls(package_dir=package_dir)
        sys.path.insert(0, package_dir)
        if cache and client.load_cached_response():
            client.response_with_results()
        try:
            client.install_requirements()
            run(func(client))
            if cache:
                client.cache_response()
            client.response_with_results()
        except Exception as e:
            if isinstance(e, WorkflowError):
                client.error_response(
                    title=e.title,
                    subtitle=e.subtitle,
                    arg=e.arg,
                )
            else:
                client.error_response(
                    title=str(e),
                    subtitle=format_exc().strip().split("\n")[-1],
                    arg=format_exc().strip(),
                )

    def add_result(
        self,
        title: str,
        subtitle: str = "",
        icon_path: str | Path | None = None,
        arg: str = "",
        http_downloader: Callable[[str], str] | None = None,
        index: int | None = None,
    ) -> None:
        """Create and add alfred result

        - title: result title
        - subtitle: result subtitle
        - icon_path: result icon path
        - arg: argument to pass to alfred
        - http_downloader: function to download http icon
        """
        icon = None
        if icon_path:
            if http_downloader and "http" in str(icon_path):
                self.log(f"downloading icon from {icon_path}")
                icon_path = http_downloader(str(icon_path))
            icon = Result.Icon(str(icon_path))
        if index is not None:
            self.results.insert(
                index, Result(title=title, subtitle=subtitle, icon=icon, arg=arg)
            )
        else:
            self.results.append(
                Result(title=title, subtitle=subtitle, icon=icon, arg=arg)
            )

    def error_response(
        self,
        title: str,
        subtitle: str,
        icon_path: str | Path | None = None,
        arg: str = "",
    ) -> NoReturn:
        """Create and add alfred error result

        - title: error title
        - subtitle: error subtitle
        - icon_path: error icon path
        - arg: argument to pass to alfred
        - terminate: terminate workflow
        """
        self.add_result(
            title=title,
            subtitle=subtitle,
            icon_path=icon_path or self.icondir / "error.png",
            arg=arg,
        )
        self.response_with_results()

    def response_with_results(self) -> NoReturn:
        """Print saved alfred results and exit

        - terminate: terminate workflow
        """
        print(json.dumps({"items": [result.to_dict() for result in self.results]}))
        exit(0)

    def response(
        self,
        title: str,
        subtitle: str = "",
        icon_path: str | Path | None = None,
        arg: str = "",
    ) -> NoReturn:
        """Print alfred result and exit

        - title: result title
        - subtitle: result subtitle
        - icon_path: result icon path
        - arg: argument to pass to alfred
        """
        print(
            json.dumps(
                {
                    "items": [
                        Result(
                            title=title,
                            subtitle=subtitle,
                            icon=Result.Icon(str(icon_path)) if icon_path else None,
                            arg=arg,
                        ).to_dict()
                    ]
                }
            )
        )
        exit(0)
