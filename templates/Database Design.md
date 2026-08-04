![status](https://img.shields.io/badge/status-{STATUS}-2E74B5?style=flat-square) ![type](https://img.shields.io/badge/type-database-1F4D78?style=flat-square)

# Database Design
### {Project Name}

---

## 1. Current State

{If there is genuinely no database: state it plainly — "This project does not use a database. There is no verified information in the repository suggesting otherwise." Then describe whatever flat-file/in-memory persistence does exist.}
{If there IS a database: describe the engine, and list the actual tables/collections in a table below instead of the flat-file table.}

| Artifact | Role |
|---|---|
| `{file_or_table_1}` | {What it stores and when it's read/written} |
| `{file_or_table_2}` | {What it stores and when it's read/written} |

{One sentence on statefulness: is any request/prediction/action logged or stored, or is everything stateless?}

```mermaid
%%{init: {'theme':'base','themeVariables':{'primaryColor':'#2E74B5','primaryTextColor':'#ffffff','primaryBorderColor':'#1F4D78','lineColor':'#1F4D78','tertiaryColor':'#EAF1FA'}}}%%
flowchart LR
    A["{source data}"] -->|{when}| B["{processing step}"]
    B -->|{output action}| C["{artifact}"]
    C -->|{consumption}| D["{consumer}"]
    D -->|{result}| E["{end state, e.g. 'nothing persisted'}"]
```

## 2. Proposed Schema *(inferred — not implemented, if applicable)*

{Only include this section if a future/extended schema is a reasonable next step. State clearly this is a suggestion, not existing code.}

```mermaid
%%{init: {'theme':'base','themeVariables':{'primaryColor':'#2E74B5','primaryTextColor':'#ffffff','primaryBorderColor':'#1F4D78','lineColor':'#1F4D78','tertiaryColor':'#EAF1FA'}}}%%
erDiagram
    {ENTITY_NAME} {
        int id PK
        {type} {field_1}
        {type} {field_2}
        datetime created_at
    }
```

### Proposed `{table_name}` table

| Column | Type | Notes |
|---|---|---|
| `id` | `INTEGER PRIMARY KEY` | Auto-increment |
| `{field_1}` | `{TYPE}` | {Notes} |
| `{field_2}` | `{TYPE}` | {Notes} |
| `created_at` | `TIMESTAMP` | Default `now()` |

### Notes on the proposal

- {Note 1 — e.g. normalization is/isn't needed at this scale}
- {Note 2 — why a specific field matters given the project's specific quirks}
- {Note 3 — recommended engine/tech for this scale, and any component that couldn't write to it directly}

## 3. If Growing {The Core Dataset}

{1 short paragraph: what the natural next step would be if the current data source (CSV, hardcoded list, etc.) needs to become a real data store. State this is not currently needed if the scale doesn't warrant it.}
