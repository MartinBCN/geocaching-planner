import re
import tomllib
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "ci.yml"


def test_ci_uses_mise_tasks_and_declared_jobs() -> None:
    """AC4, AC7, AC8: workflow triggers, privileges, concurrency, and task-only gates."""
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))
    triggers = workflow.get("on", workflow.get(True, {}))
    expected_jobs = {
        "backend": "mise run check:backend",
        "frontend": "mise run check:frontend",
        "e2e": "mise run test:e2e:ci",
        "pre-commit": "mise run check:pre-commit",
    }

    assert set(triggers) == {"pull_request", "push", "workflow_dispatch"}
    assert triggers["push"]["branches"] == ["main"]
    assert workflow["permissions"] == {"contents": "read"}
    assert workflow["concurrency"]["cancel-in-progress"] == (
        "${{ github.event_name == 'pull_request' }}"
    )
    assert "github.event.pull_request.number || github.ref" in workflow["concurrency"]["group"]
    assert set(workflow["jobs"]) == set(expected_jobs)

    for job_id, gate in expected_jobs.items():
        job = workflow["jobs"][job_id]
        assert job["runs-on"] == "ubuntu-latest"
        assert int(job["timeout-minutes"]) <= 20
        run_steps = [step["run"] for step in job["steps"] if "run" in step]
        assert gate in run_steps
        assert all(command.startswith("mise run ") for command in run_steps)
        for step in job["steps"]:
            if "uses" in step:
                assert re.search(r"@[0-9a-f]{40}$", step["uses"])

    pre_commit_steps = workflow["jobs"]["pre-commit"]["steps"]
    assert any(step.get("run") == "mise run test:bootstrap" for step in pre_commit_steps)
    pre_commit_gate = next(
        step for step in pre_commit_steps if step.get("run") == expected_jobs["pre-commit"]
    )
    assert pre_commit_gate["env"] == {"SKIP": "mypy"}
    artifact_names = {
        step["with"]["name"]
        for job in workflow["jobs"].values()
        for step in job["steps"]
        if "actions/upload-artifact@" in step.get("uses", "")
    }
    assert artifact_names == {"backend-coverage", "frontend-coverage", "e2e-report"}

    workflow_text = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert not re.search(
        r"setup-python|setup-node|astral-uv|pnpm/action-setup|"
        r"(?:python|node|uv|pnpm)-version|tool_versions|mise_toml",
        workflow_text,
    )


def test_check_frontend_fails_on_generated_schema_drift() -> None:
    """AC5: frontend's gate compares generated schema in a temporary file."""
    mise = tomllib.loads((REPO_ROOT / "mise.toml").read_text(encoding="utf-8"))
    tasks = mise["tasks"]

    assert "api:check" in tasks["check:frontend"]["depends"]
    assert tasks["api:check"]["run"] == "scripts/api-schema.sh check"
    schema_script = (REPO_ROOT / "scripts" / "api-schema.sh").read_text(encoding="utf-8")
    assert 'SCHEMA="$ROOT/frontend/src/api/schema.d.ts"' in schema_script
    assert 'openapi-typescript "$tmp/openapi.json" -o "$tmp/schema.d.ts"' in schema_script
    assert 'cmp -s "$tmp/schema.d.ts" "$SCHEMA"' in schema_script
    assert "API schema out of date: run mise run api:gen" in schema_script


def test_quality_gate_tasks_enforce_lint_and_coverage_thresholds() -> None:
    """AC1-AC3: CI invokes local gates that enforce the declared lint and coverage levels."""
    backend = tomllib.loads((REPO_ROOT / "backend" / "pyproject.toml").read_text(encoding="utf-8"))
    frontend = (REPO_ROOT / "frontend" / "vite.config.ts").read_text(encoding="utf-8")
    mise = tomllib.loads((REPO_ROOT / "mise.toml").read_text(encoding="utf-8"))

    assert "--cov-fail-under=85" in backend["tool"]["pytest"]["ini_options"]["addopts"]
    assert "thresholds: { lines: 80 }" in frontend
    assert mise["tasks"]["lint:backend"]["run"].endswith(
        "ruff check . && uv run --locked ruff format --check ."
    )
    assert mise["tasks"]["lint:frontend"]["run"] == "pnpm lint"
    assert mise["tasks"]["test:backend"]["run"].endswith(
        "--cov-report=term-missing --cov-report=xml:coverage.xml"
    )
    assert mise["tasks"]["test:frontend"]["run"] == "pnpm test:coverage"


def test_e2e_ci_starts_db_only_and_checks_backend_health() -> None:
    """The CI smoke path must avoid BRouter and exercise the production preview build."""
    script = (REPO_ROOT / "scripts" / "test-e2e-ci.sh").read_text(encoding="utf-8")

    assert "docker compose up -d --wait db" in script
    assert "brouter" not in script.lower()
    assert "mise run db:migrate" in script
    assert "GCP_HOST=127.0.0.1" in script
    assert "GCP_PORT=8000" in script
    assert "mise run build:frontend" in script
    assert "--port 5173 --strictPort" in script
    assert "E2E_BASE_URL:-http://localhost:5173" in script
    assert "mise exec -- pnpm --dir frontend exec playwright test" in script


def test_readme_required_checks_match_workflow() -> None:
    """AC6: README lists all required status-check names in Development / CI."""
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
    section = readme.split("## Development / CI", 1)[1].split("\n## ", 1)[0]
    workflow = yaml.safe_load(WORKFLOW_PATH.read_text(encoding="utf-8"))

    for job_id in workflow["jobs"]:
        assert f"`{job_id}`" in section
    assert "actions/workflows/ci.yml/badge.svg" in readme
