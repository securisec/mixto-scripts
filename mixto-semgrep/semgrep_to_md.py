#!/usr/bin/env python

import sys
import json
from pathlib import Path

from typing import List, Optional
from pydantic import BaseModel


class Paths(BaseModel):
    scanned: List[str]


class End(BaseModel):
    col: int
    line: int
    offset: int


class Start(BaseModel):
    col: int
    line: int
    offset: int


class Metadata(BaseModel):
    technology: Optional[List[str]] = None


class Extra(BaseModel):
    engine_kind: str
    fingerprint: str
    is_ignored: bool
    lines: str
    message: str
    severity: str
    metadata: Metadata


class Result(BaseModel):
    check_id: str
    end: End
    extra: Extra
    path: str
    start: Start


class Semgrep(BaseModel):
    results: List[Result]


def preformatted(path: str, extra: Extra) -> str:
    line = extra.lines
    if len(line) > 150:
        line = line[:150] + "..."
    return f"""```{Path(path).suffix[1:]}
{line}
```"""


def code(s: str) -> str:
    return f"`{s}`"


def h3(s: str) -> str:
    return f"### {s}"


def h4(s: str) -> str:
    return f"#### {s}"


def italics(s: str) -> str:
    return f"*{s}*"


def bold(s: str) -> str:
    return f"**{s}**"


def seperator() -> str:
    return "---"


def blank_line() -> str:
    return ""


def get_markdown(semgrep: Semgrep) -> str:
    hold = []
    hold.append("### Semgrep")
    for d in semgrep.results:
        hold.append(h4(d.path))
        hold.append(
            f"Lines: {(d.check_id)} {code(str(d.start.line) + ' - ' + str(d.end.line))}"
        )
        hold.append(d.extra.message)
        hold.append(preformatted(d.path, d.extra))
        # hold.append(blank_line())
        hold.append(seperator())
        hold.append('')

    return "\n\n".join(hold)


if __name__ == "__main__":
    if not sys.stdin.isatty():
        data = sys.stdin.read()
        try:
            sg = Semgrep(**json.loads(data))
            print(get_markdown(sg))
        except json.decoder.JSONDecodeError:
            print("🔴 invalid json")
    else:
        # TODO 🔥
        pass

# with open('/tmp/sg.json', 'r') as f:
#     data = json.loads(f.read())
#     data = Semgrep(**data)
