# OrquestaGit — Control Center specification (RepoBar layout)

UI/UX design spec for the Control Center. Styles are based on the shared
`brand.css` design system.

## Principle

A single surface that **opens with cached data** (never empty) and refreshes in
the background. The user sees state and acts; logs live in a collapsible drawer,
not center stage.

## Four levels

1. **Global dashboard** — context strip, actionable KPIs, alerts.
2. **Repository list** — each repo is one row with fixed columns.
3. **Per-repo detail** — right-hand side panel with tabs (Summary, Git, Security, CI/CD).
4. **Tools** — Architect, bulk cleanup, and so on; shown only when acting.

## Context strip (top)

`[active folder v] · [local engine ● updated 2 min ago] · ......... · [search] [refresh all]`

Showing data freshness ("fetched 30s ago", "reading cache") noticeably raises the
perceived quality of the app.

## Actionable KPIs

Each KPI filters the list when clicked; none are decorative:
Repos · High vulnerabilities · CI failing · Unpushed · Dead branches · No upstream.

## Repository row (fixed columns)

| Zone | Content |
|------|---------|
| Left | Name · detected stack · short path |
| Git | Branch · last commit · ahead/behind · dirty files |
| State | Chips: `clean` `CI failed` `no upstream` `N vulns` `down N` `up N` |
| Actions | Open folder · open on GitHub · audit · clean · sync |

Clicking a row opens the detail panel (level 3).

## Detail panel (right, collapsible)

Short tabs: **Summary · Git · Security · CI/CD**.

- **Summary**: health, security, git, last scan, and a recommended action.
- **Security**: findings ordered by severity (severity · package + range · advisory · fixing version), a copyable fix command, and a "Fix" button **with confirmation**.
- **Git**: branch, ahead/behind, dirty, safe fast-forward sync, reflog.
- **CI/CD**: last workflow, status, logs, generate workflow.

## Design rules (critical)

- **Color means state, never decoration**: green = clean, amber = warning, red = problem, gray = not configured.
- **Chips are identical across the app**: "no upstream" looks the same in the Dashboard, the radar and the auditor.
- **Never an empty console by default**: with no data, show a "last scan unavailable" card plus an action.
- **The console** is a collapsible bottom drawer, for debugging only.

## Safe automation (no smoke and mirrors)

- Auto-fetch: all repos, every N minutes.
- Auto-pull: only when clean **and** a fast-forward is possible.
- Auto-audit: on open and when a new commit is detected.
- Cleanup / fix: suggest, then confirm. Never silently destructive.

## Consolidated to six modules

Repositories (state) · Security · CI/CD · Hygiene · Local Git · Architect —
all feeding the same dashboard.
