from __future__ import annotations
from logging import Logger, StreamHandler
import json
import sys
from asyncio import run
from collections.abc import Callable, Coroutine
from pathlib import Path
from shutil import copy2, move
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile
from ruamel.yaml import load as yaml_load, dump as yaml_dump
from plistlib import load as plist_load
from .models import SNIPPET_INFO_TEMPLATE, Result, Snippet, yaml
from typing import NoReturn


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
    query: str
    page_count: int
    bundleid: str

    datadir: Path
    db_results: Path

    results: list[Result]

    logger: Logger

    def __init__(self) -> None:
        self.logger = Logger("alfred5")
        self.logger.addHandler(StreamHandler(sys.stderr))
        self.log(f"logger initted")

        self.page_count = sys.argv[1].count("+") + 1
        self.query = sys.argv[1].replace("+", "")

        self.log(
            f"sys.argv: {sys.argv} page_count: {self.page_count} query: {self.query}"
        )

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

    def cache_response(self) -> None:
        """Cache response to workflow db_results"""
        if not self.db_results.exists():
            self.db_results.parent.mkdir(parents=True, exist_ok=True)
            self.db_results.touch()
        with self.db_results.open("r") as f:
            data = yaml_load(f) or {}
        data[self.query] = self.results
        with self.db_results.open("w") as f:
            yaml_dump(data, f)
            self.log(f"cached response to {self.db_results}")

    def load_cached_response(self) -> bool:
        """Load cached result from alfred"""
        self.log(f"checking if `{self.query}` exists in `{self.db_results}`")
        if self.db_results.exists():
            with self.db_results.open("r") as f:
                data: dict[str, list[Result]] = yaml.load(f)
                self.log(f"loaded data from {self.db_results} {len(data.keys())}")
                if self.query in data:
                    self.results = data[self.query]
                    self.log(f"found: {self.query} in {self.db_results}")
                    return True
        self.log(f"not found `{self.query}` in `{self.db_results}`")
        return False

    @classmethod
    def run(
        cls, func: Callable[[WorkflowClient], Coroutine[None, None, None]]
    ) -> NoReturn:
        """Give async main function, no need to call `client.response` method

        ```
        from alfred import AlfredWorkflowClient

        async def main(alfred_client: AlfredWorkflowClient):
            pass

        if __name__ == "__main__":
            AlfredWorkflowClient.run(main)
        ```
        """
        client = cls()
        try:
            run(func(client))
            client.response()
        except Exception as e:
            client.error_response(title="Error", subtitle=str(e))

    def add_result(
        self,
        title: str,
        subtitle: str = "",
        icon_path: str | Path | None = None,
        arg: str = "",
        http_downloader: Callable[[str], str] | None = None,
    ) -> None:
        """Create and add alfred result."""
        icon = None
        if icon_path:
            if http_downloader and "http" in str(icon_path):
                self.log(f"downloading icon from {icon_path}")
                icon_path = http_downloader(str(icon_path))
            icon = Result.Icon(str(icon_path))
        self.results.append(Result(title=title, subtitle=subtitle, icon=icon, arg=arg))

    def error_response(
        self, title: str, subtitle: str, icon_path: str | Path | None = None
    ) -> NoReturn:
        self.add_result(
            title=title,
            subtitle=subtitle,
            icon_path=icon_path or Path(__file__).parent / "icons" / "error.png",
        )
        self.response()

    def response(self) -> NoReturn:
        """Print alfred results and exit."""
        print(json.dumps({"items": [result.to_dict() for result in self.results]}))
        exit(0)
