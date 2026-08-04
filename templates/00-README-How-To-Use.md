# Documentation Template Pack — How To Use With an LLM

This folder contains **8 locked-format templates** plus this instruction file. They encode the exact structure, tone, and visual conventions used across your project docs (badges, color palette, section numbering, Mermaid diagram theming, table styles) — independent of any specific project's content.

## Purpose

Instead of letting an LLM invent its own report structure per project, you give it:
1. **This README** (the rules).
2. **The 8 template files** (the skeletons, one per doc type).
3. **Your project's source material** (a repo, a description, code, etc.).

The LLM's job becomes: *fill in the placeholders, following the rules below* — not *design a new report format*.

## The 8 Templates

| # | File | Purpose |
|---|---|---|
| 1 | `TEMPLATE-PRD.md` | Product requirements — overview, goals, personas, features, success metrics |
| 2 | `TEMPLATE-Architecture-Design.md` | System architecture, components, data flow, trade-offs |
| 3 | `TEMPLATE-Database-Design.md` | Data storage — current state + proposed schema if applicable |
| 4 | `TEMPLATE-API-Specification.md` | Interface contracts (HTTP or in-process), request/response shapes |
| 5 | `TEMPLATE-Deployment-Guide.md` | How the project is (or would be) deployed, env vars, rollback |
| 6 | `TEMPLATE-Run-Locally.md` | Local setup, prerequisites, verification steps, troubleshooting |
| 7 | `TEMPLATE-Stack-and-Techniques.md` | Languages, libraries, ML/technical techniques, testing status |
| 8 | `TEMPLATE-Review-and-TODO.md` | Honest strengths/risks review + prioritized TODO list |

## Global Rules (apply to every template)

1. **Never invent new top-level structure.** Keep every `##` heading in a template, in order. Do not add, remove, reorder, or rename sections unless a section is explicitly marked `(omit if not applicable)`.
2. **Badges are mandatory**, first line of every file, using this exact pattern:
   ```
   ![status](https://img.shields.io/badge/status-{STATUS}-2E74B5?style=flat-square) ![type](https://img.shields.io/badge/type-{TYPE}-1F4D78?style=flat-square)
   ```
   - `{STATUS}` = `active`, `no%20database`, `no%20REST%20API`, `draft`, etc. (URL-encode spaces as `%20`).
   - `{TYPE}` = one lowercase word matching the doc: `PRD`, `architecture`, `database`, `API`, `deployment`, `setup`, `stack`, `review`.
3. **Title block is mandatory**, exactly this shape:
   ```
   # {Document Title}
   ### {Project Name}

   ---
   ```
4. **Color palette is fixed** unless the project supplies its own theme — reuse these hex values everywhere (badges, Mermaid `themeVariables`):
   - Primary: `#2E74B5`
   - Secondary: `#1F4D78`
   - Accent: `#0563C1`
   - Tertiary/fill: `#EAF1FA`
   If the project has its own brand colors, substitute them consistently across **all 8 docs**, not just one.
5. **Mermaid diagrams**: every diagram opens with this init line (swap colors per rule 4 if rebranded):
   ```
   %%{init: {'theme':'base','themeVariables':{'primaryColor':'#2E74B5','primaryTextColor':'#ffffff','primaryBorderColor':'#1F4D78','lineColor':'#1F4D78','tertiaryColor':'#EAF1FA'}}}%%
   ```
   Use `flowchart`, `sequenceDiagram`, or `erDiagram` as appropriate — never a bare, unstyled diagram.
6. **Tables over prose** for anything enumerable (inputs/outputs, components, personas, troubleshooting steps, tech stack). Prose is for explaining *why*, tables are for listing *what*.
7. **Honesty over polish.** State clearly when something is "not implemented," "proposed — not present in the repo," "inferred," or "no verified information exists." Do not present proposed/future work as if it already exists. Mark inferred content explicitly with *(inferred)*.
8. **Cross-reference other docs** by name in italics, e.g. `*see Deployment-Guide.md, section 6*`, instead of duplicating content across files.
9. **No filler sections.** If a section genuinely doesn't apply (e.g. no database exists), keep the heading but state that plainly in 1–2 sentences rather than deleting the section or padding it.
10. **Voice**: direct, technical, no marketing language. Prefer "This project does X" over "This innovative solution leverages X."

## Prompt to Paste Into an LLM

```
You will generate professional project documentation using a fixed template pack.

Rules:
- Follow every rule in 00-README-How-To-Use.md exactly.
- For each of the 8 template files I provide, keep the section structure, badges, title block, color palette, and Mermaid styling identical to the template — only replace the {PLACEHOLDER} content with real information about the project below.
- Do not add, remove, or reorder ## sections.
- Do not invent features, metrics, or architecture that aren't evidenced by the project material I give you. Mark anything you must infer as "(inferred)".
- Where the template shows an example table/diagram, replace its contents but keep its shape.

Project material:
[paste repo README / code / description / links here]

Generate the 8 files now, one at a time, in this order: PRD, Architecture-Design, Database-Design, API-Specification, Deployment-Guide, Run-Locally, Stack-and-Techniques, Review-and-TODO.
```

## Tip
Keep this pack itself project-agnostic — don't edit the templates to match one specific project. If you want a *second* palette (e.g. for a different client brand), duplicate this whole folder rather than overwriting it.
