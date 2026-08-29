# System Architecture & Design
### {{PROJECT_NAME}}

---

## 1. Architecture at a Glance

{{ARCHITECTURE_SUMMARY}}

| Unit | Type | Runtime | Entry | Stateful? |
|---|---|---|---|---|
{{#EACH deployables}}
| **{{UNIT_NAME}}** | {{UNIT_TYPE}} | {{UNIT_RUNTIME}} | `{{UNIT_ENTRY}}` | {{UNIT_STATEFUL}} |
{{/EACH}}

| # | Decision | Chosen | Not taken | ADR |
|---|---|---|---|---|
{{#EACH defining_decisions}}
| D-{{INDEX}} | {{DECISION_TOPIC}} | {{DECISION_CHOICE}} | {{DECISION_ALTERNATIVE}} | `{{ADR_ID}}` |
{{/EACH}}

---

## 2. Technology Stack

| Layer | Technology | Version | Manifest | Usage | State |
|---|---|---|---|---|---|
{{#EACH stack_runtime}}
| {{STACK_LAYER}} | **{{STACK_TECH}}** | `{{STACK_VERSION}}` | `{{STACK_MANIFEST}}` | `{{STACK_USAGE}}` | {{STACK_STATE}} |
{{/EACH}}

| Deps / Lockfile / Unused / Platform-locked | {{DEP_COUNT}} · {{LOCKFILE_STATUS}} · {{UNUSED_DEPS}} · {{PLATFORM_DEPS}} | `{{DEP_EVIDENCE}}` |

---

## 3. Architecture Views

### 3.1 Context

```mermaid
%%{init: {'theme':'base','themeVariables':{'primaryColor':'#2E74B5','primaryTextColor':'#ffffff','primaryBorderColor':'#1F4D78','lineColor':'#1F4D78','secondaryColor':'#EAF1FA','tertiaryColor':'#EAF1FA','fontFamily':'Segoe UI, Inter, sans-serif','fontSize':'14px'}}}%%
flowchart TB
    U1(["{{L1_ACTOR_1}}"]) --> SYS["{{PROJECT_NAME}}"]
    U2(["{{L1_ACTOR_2}}"]) --> SYS
    SYS -->|"{{L1_EDGE_3}}"| X1(["{{L1_EXTERNAL_1}}"])
    SYS -->|"{{L1_EDGE_4}}"| X2(["{{L1_EXTERNAL_2}}"])
    classDef core fill:#2E74B5,stroke:#1F4D78,color:#ffffff,stroke-width:2px;
    classDef external fill:#F0E9FA,stroke:#6B4E9E,color:#4A356F,stroke-width:1px;
    classDef actor fill:#E3F5EA,stroke:#1E7A4B,color:#12613A,stroke-width:1px;
    class SYS core;
    class X1,X2 external;
    class U1,U2 actor;
```

### 3.2 Containers

```mermaid
%%{init: {'theme':'base','themeVariables':{'primaryColor':'#2E74B5','primaryTextColor':'#ffffff','primaryBorderColor':'#1F4D78','lineColor':'#1F4D78','secondaryColor':'#EAF1FA','tertiaryColor':'#EAF1FA','fontFamily':'Segoe UI, Inter, sans-serif','fontSize':'14px'}}}%%
flowchart TB
    USER(["{{L2_ACTOR}}"]) --> WEB["{{L2_FRONTEND}}"] -->|"{{L2_EDGE_WEB_API}}"| API["{{L2_API}}"]
    API --> DB[("{{L2_DATABASE}}")]
    API --> CACHE[("{{L2_CACHE}}")]
    API -->|"{{L2_EDGE_API_IDP}}"| IDP(["{{L2_IDENTITY}}"])
    API -.-> WORKER["{{L2_WORKER}}"]
    WORKER --> DB
    WORKER -->|"{{L2_EDGE_WORKER_VENDOR}}"| VENDOR(["{{L2_VENDOR}}"])
    classDef core fill:#2E74B5,stroke:#1F4D78,color:#ffffff,stroke-width:1px;
    classDef store fill:#EAF1FA,stroke:#1F4D78,color:#1F4D78,stroke-width:1px;
    classDef external fill:#F0E9FA,stroke:#6B4E9E,color:#4A356F,stroke-width:1px;
    classDef actor fill:#E3F5EA,stroke:#1E7A4B,color:#12613A,stroke-width:1px;
    class WEB,API,WORKER core;
    class DB,CACHE store;
    class IDP,VENDOR external;
    class USER actor;
```

| Container | Responsibility | Evidence |
|---|---|---|
{{#EACH containers}}
| **{{CONTAINER_NAME}}** | {{CONTAINER_RESP}} | `{{CONTAINER_EVIDENCE}}` |
{{/EACH}}

### 3.3 Components

```mermaid
%%{init: {'theme':'base','themeVariables':{'primaryColor':'#2E74B5','primaryTextColor':'#ffffff','primaryBorderColor':'#1F4D78','lineColor':'#1F4D78','secondaryColor':'#EAF1FA','tertiaryColor':'#EAF1FA','fontFamily':'Segoe UI, Inter, sans-serif','fontSize':'14px'}}}%%
flowchart LR
    ROUTER["{{L3_ROUTER}}"] --> MW["{{L3_MIDDLEWARE}}"] --> ORCH["{{L3_ORCHESTRATOR}}"]
    ORCH --> SVC1["{{L3_SERVICE_1}}"] & SVC2["{{L3_SERVICE_2}}"]
    SVC1 --> REPO["{{L3_REPOSITORY}}"]
    SVC2 --> CLIENT["{{L3_EXT_CLIENT}}"]
    MW --> AUTHZ["{{L3_AUTH}}"]
    classDef core fill:#2E74B5,stroke:#1F4D78,color:#ffffff,stroke-width:1px;
    classDef store fill:#EAF1FA,stroke:#1F4D78,color:#1F4D78,stroke-width:1px;
    classDef warn fill:#FEF3C7,stroke:#B45309,color:#92400E,stroke-width:1px;
    class ROUTER,MW,ORCH,SVC1,SVC2 core;
    class REPO,CLIENT store;
    class AUTHZ warn;
```

| Module | Responsibility | Key symbols | LOC |
|---|---|---|---:|
{{#EACH modules_tier1}}
| `{{MOD_PATH}}` | {{MOD_RESP}} | {{MOD_SYMBOLS}} | {{MOD_LOC}} |
{{/EACH}}

---

## 4. Runtime Views

```mermaid
%%{init: {'theme':'base','themeVariables':{'primaryColor':'#2E74B5','primaryTextColor':'#ffffff','primaryBorderColor':'#1F4D78','lineColor':'#1F4D78','tertiaryColor':'#EAF1FA','fontFamily':'Segoe UI, Inter, sans-serif','fontSize':'13px'}}}%%
sequenceDiagram
    autonumber
    actor U as {{SEQ_ACTOR}}
    participant FE as {{SEQ_FRONTEND}}
    participant API as {{SEQ_API}}
    participant SVC as {{SEQ_SERVICE}}
    participant DB as {{SEQ_DATABASE}}
    participant EXT as {{SEQ_EXTERNAL}}
    U->>FE: {{SEQ_STEP_1}}
    FE->>API: {{SEQ_STEP_2}}
    API->>SVC: {{SEQ_STEP_3}}
    SVC->>DB: {{SEQ_STEP_4}}
    DB-->>SVC: {{SEQ_STEP_5}}
    SVC->>EXT: {{SEQ_STEP_6}}
    EXT-->>SVC: {{SEQ_STEP_7}}
    SVC-->>API: {{SEQ_STEP_8}}
    API-->>FE: {{SEQ_STEP_9}}
```

```mermaid
%%{init: {'theme':'base','themeVariables':{'primaryColor':'#2E74B5','primaryTextColor':'#ffffff','primaryBorderColor':'#1F4D78','lineColor':'#1F4D78','tertiaryColor':'#EAF1FA','fontFamily':'Segoe UI, Inter, sans-serif'}}}%%
flowchart TD
    CALL["{{RES_OPERATION}}"] --> RESULT{"{{RES_OUTCOME}}"}
    RESULT -->|"{{RES_SUCCESS}}"| OK["{{RES_CONTINUE}}"]
    RESULT -->|"fail"| CLASSIFY{"{{RES_CLASSIFY}}"}
    CLASSIFY -->|"{{RES_TRANSIENT}}"| BACKOFF["{{RES_BACKOFF}}"] --> CALL
    CLASSIFY -->|"{{RES_PERMANENT}}"| FAIL["{{RES_FAIL_FAST}}"]
    CLASSIFY -->|"down"| DEGRADE["{{RES_DEGRADED_MODE}}"]
    classDef core fill:#2E74B5,stroke:#1F4D78,color:#ffffff,stroke-width:1px;
    classDef success fill:#E3F5EA,stroke:#1E7A4B,color:#12613A,stroke-width:1px;
    classDef warn fill:#FEF3C7,stroke:#B45309,color:#92400E,stroke-width:1px;
    classDef danger fill:#FDE8E8,stroke:#B91C1C,color:#B91C1C,stroke-width:1px;
    class CALL,BACKOFF core;
    class OK success;
    class DEGRADE warn;
    class FAIL danger;
```

{{FAILURE_NARRATIVE}} · Retry/Timeout/Breaker/Health: {{CTRL_STATUS}} (`{{CTRL_EVIDENCE}}`)

---

## 5. Security Architecture

```mermaid
%%{init: {'theme':'base','themeVariables':{'primaryColor':'#2E74B5','primaryTextColor':'#ffffff','primaryBorderColor':'#1F4D78','lineColor':'#1F4D78','tertiaryColor':'#EAF1FA','fontFamily':'Segoe UI, Inter, sans-serif'}}}%%
flowchart TB
    BROWSER(["{{SEC_CLIENT}}"]) --> PROXY["{{SEC_PROXY}}"] --> AUTHN["{{SEC_AUTHN_COMPONENT}}"]
    AUTHN -->|"{{SEC_EDGE_2}}"| APPSVC["{{SEC_APP}}"] --> AUTHZ["{{SEC_AUTHZ_COMPONENT}}"] --> DATA[("{{SEC_DATASTORE}}")]
    classDef danger fill:#FDE8E8,stroke:#B91C1C,color:#B91C1C,stroke-width:1px;
    classDef warn fill:#FEF3C7,stroke:#B45309,color:#92400E,stroke-width:1px;
    classDef core fill:#2E74B5,stroke:#1F4D78,color:#ffffff,stroke-width:1px;
    classDef store fill:#EAF1FA,stroke:#1F4D78,color:#1F4D78,stroke-width:1px;
    class BROWSER danger;
    class PROXY,AUTHN warn;
    class APPSVC,AUTHZ core;
    class DATA store;
```

{{BOUNDARY_NARRATIVE}}

| STRIDE | Target | Mitigation | Residual | Evidence |
|---|---|---|---|---|
| S/T/R/I/D/E | {{STRIDE_TARGET}} | {{STRIDE_MIT}} | {{STRIDE_RISK}} | `{{STRIDE_EV}}` |

| Secret | Storage | Injection | Evidence |
|---|---|---|---|
{{#EACH secrets}}
| `{{SECRET_NAME}}` | {{SECRET_STORAGE}} | {{SECRET_INJECTION}} | `{{SECRET_EVIDENCE}}` |
{{/EACH}}

| Cross-cutting | Authn/Authz/Validation/Errors/Logging/Config/Secrets — {{XC_SUMMARY}} · Gaps: {{XC_GAPS}} | `{{XC_EVIDENCE}}` |

---


