# Marketplace testing record

## Task 8 isolated rehearsal — 2026-08-04

The pre-evidence rehearsal candidate was `46c91c8200b78abbbde83b39f80e42c8f91b7da0`; it is not tenant-backed evidence. The marketplace build reported version `0.1.0`. Installed clients were `codex-cli 0.142.5` and `2.1.220 (Claude Code)`.

Local structural/native validation was run with `claude plugin validate .` and `claude plugin validate` for each of the nine generated plugin directories; every command exited 0. In a fresh temporary Codex profile, the documented local marketplace flow added the repository, listed nine available plugins, installed `efficient-search@stack-internal` at `0.1.0`, removed it, and then listed no installed plugins. The temporary profile was removed after the rehearsal.

Claude Code's documented project-scoped local marketplace add was attempted from a fresh temporary project. It was blocked before project configuration with an `EPERM` opening Claude Code's personal known-marketplace cache. No permitted personal-state change was made, so no Claude lifecycle result is recorded. The public GitHub-source rehearsal was not attempted because this candidate is not on public `main`; the public Pages review was also not run. No authorized tenant or credentials were supplied, so all tenant-backed smokes, smoke artifacts, and compatibility evidence remain uncreated.

GitHub Copilot CLI support was added after this historical rehearsal. Its `.github/plugin` marketplace and package manifests, native lifecycle, explicit skill invocation, MCP OAuth flow, and all tenant-backed smokes remain pending for the next release candidate.

The fixed tenant purpose for every tenant-backed smoke is `non-production skill validation`. Raw tenant data is forbidden: do not record tenant identifiers, slugs, names, credentials, tokens, personal data, customer data, or raw retrieved content.

| Client | Exact client version | Marketplace add | Plugin list | Individual install | Core install | Explicit invocation | Update | Disable/remove | Project-scope observation | Smoke 1-4 | Result | Reviewer |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Codex | `codex-cli 0.142.5` | Local isolated-profile add succeeded; public GitHub source pending publication | Local list showed 9 available entries; after removal it showed 0 installed | Local install of `efficient-search@stack-internal` at `0.1.0` succeeded | Not run | Not run | Not run | Local removal succeeded; disablement not run | Installed help exposes no project-scope flag; command-driven registration is client-managed | Not run; no authorized tenant | Local structural/native and isolated lifecycle rehearsal only; compatibility remains `experimental` | Task 8 isolated rehearsal |
| Claude Code | `2.1.220 (Claude Code)` | Project-scoped local add blocked by `EPERM` before configuration; public GitHub source pending publication | Not run because add was blocked | Not run because add was blocked | Not run | Not run | Not run | Not run | Help supports `--scope project`, but the isolated project attempt was blocked before it could be exercised; no user/global scope was used | Not run; no authorized tenant | Local structural/native validation only; compatibility remains `experimental` | Task 8 isolated rehearsal |

For the release review, test the public GitHub marketplace add path, plugin listing, one individual install, the three-plugin core convenience flow, explicit invocation, native update, disablement and removal, and actual scope behavior in Codex, Claude Code, and GitHub Copilot CLI. Navigate the deployed GitHub Pages catalog during the same review. Run all four tenant-backed smokes only against the exact generated plugin and skill versions, preserving the existing changed-payload reapproval and byte-for-byte approval semantics. A missing, blocked, or failed observation keeps compatibility `experimental`.
