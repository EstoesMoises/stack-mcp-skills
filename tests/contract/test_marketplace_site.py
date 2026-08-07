import json
import re
import shutil
from pathlib import Path

import pytest

from stack_skill_catalog.site import build_site_model, write_site


ROOT = Path(__file__).parents[2]
SHA = "a" * 40
SECTION_HEADINGS = (
    "Purpose",
    "Requirements",
    "Safety",
    "Install in Codex",
    "Install in Claude Code",
    "Install in GitHub Copilot",
    "Connect Stack Internal MCP",
    "Try it",
    "Troubleshooting",
    "Compatibility",
    "Source",
)
DIRECTION_SEED = "6d37fffd"


def _files(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _catalog_entries() -> list[dict[str, object]]:
    return json.loads((ROOT / "catalog/skills.json").read_text(encoding="utf-8"))["skills"]


def _css_at_rule(css: str, header: str) -> str:
    start = css.index(header)
    opening = css.index("{", start)
    depth = 0
    for index in range(opening, len(css)):
        if css[index] == "{":
            depth += 1
        elif css[index] == "}":
            depth -= 1
            if depth == 0:
                return css[opening + 1:index]
    raise AssertionError(f"unclosed CSS at-rule: {header}")


def test_site_model_has_nine_skills_and_exact_core_selection():
    model = build_site_model(ROOT, SHA)

    assert model["source_commit"] == SHA
    assert len(model["skills"]) == 9
    assert model["core_skill_ids"] == [
        "efficient-search",
        "company-debugging",
        "capture-quality-qa",
    ]


@pytest.mark.parametrize("sha", ["", "A" * 40, "a" * 39, "a" * 41, "g" * 40])
def test_site_model_rejects_noncanonical_source_commit(sha):
    with pytest.raises(ValueError, match="lowercase 40-character Git SHA"):
        build_site_model(ROOT, sha)


def test_site_build_is_byte_deterministic(tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "second"
    write_site(ROOT, first, SHA)
    write_site(ROOT, second, SHA)

    assert _files(first) == _files(second)


def test_reused_site_output_is_replaced_with_the_exact_owned_tree(tmp_path):
    output = tmp_path / "dist"
    (output / "skills" / "removed-skill").mkdir(parents=True)
    (output / "skills" / "removed-skill" / "index.html").write_text("obsolete", encoding="utf-8")
    (output / "arbitrary-stale.txt").write_text("obsolete", encoding="utf-8")

    write_site(ROOT, output, SHA)

    assert set(_files(output)) == {
        "assets/app.js",
        "assets/styles.css",
        "catalog.json",
        "index.html",
        *(f"skills/{entry['id']}/index.html" for entry in _catalog_entries()),
    }


def test_site_output_refuses_symlink_redirects_without_touching_target(tmp_path):
    redirected = tmp_path / "redirected"
    redirected.mkdir()
    marker = redirected / "marker.txt"
    marker.write_text("preserve", encoding="utf-8")
    output = tmp_path / "dist"
    output.symlink_to(redirected, target_is_directory=True)

    with pytest.raises(ValueError, match="symlink"):
        write_site(ROOT, output, SHA)

    assert _files(redirected) == {"marker.txt": b"preserve"}


def test_site_output_refuses_a_non_directory_target(tmp_path):
    output = tmp_path / "dist"
    output.write_text("preserve", encoding="utf-8")

    with pytest.raises(ValueError, match="directory"):
        write_site(ROOT, output, SHA)

    assert output.read_text(encoding="utf-8") == "preserve"


def test_replacing_stale_tree_does_not_follow_an_internal_symlink(tmp_path):
    output = tmp_path / "dist"
    output.mkdir()
    redirected = tmp_path / "outside"
    redirected.mkdir()
    marker = redirected / "marker.txt"
    marker.write_text("preserve", encoding="utf-8")
    (output / "stale-link").symlink_to(redirected, target_is_directory=True)

    write_site(ROOT, output, SHA)

    assert marker.read_text(encoding="utf-8") == "preserve"
    assert not (output / "stale-link").exists()


def test_site_build_has_complete_normalized_catalog(tmp_path):
    output = tmp_path / "dist"
    model = build_site_model(ROOT, SHA)
    write_site(ROOT, output, SHA)

    assert json.loads((output / "catalog.json").read_text(encoding="utf-8")) == model
    assert set(_files(output)) == {
        "assets/app.js",
        "assets/styles.css",
        "catalog.json",
        "index.html",
        *(f"skills/{entry['id']}/index.html" for entry in _catalog_entries()),
    }
    serialized = (output / "catalog.json").read_text(encoding="utf-8").lower()
    assert SHA in serialized
    assert all(key not in serialized for key in ("generated_at", "generatedat", "timestamp", "built_at"))


def test_index_has_field_manual_controls_core_ledger_and_accessibility(tmp_path):
    output = tmp_path / "dist"
    write_site(ROOT, output, SHA)
    body = (output / "index.html").read_text(encoding="utf-8")

    assert body.count("<h1") == 1
    assert '<a class="skip-link" href="#main-content">' in body
    assert '<label for="skill-search">' in body
    assert '<input id="skill-search"' in body
    assert all(f'<fieldset data-filter-group="{name}">' in body for name in ("tier", "client", "write"))
    assert body.count("data-skill-card") == 9
    assert all(attribute in body for attribute in ("data-tier=", "data-tags=", "data-clients=", "data-write-capable="))
    assert body.count("codex plugin add ") == 3
    assert body.count("claude plugin install ") == 3
    assert body.count("copilot plugin install ") == 3
    assert "/plugin install " not in body
    assert all(
        command.endswith(" --scope project")
        for command in re.findall(r"claude plugin install [^<\n]+", body)
    )
    assert "aria-selected" in body
    assert "aria-controls" in body
    assert 'aria-live="polite"' in body
    assert DIRECTION_SEED in body
    assert re.search(r"<body[^>]*>\s*<!--\s*THESIS:", body)
    assert "unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, and DESIGN.md" in body


def test_core_ledger_is_operational_without_unapproved_theme_control(tmp_path):
    output = tmp_path / "dist"
    write_site(ROOT, output, SHA)
    body = (output / "index.html").read_text(encoding="utf-8")
    script = (output / "assets/app.js").read_text(encoding="utf-8")

    assert "codex plugin marketplace add EstoesMoises/stack-mcp-skills" in body
    assert "claude plugin marketplace add EstoesMoises/stack-mcp-skills --scope project" in body
    assert "copilot plugin marketplace add EstoesMoises/stack-mcp-skills" in body
    assert "data-theme-toggle" not in body
    assert "toggleTheme" not in script


def test_every_skill_page_has_native_commands_smokes_and_required_sections(tmp_path):
    output = tmp_path / "dist"
    write_site(ROOT, output, SHA)

    for entry in _catalog_entries():
        body = (output / "skills" / entry["id"] / "index.html").read_text(encoding="utf-8")
        assert body.count("<h1") == 1
        assert f"codex plugin add {entry['id']}@stack-internal" in body
        assert f"claude plugin install {entry['id']}@stack-internal --scope project" in body
        assert f"copilot plugin install {entry['id']}@stack-internal" in body
        assert "/plugin install " not in body
        assert all(
            command.endswith(" --scope project")
            for command in re.findall(r"claude plugin install [^<\n]+", body)
        )
        assert "How should I structure logging in this service?" in body
        assert "Write a Python function that reverses a string." in body
        assert all(f">{heading}</h2>" in body for heading in SECTION_HEADINGS)
        assert DIRECTION_SEED in body
        assert re.search(r"<body[^>]*>\s*<!--\s*THESIS:", body)


def test_skill_pages_expose_permissions_and_one_scoped_codex_manifest(tmp_path):
    output = tmp_path / "dist"
    write_site(ROOT, output, SHA)

    for entry in _catalog_entries():
        body = (output / "skills" / entry["id"] / "index.html").read_text(encoding="utf-8")
        if entry["write_actions"]:
            assert all(action in body for action in entry["write_actions"])
        else:
            assert "Read-only" in body
        match = re.search(
            r'<script type="application/json" data-codex-project-manifest>(.*?)</script>',
            body,
            re.DOTALL,
        )
        assert match
        manifest = json.loads(match.group(1))
        assert [plugin["name"] for plugin in manifest["plugins"]] == [entry["id"]]
        source = manifest["plugins"][0]["source"]
        assert source["source"] == "git-subdir"
        assert source["path"] == f"./plugins/{entry['id']}"
        assert "codex plugin add" in body and "--scope project" not in body.split("Install in Codex", 1)[1].split("Install in Claude Code", 1)[0]


def test_generated_site_has_no_network_or_tenant_data_surfaces(tmp_path):
    output = tmp_path / "dist"
    write_site(ROOT, output, SHA)

    all_text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted(output.rglob("*"))
        if path.is_file()
    )
    assert "http://" not in all_text
    assert "<form" not in all_text
    assert "fetch(" not in all_text
    assert "XMLHttpRequest" not in all_text
    assert "analytics" not in all_text.lower()
    assert str(ROOT) not in all_text
    assert all_text.count("[tenant-slug]") == 27
    for line in all_text.splitlines():
        if "[tenant-slug]" in line:
            assert "mcp add" in line


def test_html_security_and_troubleshooting_contract(tmp_path):
    output = tmp_path / "dist"
    write_site(ROOT, output, SHA)
    expected_csp = (
        "default-src &#x27;self&#x27;; script-src &#x27;self&#x27;; style-src &#x27;self&#x27;; "
        "img-src &#x27;self&#x27; data:; object-src &#x27;none&#x27;; base-uri &#x27;self&#x27;; form-action &#x27;none&#x27;"
    )
    troubleshooting_states = (
        "Plugin commands are missing",
        "Marketplace Git or policy failure",
        "Plugin not found",
        "Installed but undiscovered",
        "MCP or OAuth failure",
    )

    for path in sorted(output.rglob("*.html")):
        body = path.read_text(encoding="utf-8")
        assert expected_csp in body
        assert '<a class="skip-link" href="#main-content">' in body
        assert "<button" in body or "<input" in body
    for entry in _catalog_entries():
        body = (output / "skills" / entry["id"] / "index.html").read_text(encoding="utf-8")
        assert all(state in body for state in troubleshooting_states)
        assert "bypass managed marketplace policy" not in body.lower()


def test_local_assets_have_accessible_responsive_behavior(tmp_path):
    output = tmp_path / "dist"
    write_site(ROOT, output, SHA)
    css = (output / "assets/styles.css").read_text(encoding="utf-8")
    js = (output / "assets/app.js").read_text(encoding="utf-8")

    assert ":focus-visible" in css
    assert "prefers-reduced-motion: reduce" in css
    assert "@media (max-width: 720px)" in css
    assert "min-height: 44px" in css
    assert "@import" not in css
    assert "url(" not in css
    assert "toLocaleLowerCase().trim()" in js
    assert "function applyFilters()" in js
    assert "function selected(" in js
    assert "ArrowLeft" in js and "ArrowRight" in js
    assert "navigator.clipboard.writeText" in js
    assert "fetch(" not in js and "XMLHttpRequest" not in js


def test_assets_define_automatic_dark_mode_and_true_narrow_single_column_layout(tmp_path):
    output = tmp_path / "dist"
    write_site(ROOT, output, SHA)
    css = (output / "assets/styles.css").read_text(encoding="utf-8")
    html = (output / "index.html").read_text(encoding="utf-8")
    dark = _css_at_rule(css, "@media (prefers-color-scheme: dark)")
    narrow = _css_at_rule(css, "@media (max-width: 720px)")

    assert '<meta name="color-scheme" content="light dark">' in html
    for token in ("--paper", "--paper-raised", "--ink", "--ink-muted", "--rule", "--blue", "--amber"):
        assert token in dark
    for selector in (r"\.site-header nav", r"\.truth-ledger", r"\.record-index"):
        assert re.search(rf"{selector}\s*\{{[^}}]*grid-template-columns:\s*1fr\s*;", narrow, re.DOTALL)
    assert re.search(r"\.record-index a:nth-of-type\(odd\)\s*\{[^}]*border-right:\s*0\s*;", narrow, re.DOTALL)


def test_catalog_and_frontmatter_values_are_html_escaped(repo_fixture, tmp_path):
    hostile_path = "skills/core/hostile-skill"
    repo_fixture.add_skill(path=hostile_path, name="hostile-skill")
    catalog_path = repo_fixture.root / "catalog" / "skills.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    catalog["skills"][0].update(
        {
            "name": '<img src=x onerror="alert(1)">',
            "summary": "<script>alert('summary')</script> & evidence",
            "tags": ["<unsafe&tag>"],
        }
    )
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")
    skill_path = repo_fixture.root / hostile_path / "SKILL.md"
    skill_path.write_text(
        skill_path.read_text(encoding="utf-8").replace(
            "description: Find company-specific guidance when an internal answer may help.",
            "description: '<b>unsafe & \"quoted\" description</b>'",
        ),
        encoding="utf-8",
    )
    marketplace_path = repo_fixture.root / "catalog" / "marketplace.json"
    marketplace = json.loads(marketplace_path.read_text(encoding="utf-8"))
    marketplace["category"] = "</script><script>alert('category')</script>"
    marketplace_path.write_text(json.dumps(marketplace), encoding="utf-8")
    shutil.copytree(ROOT / "marketplace_web", repo_fixture.root / "marketplace_web")

    output = tmp_path / "dist"
    write_site(repo_fixture.root, output, SHA)
    index = (output / "index.html").read_text(encoding="utf-8")
    detail = (output / "skills" / "hostile-skill" / "index.html").read_text(encoding="utf-8")

    assert '<img src=x onerror="alert(1)">' not in index
    assert "<script>alert('summary')</script>" not in index
    assert "<b>unsafe" not in detail
    assert "</script><script>alert('category')</script>" not in detail
    assert "&lt;img src=x onerror=&quot;alert(1)&quot;&gt;" in index
    assert "&lt;script&gt;alert(&#x27;summary&#x27;)&lt;/script&gt; &amp; evidence" in index
    assert 'data-tags="&lt;unsafe&amp;tag&gt;"' in index
    assert "&lt;b&gt;unsafe &amp; &quot;quoted&quot; description&lt;/b&gt;" in detail
    assert (
        'href="https://github.com/EstoesMoises/stack-mcp-skills/tree/'
        f'{SHA}/skills/core/hostile-skill"'
    ) in detail
    manifest_match = re.search(
        r'<script type="application/json" data-codex-project-manifest>(.*?)</script>', detail, re.DOTALL
    )
    assert manifest_match
    assert json.loads(manifest_match.group(1))["plugins"][0]["category"] == marketplace["category"]
