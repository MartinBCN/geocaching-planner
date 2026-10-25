import argparse
from collections.abc import Sequence

import uvicorn

from geocaching_planner.config import AppConfig


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="python -m geocaching_planner")
    parser.add_argument("--reload", action="store_true", help="restart on source changes")
    args = parser.parse_args(argv)

    settings = AppConfig()
    uvicorn.run(
        "geocaching_planner.main:create_app",
        factory=True,
        host=settings.host,
        port=settings.port,
        reload=args.reload,
        # Keep Uvicorn's own handlers off so logs flow through logging_config.
        log_config=None,
    )


if __name__ == "__main__":
    main()
