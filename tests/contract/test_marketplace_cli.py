from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil

import pytest

from stack_skill_catalog.marketplace_distribution import generate_distribution


ROOT = Path(__file__).parents[2]
SCRIPT_PATH = ROOT / "scripts/build_marketplace.py"
SPEC = importlib.util.spec_from_file_location("build_marketplace", SCRIPT_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
main = MODULE.main


def _source_root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    shutil.copytree(ROOT / "catalog", root / "catalog")
    shutil.copytree(ROOT / "marketplace_web", root / "marketplace_web")
    shutil.copytree(ROOT / "standards", root / "standards")
    shutil.copytree(ROOT / "skills", root / "skills")
    shutil.copyfile(ROOT / "LICENSE", root / "LICENSE")
    return root


def _distribution_state(root: Path) -> dict[str, tuple[str, bytes]]:
    """Capture node types and bytes for all three committed distribution surfaces."""
    state: dict[str, tuple[str, bytes]] = {}
    for relative in ("plugins", ".agents", ".claude-plugin"):
        surface = root / relative
        if not surface.exists():
            state[relative] = ("missing", b"")
            continue
        paths = [surface] if surface.is_file() else [surface, *sorted(surface.rglob("*"))]
        for path in paths:
            key = path.relative_to(root).as_posix()
            state[key] = ("file", path.read_bytes()) if path.is_file() else ("directory", b"")
    return state


def _site_files(root: Path) -> dict[str, bytes]:
    """Return the relative file tree for a generated site."""
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _catalog_entries(root: Path) -> list[dict[str, object]]:
    """Load the catalog entries used to determine expected skill pages."""
    return json.loads((root / "catalog" / "skills.json").read_text(encoding="utf-8"))["skills"]


def test_site_command_requires_explicit_commit(tmp_path, capsys):
    """Site builds must name the exact source commit they publish."""
    with pytest.raises(SystemExit) as error:
        main(["site", "--root", str(ROOT), "--output", str(tmp_path)])

    assert error.value.code == 2
    assert "--source-commit" in capsys.readouterr().err


def test_site_command_builds_dist_from_explicit_commit(tmp_path, capsys):
    """The site command writes a deterministic site and a relative result path."""
    root = _source_root(tmp_path)
    output = root / "dist"
    source_commit = "b" * 40

    assert main(
        [
            "site",
            "--root",
            str(root),
            "--output",
            str(output),
            "--source-commit",
            source_commit,
        ]
    ) == 0

    assert (output / "index.html").is_file()
    assert capsys.readouterr().out == (
        '{"output": "dist", "source_commit": "' + source_commit + '", "valid": true}\n'
    )


def test_version_command_prints_only_semver(capsys):
    """Version output stays directly usable by release workflows."""
    assert main(["version", "--root", str(ROOT)]) == 0

    assert capsys.readouterr().out == "0.1.0\n"


def test_site_command_sanitizes_a_malformed_catalog_entry(tmp_path, capsys):
    """Malformed source data must fail without leaking a traceback or repository path."""
    root = _source_root(tmp_path)
    catalog_path = root / "catalog" / "skills.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog["skills"] = [{}]
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")

    assert main(["site", "--root", str(root), "--output", str(tmp_path / "dist"), "--source-commit", "a" * 40]) == 1

    output = capsys.readouterr().out
    assert output == '{"error": "site build failed", "valid": false}\n'
    assert "Traceback" not in output
    assert str(root) not in output


@pytest.mark.parametrize(
    ("mode", "expected"),
    [
        ("check", '{"error": "package check failed", "valid": false}\n'),
        ("write", '{"error": "package write failed", "generated": false}\n'),
    ],
)
def test_packages_command_sanitizes_an_invalid_root(tmp_path, capsys, mode, expected):
    """Package operations must not disclose missing-root paths in their failure output."""
    root = tmp_path / "missing-root"

    assert main(["packages", "--mode", mode, "--root", str(root)]) == 1

    output = capsys.readouterr().out
    assert output == expected
    assert "Traceback" not in output
    assert str(root) not in output


def test_version_command_sanitizes_an_invalid_root(tmp_path, capsys):
    """Version lookup must not expose a missing configuration path."""
    root = tmp_path / "missing-root"

    assert main(["version", "--root", str(root)]) == 1

    output = capsys.readouterr().out
    assert output == "marketplace version unavailable\n"
    assert "Traceback" not in output
    assert str(root) not in output


def test_version_command_sanitizes_a_symlink_loop_root(tmp_path, capsys):
    """A self-referential root cannot leak a filesystem path through version lookup."""
    root = tmp_path / "loop"
    root.symlink_to(root.name)

    assert main(["version", "--root", str(root)]) == 1

    output = capsys.readouterr().out
    assert output == "marketplace version unavailable\n"
    assert "Traceback" not in output
    assert str(root) not in output


def test_version_command_sanitizes_a_malformed_marketplace_config(tmp_path, capsys):
    """Malformed marketplace data cannot expose parser details or a repository path."""
    root = _source_root(tmp_path)
    (root / "catalog" / "marketplace.json").write_text("{}", encoding="utf-8")

    assert main(["version", "--root", str(root)]) == 1

    output = capsys.readouterr().out
    assert output == "marketplace version unavailable\n"
    assert "Traceback" not in output
    assert str(root) not in output


@pytest.mark.parametrize("output", (".", ".."))
def test_site_command_refuses_repository_or_ancestor_outputs_without_deleting(repo_fixture, output, monkeypatch, capsys):
    """A site build must never replace its source repository or one of its parents."""
    root = repo_fixture.root
    marker = root / "preserve.txt"
    marker.write_text("keep this source tree\n", encoding="utf-8")
    monkeypatch.chdir(root)

    assert main(["site", "--root", str(root), "--output", output, "--source-commit", "c" * 40]) == 1

    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is False
    assert marker.read_text(encoding="utf-8") == "keep this source tree\n"
    assert (root / "catalog" / "marketplace.json").is_file()


def test_site_command_refuses_repository_root_without_deleting(repo_fixture, capsys):
    """An explicit repository-root output must leave every source file intact."""
    root = repo_fixture.root
    marker = root / "preserve.txt"
    marker.write_text("keep this source tree\n", encoding="utf-8")

    assert main(["site", "--root", str(root), "--output", str(root), "--source-commit", "c" * 40]) == 1

    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is False
    assert marker.read_text(encoding="utf-8") == "keep this source tree\n"
    assert (root / "catalog" / "marketplace.json").is_file()


def test_site_command_refuses_symlinked_output_without_touching_target(repo_fixture, tmp_path, capsys):
    """A symlinked output cannot redirect a build outside its validated destination."""
    root = repo_fixture.root
    outside = tmp_path / "outside"
    outside.mkdir()
    marker = outside / "preserve.txt"
    marker.write_text("keep this external tree\n", encoding="utf-8")
    output = root / "dist"
    output.symlink_to(outside, target_is_directory=True)

    assert main(["site", "--root", str(root), "--output", str(output), "--source-commit", "c" * 40]) == 1

    payload = json.loads(capsys.readouterr().out)
    assert payload["valid"] is False
    assert marker.read_text(encoding="utf-8") == "keep this external tree\n"
    assert list(outside.iterdir()) == [marker]


def test_site_command_is_byte_deterministic_for_a_source_commit(tmp_path, capsys):
    """The same source SHA must produce identical paths and bytes in separate outputs."""
    root = _source_root(tmp_path)
    first = tmp_path / "first"
    second = tmp_path / "second"
    source_commit = "a" * 40

    assert main(["site", "--root", str(root), "--output", str(first), "--source-commit", source_commit]) == 0
    capsys.readouterr()
    assert main(["site", "--root", str(root), "--output", str(second), "--source-commit", source_commit]) == 0
    capsys.readouterr()

    assert _site_files(first) == _site_files(second)


def test_site_command_changes_only_release_references_for_a_different_commit(tmp_path, capsys):
    """Changing the SHA may alter catalog data and HTML source/release references only."""
    root = _source_root(tmp_path)
    first = tmp_path / "first"
    second = tmp_path / "second"
    first_commit = "a" * 40
    second_commit = "b" * 40

    assert main(["site", "--root", str(root), "--output", str(first), "--source-commit", first_commit]) == 0
    capsys.readouterr()
    assert main(["site", "--root", str(root), "--output", str(second), "--source-commit", second_commit]) == 0
    capsys.readouterr()

    first_files = _site_files(first)
    second_files = _site_files(second)
    assert set(first_files) == set(second_files)
    changed = {path for path in first_files if first_files[path] != second_files[path]}
    assert changed == {
        "catalog.json",
        "index.html",
        *(f"skills/{entry['id']}/index.html" for entry in _catalog_entries(root)),
    }
    for path in changed:
        assert first_files[path].replace(first_commit.encode(), second_commit.encode()) == second_files[path]


def test_check_reports_relative_missing_surfaces_before_generation(tmp_path, capsys):
    """A clean source tree must report missing outputs without leaking its absolute path."""
    root = _source_root(tmp_path)

    exit_code = main(["packages", "--mode", "check", "--root", str(root)])

    output = capsys.readouterr().out
    payload = json.loads(output)
    assert exit_code == 1
    assert payload == {
        "differences": [
            "missing: .agents/plugins/marketplace.json",
            "missing: .claude-plugin/marketplace.json",
            "missing: plugins",
        ],
        "valid": False,
    }
    assert str(root) not in output


def test_write_then_check_creates_an_exact_distribution(tmp_path, capsys):
    """Write mode must create all surfaces that a following check accepts byte-for-byte."""
    root = _source_root(tmp_path)

    assert main(["packages", "--mode", "write", "--root", str(root)]) == 0
    write_payload = json.loads(capsys.readouterr().out)
    assert write_payload == {"generated": True, "root": str(root.resolve())}
    assert main(["packages", "--mode", "check", "--root", str(root)]) == 0
    assert json.loads(capsys.readouterr().out) == {"differences": [], "valid": True}


def test_check_reports_changed_generated_bytes_and_unexpected_stale_files(tmp_path, capsys):
    """Byte edits and stale packages must both appear in deterministic drift output."""
    root = _source_root(tmp_path)
    assert main(["packages", "--mode", "write", "--root", str(root)]) == 0
    capsys.readouterr()
    readme = root / "plugins/efficient-search/README.md"
    readme.write_bytes(readme.read_bytes() + b"changed\n")
    stale = root / "plugins/stale/file.txt"
    stale.parent.mkdir(parents=True)
    stale.write_text("stale\n", encoding="utf-8")

    assert main(["packages", "--mode", "check", "--root", str(root)]) == 1

    output = capsys.readouterr().out
    differences = json.loads(output)["differences"]
    assert "changed: plugins/efficient-search/README.md" in differences
    assert "unexpected: plugins/stale/file.txt" in differences
    assert str(root) not in output


def test_write_refuses_unmarked_plugins_and_preserves_existing_content(tmp_path, capsys):
    """Write mode must not replace a plugins tree it cannot prove was generated."""
    root = _source_root(tmp_path)
    keep = root / "plugins/keep-me.txt"
    keep.parent.mkdir()
    keep.write_text("keep me\n", encoding="utf-8")

    assert main(["packages", "--mode", "write", "--root", str(root)]) == 1

    payload = json.loads(capsys.readouterr().out)
    assert payload["generated"] is False
    assert keep.read_text(encoding="utf-8") == "keep me\n"
    assert not (root / ".agents/plugins/marketplace.json").exists()
    assert not (root / ".claude-plugin/marketplace.json").exists()


def test_write_refuses_a_plugins_tree_with_an_edited_marker(tmp_path, capsys):
    """Only the exact generated marker authorizes destructive replacement."""
    root = _source_root(tmp_path)
    marker = root / "plugins/.generated-marketplace"
    marker.parent.mkdir()
    marker.write_text("generated but edited\n", encoding="utf-8")

    assert main(["packages", "--mode", "write", "--root", str(root)]) == 1

    payload = json.loads(capsys.readouterr().out)
    assert payload["generated"] is False
    assert marker.read_text(encoding="utf-8") == "generated but edited\n"


@pytest.mark.parametrize("symlinked_parent", [".agents", ".agents/plugins", ".claude-plugin"])
def test_write_refuses_symlinked_manifest_parents(tmp_path, capsys, symlinked_parent):
    """Write mode must not redirect either manifest outside the requested repository root."""
    root = _source_root(tmp_path)
    generated = tmp_path / "generated"
    generate_distribution(root, generated)
    shutil.move(str(generated / "plugins"), root / "plugins")
    outside = tmp_path / "outside"
    outside.mkdir()
    symlink = root / symlinked_parent
    symlink.parent.mkdir(parents=True, exist_ok=True)
    symlink.symlink_to(outside, target_is_directory=True)

    assert main(["packages", "--mode", "write", "--root", str(root)]) == 1

    payload = json.loads(capsys.readouterr().out)
    assert payload["generated"] is False
    assert list(outside.iterdir()) == []
    assert (root / "plugins/.generated-marketplace").is_file()


@pytest.mark.parametrize(
    ("collision_type", "collision_path"),
    [
        ("parent-file", ".agents"),
        ("parent-file", ".agents/plugins"),
        ("parent-file", ".claude-plugin"),
        ("manifest-directory", ".agents/plugins/marketplace.json"),
        ("manifest-directory", ".claude-plugin/marketplace.json"),
    ],
)
def test_write_preflights_manifest_collisions_before_replacing_any_surface(
    tmp_path, capsys, collision_type, collision_path
):
    """An incompatible manifest path must leave every existing distribution byte untouched."""
    root = _source_root(tmp_path)
    assert main(["packages", "--mode", "write", "--root", str(root)]) == 0
    capsys.readouterr()
    readme = root / "plugins/efficient-search/README.md"
    readme.write_bytes(readme.read_bytes() + b"preserve this drift\n")
    collision = root / collision_path
    if collision.is_dir():
        shutil.rmtree(collision)
    else:
        collision.unlink()
    if collision_type == "parent-file":
        collision.write_text("preserve parent file\n", encoding="utf-8")
    else:
        collision.mkdir()
        (collision / "keep.txt").write_text("preserve directory\n", encoding="utf-8")
    before = _distribution_state(root)

    assert main(["packages", "--mode", "write", "--root", str(root)]) == 1

    payload = json.loads(capsys.readouterr().out)
    assert payload["generated"] is False
    assert _distribution_state(root) == before
