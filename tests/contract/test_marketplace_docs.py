import re
from pathlib import Path


ROOT = Path(__file__).parents[2]


def test_readme_has_native_marketplace_quickstart():
    body = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "codex plugin marketplace add EstoesMoises/stack-mcp-skills" in body
    assert "codex plugin add efficient-search@stack-internal" in body
    assert "claude plugin marketplace add EstoesMoises/stack-mcp-skills --scope project" in body
    assert "claude plugin install efficient-search@stack-internal --scope project" in body
    assert "/plugin install " not in body


def test_claude_install_guides_never_publish_an_unscoped_install_command():
    """Catch a project-scope claim paired with a user-scope Claude install command."""
    for path in (ROOT / "README.md", ROOT / "adapters/claude-code/README.md"):
        body = path.read_text(encoding="utf-8")
        commands = re.findall(r"^claude plugin install .+$", body, flags=re.MULTILINE)

        assert commands
        assert all(command.endswith(" --scope project") for command in commands)
        assert "/plugin install " not in body


def test_claude_install_guides_keep_slash_commands_out_of_shell_blocks():
    """Catch a copyable shell block that includes a Claude Code slash command."""
    offenders = {}
    for path in (ROOT / "README.md", ROOT / "adapters/claude-code/README.md"):
        body = path.read_text(encoding="utf-8")
        bash_blocks = re.findall(r"```bash\n(.*?)```", body, flags=re.DOTALL)
        slash_commands = [
            line
            for block in bash_blocks
            for line in block.splitlines()
            if line.startswith("/")
        ]
        if slash_commands:
            offenders[path.relative_to(ROOT).as_posix()] = slash_commands

    assert offenders == {}


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
