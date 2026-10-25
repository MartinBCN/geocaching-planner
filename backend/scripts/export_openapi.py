"""Export the backend OpenAPI document as JSON.

Run through `mise run api:gen`, which feeds the output to openapi-typescript. The app is built
without its lifespan, so no database or network connection is opened.
"""

import json
import sys
from pathlib import Path
from typing import Any

from geocaching_planner.main import create_app


def render_openapi() -> str:
    """Return the OpenAPI document as stable, pretty-printed JSON with a trailing newline."""
    document: dict[str, Any] = create_app().openapi()
    return json.dumps(document, indent=2, sort_keys=True) + "\n"


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: export_openapi.py OUTPUT_PATH", file=sys.stderr)
        return 2
    Path(argv[1]).write_text(render_openapi(), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
