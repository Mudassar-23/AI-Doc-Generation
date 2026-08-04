![status](https://img.shields.io/badge/status-{STATUS}-2E74B5?style=flat-square) ![type](https://img.shields.io/badge/type-PRD-1F4D78?style=flat-square)

# Product Requirements Document
### {Project Name}

> Source: [`{owner}/{repo}`]({repo_url})

---

## 1. Overview

{2–4 sentences: what the project is, what problem it estimates/solves/does, and the number of distinct delivery paths or components it ships (e.g. "two parallel front ends", "a single CLI tool"). Name each major deliverable.}

1. **{Deliverable A}** ({file/module}) — {one-line description}.
2. **{Deliverable B}** ({file/module}) — {one-line description}.

{State deployment/availability status in one sentence, e.g. "Both are live at: ..." or "Not yet deployed."}

## 2. Problem Statement

{1 paragraph. What gap or naive approach does this project move beyond? What is the project's *real* subject/lesson/value — be honest if it's a teaching artifact, portfolio piece, MVP, or production system.}

## 3. Goals

- {Goal 1 — outcome-oriented, not a feature list}
- {Goal 2}
- {Goal 3}
- {Goal 4, optional}

## 4. Non-Goals

- {Explicitly out of scope item 1}
- {Explicitly out of scope item 2}
- {Explicitly out of scope item 3}
- {Any inferred non-goal} *(inferred: {one-line justification})*

## 5. Target Users

| Persona | Need |
|---|---|
| **{Persona 1}** | {What they want from this project} |
| **{Persona 2}** | {What they want from this project} |
| **{Persona 3}** | {What they want from this project} |

## 6. Core Features *(as implemented)*

- {Feature 1 — tie to concrete input/output}
- {Feature 2}
- {Feature 3}
- {Feature 4}
- {Feature 5, if there's a notable UX/visual detail worth naming}

## 7. Success Metrics *(proposed — not currently instrumented, if applicable)*

{State plainly if no analytics/logging exists yet, then list suggested targets rather than measured facts.}

- {Metric 1, e.g. performance target}
- {Metric 2, e.g. UX smoothness target}
- {Metric 3, e.g. cold-start / onboarding time target}
- Repo: a new contributor can go from clone to a working local {result} in under {N} minutes (see *Run-Locally.md*).

## 8. Assumptions

- {Assumption about data/scale, e.g. "dataset is a placeholder, not production data"}
- {Assumption about parity between delivery paths, and whether it's enforced — cross-ref *Review-and-TODO.md* if not}
- {Assumption about what "deployment" means in this context}

## 9. Open Questions

- {Open question 1 — e.g. should two implementations be consolidated?}
- {Open question 2 — e.g. is there intent to scale beyond current data/scope?}
