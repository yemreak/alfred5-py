from __future__ import annotations

import json
import sys
from asyncio import run
from collections.abc import Callable, Coroutine
from os import environ
from pathlib import Path
from shutil import copy2, move
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile


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
    query: str
    page_count: int

    datadir: Path

    results: list[Result]

    def __init__(self) -> None:
        self.page_count = sys.argv[1].count("+") + 1
        self.query = sys.argv[1].replace("+", "")

        self.datadir = Path("~/Library/Application Support/Alfred/Workflow Data")

        self.results = []

    @classmethod
    def run(cls, func: Callable[[WorkflowClient], Coroutine[None, None, None]]) -> None:
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
        run(func(client))
        client.response()

    def get_env(self, name: str) -> str | None:
        return environ.get(name)

    def add_result(
        self,
        title: str,
        subtitle: str = "",
        icon_path: str | Path | None = None,
        arg: str = "",
        http_downloader: Callable[[str], str] | None = None,
    ):
        """Create and add alfred result."""
        icon = None
        if icon_path:
            if http_downloader and "http" in str(icon_path):
                icon_path = http_downloader(str(icon_path))
            icon = Result.Icon(str(icon_path))
        self.results.append(Result(title=title, subtitle=subtitle, icon=icon, arg=arg))

    def error_response(self, title: str, subtitle: str, icon_path: str | Path = ""):
        self.add_result(title=title, subtitle=subtitle, icon_path=icon_path)
        self.response()

    def response(self):
        """Print alfred results and exit."""
        print(json.dumps({"items": [result.to_dict() for result in self.results]}))
        exit(0)
