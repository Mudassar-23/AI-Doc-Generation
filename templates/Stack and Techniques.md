![status](https://img.shields.io/badge/status-{STATUS}-2E74B5?style=flat-square) ![type](https://img.shields.io/badge/type-stack-1F4D78?style=flat-square)

# Stack & Techniques
### {Project Name}

---

## 1. Languages

- **{Language 1}** — {what it's used for}
- **{Language 2}** — {what it's used for}
- **{Language 3, if applicable}** — {what it's used for}

## 2. Core Libraries & Dependencies

From `{manifest file, e.g. requirements.txt / package.json}`:

| Package | Used for |
|---|---|
| `{package_1}` | {what it does in this project} |
| `{package_2}` | {what it does in this project} |
| `{package_3}` | {what it does in this project} |

{If applicable — packages used but NOT pinned in the manifest:}

| Package | Used for |
|---|---|
| `{package}` | {what it does in this project} |

## 3. Core Technique / Domain Logic

{Rename this section to match the project's actual domain — e.g. "Machine Learning", "Payment Processing", "Real-time Sync". Describe:}

- **{What is built/trained/computed}:** {detail}
- **{What is shipped/chosen}:** {detail, with honesty about whether the choice is backed by evidence — cross-ref *Review-and-TODO.md* if not}
- **{Inputs/Features}:** {detail}
- **{Data/scale note}:** {detail, cross-ref *Review-and-TODO.md* if there's a scale/quality risk}

## 4. {Standout Technique Name}

{Name and describe the one technique that makes this project interesting or non-obvious — the "how it actually works under the hood" section.}

```{language}
{short, real code snippet illustrating the technique}
```

{1–2 sentences on the practical effect: what this technique removes the need for (a server, a runtime, a manual step), and what constraint it introduces instead.}

## 5. Frontend / Interface Techniques

- **{Technique 1}:** {detail}
- **{Technique 2}:** {detail}
- **{Formatting/UX detail}:** {detail, e.g. number/date/currency formatting}

## 6. Design System *(if applicable)*

{Only include if a design system doc/tokens file actually exists in the repo.}

Documented explicitly in `{design doc path}` ("{design system name}"):

- **Palette:** {colors and how they're used}
- **Typography:** {fonts and where each is used}
- **Elevation / layering:** {approach}
- **Components:** {button/card/etc. style notes}

## 7. Architectural Pattern

{1–2 sentences naming the pattern(s) in play — e.g. "compiled inference" vs. "client-server", monolith vs. microservices, event-driven vs. request-response. Cross-ref *Architecture-Design.md* for the full diagram.}

## 8. Testing

{State plainly what test coverage exists today — unit, integration, visual — or that none exists, for each track/component.}
