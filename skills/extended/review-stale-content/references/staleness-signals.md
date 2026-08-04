# Staleness signals

Load this reference only when classifying a fully retrieved target against current evidence. Signals establish what to investigate; a classification still requires the comparison procedure in `SKILL.md`.

## Strong signals

Strong signals can support `confirmed-divergence` when the fully retrieved content makes a directly conflicting material claim and the current source is independently verified:

- A removed configuration, endpoint, feature flag, workflow, or service named by the target is absent from current code or a verified deployment configuration.
- A verified migration replaced the service, CI system, deployment flow, storage system, or authentication mechanism described by the target.
- An authoritative current policy or service-owner record provides an explicit deprecation, retirement, or supersession of the practice in the target.
- A versioned interface, command, or operational procedure is no longer present in the verified current implementation and an authoritative migration record identifies its replacement.

State the old claim, the current fact, the source for each, and why they conflict. A strong signal without a full target retrieval, complete relevant comments, or an independently verified current source is insufficient for an update.

## Weak signals

Weak signals justify review but never prove stale content on their own:

- An old publication or edit date.
- A low score, low vote count, or no recent activity.
- Different terminology, formatting, style, or writing quality.
- A search snippet, title, tag, or comment that has not been retrieved in full.
- A user report, recollection, or model inference without an independently verified source.

Do not turn a weak signal into `confirmed-divergence`. Obtain current verified evidence, then classify `still-current` if it agrees, `confirmed-divergence` if it directly conflicts, or `possible-divergence` if it remains uncertain.

## Conflicts and boundaries

When authoritative current sources conflict with one another, show both with their IDs or source locations and request human resolution. Classify `possible-divergence`; do not silently select a winner and do not update content. The same rule applies when current code and a claimed policy disagree without a verified explanation.

An update changes only the retrieved statement that the evidence directly contradicts. Preserve unrelated fields and existing tags exactly; do not invent a tag or repair grammar merely because a stale-content review was requested.
