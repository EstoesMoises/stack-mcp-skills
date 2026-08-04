from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_readme_has_native_marketplace_quickstart():
    body = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "codex plugin marketplace add EstoesMoises/stack-mcp-skills" in body
    assert "codex plugin add efficient-search@stack-internal" in body
    assert "claude plugin marketplace add EstoesMoises/stack-mcp-skills --scope project" in body
    assert "/plugin install efficient-search@stack-internal" in body


def test_codex_docs_do_not_claim_a_project_scope_flag():
    body = (ROOT / "adapters/codex/README.md").read_text(encoding="utf-8").lower()
    assert "client-managed" in body
    assert "codex plugin marketplace add" in body
    assert "codex plugin marketplace add" not in "\n".join(
        line for line in body.splitlines() if "--scope project" in line
    )


def test_contributing_marks_generated_surfaces():
    body = (ROOT / "CONTRIBUTING.md").read_text(encoding="utf-8")
    assert "Do not edit `plugins/`" in body
    assert "packages --mode write" in body
    assert "packages --mode check" in body
