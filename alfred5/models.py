from __future__ import annotations

from dataclasses import asdict, dataclass, field
from json import dump
from pathlib import Path
from uuid import uuid4

SNIPPET_INFO_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
	<key>snippetkeywordprefix</key>
	<string>{}</string>
	<key>snippetkeywordsuffix</key>
	<string>{}</string>
</dict>
</plist>"""


@dataclass
class Snippet:
    """Alfred snippet

    ```json
    // name [uid].json
    // Example Markdown [543B95E5-469E-4D8D-B4B7-D16336E08A28].json
    {
        "alfredsnippet": {
            "snippet": "## ⭐️ Example",
            "dontautoexpand": false,
            "uid": "543B95E5-469E-4D8D-B4B7-D16336E08A28",
            "name": "Example ~ Markdown",
            "keyword": ":example:"
        }
    }
    ```
    """

    snippet: str
    name: str
    keyword: str

    uid: str = field(default_factory=lambda: str(uuid4()))
    dontautoexpand: bool = True

    def save(self, snippets_dir: Path) -> Path:
        """Save snippet to file"""
        snippet_path = snippets_dir / f"{self.name} [{self.uid}].json"
        with snippet_path.open("w") as f:
            dump({"alfredsnippet": asdict(self)}, f, indent=4)
        return snippet_path


@dataclass
class Result:
    """Alfred result

    https://www.alfredapp.com/help/workflows/inputs/script-filter/json/

    ```json
    {
        "uid": "desktop",
        "type": "file",
        "title": "Desktop",
        "subtitle": "~/Desktop",
        "arg": "~/Desktop",
        "autocomplete": "Desktop",
        "icon": {
            "type": "fileicon",
            "path": "~/Desktop"
        }
    }
    ```
    """

    @dataclass
    class Icon:
        path: str
        type: str | None = None

    title: str

    subtitle: str = ""
    uid: str = field(default_factory=lambda: str(uuid4()))
    arg: str = ""
    autocomplete: str | None = None
    icon: Icon | None = None

    def to_dict(self) -> dict[str, str | dict[str, str]]:
        return asdict(self)
