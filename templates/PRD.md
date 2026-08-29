# Product Requirements Document
### {{PROJECT_NAME}}

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


