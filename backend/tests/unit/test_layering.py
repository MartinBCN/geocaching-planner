import ast
from collections.abc import Callable, Iterable
from pathlib import Path

SRC = Path(__file__).resolve().parents[2] / "src"
FORBIDDEN_DOMAIN_ROOTS = (
    "fastapi",
    "starlette",
    "sqlalchemy",
    "geoalchemy2",
    "httpx",
    "pydantic_settings",
)
FORBIDDEN_FROM_SERVICES = ("geocaching_planner.api", "geocaching_planner.adapters")

SourceFile = tuple[str, bool, str]


def _module_name(path: Path) -> tuple[str, bool]:
    parts = path.relative_to(SRC).with_suffix("").parts
    if parts[-1] == "__init__":
        return ".".join(parts[:-1]), True
    return ".".join(parts), False


def _imported_modules(source: str, module_name: str, is_package: bool) -> list[str]:
    package = module_name if is_package else module_name.rpartition(".")[0]
    package_parts = package.split(".")
    found: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            found.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                if node.module:
                    found.append(node.module)
                continue
            base = package_parts[: len(package_parts) - (node.level - 1)]
            if node.module:
                found.append(".".join([*base, node.module]))
            else:
                found.extend(".".join([*base, alias.name]) for alias in node.names)
    return found


def _violations(files: Iterable[SourceFile], forbidden: Callable[[str], bool]) -> list[str]:
    bad: list[str] = []
    for name, is_package, source in files:
        for target in _imported_modules(source, name, is_package):
            if forbidden(target):
                bad.append(f"{name} imports {target}")
    return bad


def _package_files(package: str) -> list[SourceFile]:
    files: list[SourceFile] = []
    for path in sorted((SRC / "geocaching_planner" / package).rglob("*.py")):
        name, is_package = _module_name(path)
        files.append((name, is_package, path.read_text(encoding="utf-8")))
    return files


def _is_forbidden_domain(target: str) -> bool:
    return target.split(".")[0] in FORBIDDEN_DOMAIN_ROOTS


def _is_forbidden_service(target: str) -> bool:
    return any(target == root or target.startswith(root + ".") for root in FORBIDDEN_FROM_SERVICES)


def test_domain_and_services_import_boundaries() -> None:
    domain_files = _package_files("domain")
    service_files = _package_files("services")
    assert domain_files
    assert service_files
    assert _violations(domain_files, _is_forbidden_domain) == []
    assert _violations(service_files, _is_forbidden_service) == []


def test_layering_detects_illegal_imports() -> None:
    bad_domain: list[SourceFile] = [
        ("geocaching_planner.domain.cache", False, "import fastapi\n"),
    ]
    bad_service: list[SourceFile] = [
        ("geocaching_planner.services.plan", False, "from ..api import deps\n"),
    ]
    assert _violations(bad_domain, _is_forbidden_domain) == [
        "geocaching_planner.domain.cache imports fastapi"
    ]
    assert _violations(bad_service, _is_forbidden_service) == [
        "geocaching_planner.services.plan imports geocaching_planner.api"
    ]


def test_layering_allows_valid_dependencies() -> None:
    valid: list[SourceFile] = [
        (
            "geocaching_planner.services.plan",
            False,
            "from geocaching_planner.domain.errors import NotFoundError\nimport structlog\n",
        ),
    ]
    assert _violations(valid, _is_forbidden_domain) == []
    assert _violations(valid, _is_forbidden_service) == []
