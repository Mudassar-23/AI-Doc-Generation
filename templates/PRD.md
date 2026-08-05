# Product Requirements Document
### {{PROJECT_NAME}}

| Field | Value |
|---|---|
| **ID** / **Version** / **Status** | `{{PROJECT_SLUG}}-PRD-001` · `{{DOC_VERSION}}` · `{{DOC_STATUS}}` |
| **Owner** / **Source** | `{{DOC_OWNER}}` · `{{REPO_URL}}` @ `{{COMMIT_SHA}}` |
| **Generated** / **Confidence** | `{{GENERATED_AT}}` by `{{GENERATOR}}` · `{{CONFIDENCE_PCT}}%` |

---

## 1. Executive Summary
{{EXECUTIVE_SUMMARY}}

| Dimension | Value | Evidence |
|---|---|---|
| Category / Maturity / Users | {{SYSTEM_CATEGORY}} · {{MATURITY}} · {{PRIMARY_USERS}} | `{{EVIDENCE_CATEGORY}}` |
| Deployment / Criticality / Size | {{DEPLOYMENT_MODEL}} · {{CRITICALITY}} · {{LOC}} LOC | `{{EVIDENCE_SIZE}}` |

> [!IMPORTANT]
> {{HEADLINE_CAVEAT}}

---

## 2. Purpose & Capabilities

**Purpose.** {{PURPOSE_NARRATIVE}}

| # | Capability | Description | Evidence |
|---|---|---|---|
{{#EACH capabilities}}
| C-{{INDEX}} | {{CAPABILITY_NAME}} | {{CAPABILITY_DESC}} | `{{CAPABILITY_EVIDENCE}}` |
{{/EACH}}

| # | Does **not** do | Verification |
|---|---|---|
{{#EACH non_capabilities}}
| N-{{INDEX}} | {{NON_CAPABILITY}} | `{{SEARCH_PERFORMED}}` |
{{/EACH}}

| Value | Beneficiary | Evidence |
|---|---|---|
{{#EACH value_props}}
| {{VALUE_PROP}} | {{BENEFICIARY}} | `{{VALUE_EVIDENCE}}` |
{{/EACH}}

---

## 3. System Context

<!-- ANCHOR: system-context -->

```mermaid
%%{init: {'theme':'base','themeVariables':{'primaryColor':'#2E74B5','primaryTextColor':'#ffffff','primaryBorderColor':'#1F4D78','lineColor':'#1F4D78','secondaryColor':'#EAF1FA','tertiaryColor':'#EAF1FA','fontFamily':'Segoe UI, Inter, sans-serif','fontSize':'14px'}}}%%
flowchart TB
    subgraph ACTORS["Actors"]
        A1(["{{ACTOR_1}}"])
        A2(["{{ACTOR_2}}"])
    end
    subgraph SYSTEM["{{PROJECT_NAME}}"]
        FE["{{FRONTEND_COMPONENT}}"]
        BE["{{BACKEND_COMPONENT}}"]
        WK["{{WORKER_COMPONENT}}"]
        FE --> BE --> WK
    end
    DB[("{{PRIMARY_DATASTORE}}")]
    E1(["{{EXTERNAL_1}}"])
    E2(["{{EXTERNAL_2}}"])
    A1 -->|"{{ACTOR_1_ACTION}}"| FE
    A2 -->|"{{ACTOR_2_ACTION}}"| FE
    BE --> DB
    WK --> DB
    BE -->|"{{EXT_1_PROTOCOL}}"| E1
    WK -->|"{{EXT_2_PROTOCOL}}"| E2
    classDef core fill:#2E74B5,stroke:#1F4D78,color:#ffffff,stroke-width:1px;
    classDef store fill:#EAF1FA,stroke:#1F4D78,color:#1F4D78,stroke-width:1px;
    classDef external fill:#F0E9FA,stroke:#6B4E9E,color:#4A356F,stroke-width:1px;
    classDef actor fill:#E3F5EA,stroke:#1E7A4B,color:#12613A,stroke-width:1px;
    class FE,BE,WK core;
    class DB store;
    class E1,E2 external;
    class A1,A2 actor;
```

{{CONTEXT_NOTES}}

---

## 4. Users & Roles

| Persona | Goal | Entry | Evidence | Conf. |
|---|---|---|---|---|
{{#EACH personas}}
| **{{PERSONA_NAME}}** | {{PERSONA_GOAL}} | {{PERSONA_ENTRY}} | `{{PERSONA_EVIDENCE}}` | {{PERSONA_CONFIDENCE}} {{?PERSONA_ASSUMPTION_ID}} |
{{/EACH}}

| Role | Enforcement | {{CAP_1}} | {{CAP_2}} | {{CAP_3}} |
|---|---|:--:|:--:|:--:|
{{#EACH roles}}
| **{{ROLE_NAME}}** | `{{ROLE_ENFORCEMENT}}` | {{P1}} | {{P2}} | {{P3}} |
{{/EACH}}

{{AUTHZ_NARRATIVE}}

---

## 5. Features & Requirements

```mermaid
%%{init: {'theme':'base','themeVariables':{'primaryColor':'#2E74B5','primaryTextColor':'#ffffff','primaryBorderColor':'#1F4D78','lineColor':'#1F4D78','tertiaryColor':'#EAF1FA','fontFamily':'Segoe UI, Inter, sans-serif'}}}%%
flowchart LR
    ROOT(["{{PROJECT_NAME}}"]) --> M1["{{MODULE_1}}"] & M2["{{MODULE_2}}"] & M3["{{MODULE_3}}"]
    M1 --> F11["{{FEATURE_1_1}}"] & F12["{{FEATURE_1_2}}"]
    M2 --> F21["{{FEATURE_2_1}}"] & F22["{{FEATURE_2_2}}"]
    M3 --> F31["{{FEATURE_3_1}}"] & F32["{{FEATURE_3_2}}"]
    classDef core fill:#2E74B5,stroke:#1F4D78,color:#ffffff,stroke-width:1px;
    classDef store fill:#EAF1FA,stroke:#1F4D78,color:#1F4D78,stroke-width:1px;
    classDef success fill:#E3F5EA,stroke:#1E7A4B,color:#12613A,stroke-width:1px;
    class ROOT success;
    class M1,M2,M3 core;
    class F11,F12,F21,F22,F31,F32 store;
```

| Module | Owns | Entry | Status |
|---|---|---|---|
{{#EACH modules}}
| **{{MODULE_NAME}}** | {{MODULE_RESPONSIBILITY}} | `{{MODULE_ENTRY}}` | {{MODULE_STATUS}} |
{{/EACH}}

| ID | Requirement (RFC 2119) | MoSCoW | Evidence | Conf. |
|---|---|---|---|---|
{{#EACH functional_requirements}}
| `FR-{{INDEX}}` | The system **{{RFC_KEYWORD}}** {{REQUIREMENT_TEXT}} | {{MOSCOW}} | `{{FR_EVIDENCE}}` | {{FR_CONF}} |
{{/EACH}}

---

## 6. Primary Journey

<!-- ANCHOR: primary-journey -->

```mermaid
%%{init: {'theme':'base','themeVariables':{'primaryColor':'#2E74B5','primaryTextColor':'#ffffff','primaryBorderColor':'#1F4D78','lineColor':'#1F4D78','tertiaryColor':'#EAF1FA','fontFamily':'Segoe UI, Inter, sans-serif'}}}%%
flowchart TD
    START(["{{JOURNEY_ENTRY}}"]) --> AUTH{"{{AUTH_DECISION}}"}
    AUTH -->|"{{AUTH_YES}}"| STEP1["{{JOURNEY_STEP_1}}"]
    AUTH -->|"{{AUTH_NO}}"| FALLBACK["{{AUTH_FALLBACK}}"]
    FALLBACK --> STEP1
    STEP1 --> STEP2["{{JOURNEY_STEP_2}}"]
    STEP2 --> VALIDATE{"{{VALIDATION_DECISION}}"}
    VALIDATE -->|"{{VALID}}"| STEP3["{{JOURNEY_STEP_3}}"]
    VALIDATE -->|"{{INVALID}}"| ERR["{{ERROR_PATH}}"]
    ERR --> STEP2
    STEP3 --> DONE(["{{JOURNEY_OUTCOME}}"])
    classDef core fill:#2E74B5,stroke:#1F4D78,color:#ffffff,stroke-width:1px;
    classDef danger fill:#FDE8E8,stroke:#B91C1C,color:#B91C1C,stroke-width:1px;
    classDef success fill:#E3F5EA,stroke:#1E7A4B,color:#12613A,stroke-width:1px;
    classDef warn fill:#FEF3C7,stroke:#B45309,color:#92400E,stroke-width:1px;
    class STEP1,STEP2,STEP3 core;
    class ERR danger;
    class START,DONE success;
    class FALLBACK warn;
```




---

## 7. Integrations & Data

| System | Dir | Protocol | Criticality | Failure behaviour | Evidence |
|---|---|---|---|---|---|
{{#EACH integrations}}
| {{INT_SYSTEM}} | {{INT_DIRECTION}} | {{INT_PROTOCOL}} | {{INT_CRITICALITY}} | {{INT_FAILURE}} | `{{INT_EVIDENCE}}` |
{{/EACH}}

| Entity | Meaning | Owned? | Physical |
|---|---|---|---|
{{#EACH entities}}
| **{{ENTITY_NAME}}** | {{ENTITY_MEANING}} | {{ENTITY_OWNED}} | *`Database Design.md`* |
{{/EACH}}

```mermaid
%%{init: {'theme':'base','themeVariables':{'primaryColor':'#2E74B5','primaryTextColor':'#ffffff','primaryBorderColor':'#1F4D78','lineColor':'#1F4D78','tertiaryColor':'#EAF1FA','fontFamily':'Segoe UI, Inter, sans-serif'}}}%%
stateDiagram-v2
    direction LR
    [*] --> {{STATE_1}} : {{TRANSITION_CREATE}}
    {{STATE_1}} --> {{STATE_2}} : {{TRANSITION_1_2}}
    {{STATE_2}} --> {{STATE_3}} : {{TRANSITION_2_3}}
    {{STATE_2}} --> {{STATE_FAIL}} : {{TRANSITION_2_FAIL}}
    {{STATE_FAIL}} --> {{STATE_1}} : {{TRANSITION_RETRY}}
    {{STATE_3}} --> [*] : {{TRANSITION_TERMINAL}}
```

---

## 8. NFRs, Constraints & Debt

| ID | Area | Requirement | Target / Observed | Evidence |
|---|---|---|---|---|
{{#EACH nfrs}}
| `NFR-{{INDEX}}` | {{NFR_AREA}} | {{NFR_TEXT}} | {{NFR_TARGET}} | `{{NFR_EVIDENCE}}` |
{{/EACH}}

| Constraint / Out of scope | Detail | Evidence |
|---|---|---|
{{#EACH constraints}}
| {{CONSTRAINT_TYPE}} | {{CONSTRAINT_TEXT}} | `{{CONSTRAINT_EVIDENCE}}` |
{{/EACH}}
{{#EACH out_of_scope}}
| OOS | {{OOS_ITEM}} | `{{OOS_SEARCH}}` |
{{/EACH}}

| ID | Debt | Sev | Effort | Evidence |
|---|---|:--:|---|---|
{{#EACH tech_debt}}
| `TD-{{INDEX}}` | {{DEBT_ITEM}} | {{DEBT_SEVERITY}} | {{DEBT_EFFORT}} | `{{DEBT_EVIDENCE}}` |
{{/EACH}}

```mermaid
quadrantChart
    title Debt — impact vs effort
    x-axis "Low effort" --> "High effort"
    y-axis "Low impact" --> "High impact"
    quadrant-1 "Plan"
    quadrant-2 "Fix now"
    quadrant-3 "Monitor"
    quadrant-4 "Accept"
    "{{DEBT_LABEL_1}}": [{{DEBT_X_1}}, {{DEBT_Y_1}}]
    "{{DEBT_LABEL_2}}": [{{DEBT_X_2}}, {{DEBT_Y_2}}]
    "{{DEBT_LABEL_3}}": [{{DEBT_X_3}}, {{DEBT_Y_3}}]
```

| ID | Assumption | Impact if wrong |
|---|---|---|
{{#EACH assumptions}}
| `{{ASSUMPTION_ID}}` | {{ASSUMPTION_TEXT}} | {{ASSUMPTION_IMPACT}} |
{{/EACH}}
> See *`Review and TODO.md`*.
*End of `{{PROJECT_SLUG}}-PRD-001` → *`Architecture Design.md`*.*
