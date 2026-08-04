---
name: Stack Internal Skills
description: A public technical field manual for installing and verifying native developer skills.
colors:
  paper: "#f4f7fb"
  paper-raised: "#ffffff"
  paper-blue: "#e5eefb"
  ink: "#13233a"
  ink-muted: "#53647a"
  rule: "#aab8c9"
  rule-strong: "#61758e"
  blue: "#075fc9"
  blue-deep: "#004898"
  blue-text: "#f7fbff"
  amber: "#8a4d00"
  amber-paper: "#fff0d2"
  read: "#20644b"
  read-paper: "#daf1e7"
  focus: "#005bd1"
typography:
  display:
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "clamp(2.6rem, 4.6vw, 4.4rem)"
    fontWeight: 760
    lineHeight: 1.08
    letterSpacing: "-0.035em"
  headline:
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "clamp(2rem, 4vw, 3.3rem)"
    fontWeight: 700
    lineHeight: 1.08
    letterSpacing: "-0.025em"
  title:
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "clamp(1.25rem, 2.2vw, 1.75rem)"
    fontWeight: 700
    lineHeight: 1.08
  body:
    fontFamily: "ui-sans-serif, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, Liberation Mono, monospace"
    fontSize: "0.75rem"
    fontWeight: 700
    letterSpacing: "0.06em"
rounded:
  field: "0"
spacing:
  1: "0.35rem"
  2: "0.65rem"
  3: "1rem"
  4: "1.5rem"
  5: "2.25rem"
  6: "3.5rem"
components:
  button-copy:
    backgroundColor: "#16395f"
    textColor: "{colors.blue-text}"
    typography: "{typography.label}"
    rounded: "{rounded.field}"
    padding: "0.65rem 0.9rem"
    height: "44px"
  tab-selected:
    backgroundColor: "{colors.blue}"
    textColor: "{colors.blue-text}"
    typography: "{typography.body}"
    rounded: "{rounded.field}"
    padding: "0.65rem 1rem"
    height: "44px"
  input-search:
    backgroundColor: "{colors.paper-raised}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.field}"
    padding: "0.7rem 0.85rem"
    height: "44px"
  permission-read:
    backgroundColor: "{colors.read-paper}"
    textColor: "{colors.read}"
    typography: "{typography.label}"
    rounded: "{rounded.field}"
    padding: "0.3rem 0.5rem"
  permission-write:
    backgroundColor: "{colors.amber-paper}"
    textColor: "{colors.amber}"
    typography: "{typography.label}"
    rounded: "{rounded.field}"
    padding: "0.3rem 0.5rem"
---

# Design System: Stack Internal Skills

## Overview

**Creative North Star: "Release Field Manual"**

Stack Internal Skills reads as an auditable technical guide, not a soft SaaS gallery. Cool paper, navy ink, ruled boundaries, monospaced registration labels, and numbered records make source, safety, and installation state scannable at a glance.

The system is deliberately dense but ordered: product truth and the core install ledger share the opening field, then filters and skill records continue the same ruled register. Color communicates function rather than decoration—blue marks action and selection, green marks read-only status, and amber is reserved for approval-gated write capability.

**Key Characteristics:**

- Ruled ledger layouts and square index controls over rounded card collections.
- System sans for reading, paired with monospace only for provenance, commands, versions, and classifications.
- Strong semantic color discipline for actions, permissions, and keyboard focus.

## Colors

The palette is cool, document-like, and functional: paper surfaces carry the interface while dark ink, blue action, green read state, and amber write state keep status unambiguous.

### Primary

- **Registration Blue:** Marks selected tabs, copy actions, record numbers, and interactive emphasis.
- **Deep Link Blue:** Keeps standard text links legible against paper while reserving brighter blue for hover and selected state.

### Secondary

- **Approval Amber:** Appears only with approval-gated write capability and its associated safety callout.
- **Read Green:** Marks read-only permission stamps without competing with action blue.

### Neutral

- **Cool Paper:** The default document field, with raised white for input and hover surfaces and pale blue for an active ledger field.
- **Navy Ink:** Carries primary reading text and strong record rules; muted ink carries supporting explanation.
- **Ledger Rules:** Light and strong rules create columns, sections, and registers instead of shadows.

### Named Rules

**The Permission Color Rule.** Blue is for action or selection, green is for read-only capability, and amber is exclusively for approval-gated write capability.

**The Ruled Surface Rule.** Establish grouping with paper tones and one-pixel rules; do not substitute soft, floating cards.

## Typography

**Display Font:** System sans stack
**Body Font:** System sans stack
**Label/Mono Font:** System monospace stack

**Character:** Large sans headlines give the manual a direct technical voice. Monospace is a measured annotation layer for commands, versions, field indexes, and classifications—not the default reading face.

### Hierarchy

- **Display:** Used for the opening installation statement and record titles; tightly tracked and heavy enough to anchor the field.
- **Headline:** Used for section and directory headings; it keeps the display’s compact tracking at a smaller scale.
- **Title:** Used for skill names inside directory records.
- **Body:** The default reading text, set with a comfortable 1.55 line height and a 72ch maximum measure where prose runs long.
- **Label:** A compact, uppercase-capable monospace annotation style for registers, versions, filter legends, and classification.

### Named Rules

**The Annotation Layer Rule.** Use monospace to label evidence and controls; reserve proportional sans for product statements and explanatory prose.

## Layout

The desktop field is capped at an 84rem page width with a 72ch text measure. The opening uses a 1.1fr/0.9fr split between product truth and the core ledger; the detail page uses a 15rem sticky field index beside the content. Spacing follows the six-step scale in the frontmatter, from tight label gaps through generous section breaks.

At 900px the opening and detail layouts become single-column, while the field index becomes a two-column reference grid. At 720px, the navigation, filters, directory records, and troubleshooting ledger stack vertically; truth facts retain a two-column register. Interactive targets keep a 44px minimum height, and reduced-motion users receive effectively instant transitions.

## Elevation & Depth

This is a flat document system. There are no box shadows: tonal paper changes and ledger rules describe hierarchy, while a dark command specimen creates a distinct terminal-like instruction surface. The copy-status notice uses fixed placement and opacity/translation only for transient depth.

### Named Rules

**The Flat Evidence Rule.** Depth comes from a ruled boundary, a column change, or a paper-tone change—not from ambient card shadows.

## Shapes

The form language is square and indexed. Search fields, tabs, tags, and permission stamps are explicitly square. Borders are thin, straight, and structural, with stronger rules dividing major fields and dark top rules beginning record ledgers.

## Components

### Buttons

**Character:** Compact administrative controls, built into the ledger rather than floating above it.

- **Copy action:** Dark blue command-side control with light text, a square silhouette, and a brighter blue hover state.
- **Tabs:** Square segmented controls; only the selected tab is blue with light text.
- **Focus:** Every keyboard-reachable control uses the global three-pixel blue outline with a three-pixel offset.

### Chips

**Character:** Small evidence stamps, not decorative pills.

- **Tags:** Plain ruled labels with compact padding and no rounded corners.
- **Permissions:** Read-only uses the green paper/ink pair; approval-gated write uses the amber paper/ink pair.

### Cards / Containers

**Character:** Horizontal field records rather than independently elevated cards.

- **Corner Style:** Square.
- **Background:** Cool paper at rest, raised paper on record hover, pale blue for ledger emphasis.
- **Shadow Strategy:** None; use rules and paper-tone shifts.
- **Border:** Strong section dividers and light internal column rules.
- **Internal Padding:** Record content uses the middle steps of the spacing scale.

### Inputs / Fields

**Character:** A white document insert surrounded by a strong rule.

- **Style:** Square, raised-paper search field with navy text and strong border.
- **Focus:** Global blue focus outline; checkbox controls use the registration-blue accent color.

### Navigation

**Character:** A ruled reference strip with fully usable text links.

- **Style:** Wordmark and links sit between horizontal rules; links are divided by vertical rules and gain the pale-blue field on hover.
- **Responsive treatment:** It becomes a three-column, ruled link grid on narrow screens.

### Field Record

**Character:** A three-column release register: numerical index, evidence body, and capability/action metadata.

- **Structure:** Strong top rule, a numbered blue register, and ruled metadata columns.
- **State:** Hover raises only the paper tone; it never adds a shadow or rounded card treatment.

## Do's and Don'ts

### Do:

- **Do** use ruled columns, numbered records, and compact metadata to make technical evidence easy to audit.
- **Do** use registration blue for selected controls, action affordances, and visible keyboard focus.
- **Do** keep installation commands in a dark, high-contrast specimen with a dedicated copy action.
- **Do** reserve amber for the precise moment a capability is approval-gated and write-capable.

### Don't:

- **Don't** turn the directory into a generic grid of rounded, shadowed SaaS cards.
- **Don't** use amber as an ordinary accent, warning flourish, or non-write status color.
- **Don't** use monospace as the main reading face; it is an annotation tool.
- **Don't** hide installation, MCP authorization, or experimental-compatibility boundaries behind marketing language.
