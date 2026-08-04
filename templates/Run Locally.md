![status](https://img.shields.io/badge/status-{STATUS}-2E74B5?style=flat-square) ![type](https://img.shields.io/badge/type-setup-1F4D78?style=flat-square)

# Run Locally
### {Project Name}

---

## 1. Prerequisites

- {Runtime + version, e.g. "Python 3.9+"}
- {Package manager}
- Git
- {Any optional/track-specific prerequisite}

## 2. Clone the Project

```bash
git clone {repo_url}
cd {repo_dir}
```

## 3. Track A — Run {Component/App Name}

```bash
{install command}
{run command}
# or, equivalently:
{alternate run command}
```

{One sentence: what URL/port it runs on, and what to do once it's open.}

**Verify it's running:** {a specific, checkable signal — a page title, a banner, an output line — not just "it works."}

## 4. Track B — Run {Second Component, if applicable}

{Only include if there's a second runnable path. Same shape as Track A.}

```bash
{commands}
```

{One sentence on why serving vs. opening directly matters, if relevant.}

**Verify it's running:** {specific, checkable signal}.

## 5. {Optional Task, e.g. Retraining / Rebuilding / Seeding Data}

```bash
{commands}
```

{Numbered list of what running this actually does, step by step.}

1. {Step 1}
2. {Step 2}
3. {Step 3}

> {Callout: any dependency that's used but not pinned in the manifest — install manually as shown, and note where the output needs to go. Cross-ref *Deployment-Guide.md* if relevant.}

## 6. Troubleshooting

| Symptom | Likely Cause | Fix |
|---|---|---|
| `{error message or symptom}` | {cause} | {fix} |
| `{error message or symptom}` | {cause} | {fix} |
| `{error message or symptom}` | {cause} | {fix} |
| `{error message or symptom}` | {cause} | {fix, or cross-ref another doc if it's expected behavior rather than a bug} |
