# Deployment & Operations Guide
### {{PROJECT_NAME}}

| Field | Value |
|---|---|
| **ID** / **Version** / **Status** | `{{PROJECT_SLUG}}-DEP-001` · `{{DOC_VERSION}}` · `{{DOC_STATUS}}` |
| **Owner** / **On-call** / **Nature** | `{{DOC_OWNER}}` · {{ONCALL}} · {{DOC_NATURE}} |
| **Source** | `{{REPO_URL}}` @ `{{COMMIT_SHA}}` |

## 1. Summary & Ground Truth

{{DEPLOYMENT_SUMMARY}} · Units {{UNIT_COUNT}} · Envs {{ENV_COUNT}} · Automation {{AUTOMATION_LEVEL}} · Deploy {{DEPLOY_DURATION}} · Rollback {{ROLLBACK_MECHANISM}} · Downtime {{DOWNTIME_REQUIRED}}

| Artifact | Present? | Found at |
|---|---|---|
| CI / CD | {{CI_PRESENT}} / {{CD_PRESENT}} | `{{CI_LOCATION}}` |
| Container / Orchestration / IaC | {{DOCKER_PRESENT}} / {{ORCHESTRATION_PRESENT}} / {{IAC_PRESENT}} | `{{DOCKER_LOCATION}}` |
| Env / Scripts / Monitoring | {{ENVFILE_PRESENT}} / {{SCRIPTS_PRESENT}} / {{MONITORING_PRESENT}} | `{{ENVFILE_LOCATION}}` |

> [!IMPORTANT]
> {{GROUND_TRUTH_STATEMENT}}

## 2. Environments, Prereqs & Local

| Property | Local | {{ENV_2_NAME}} | Production |
|---|---|---|---|
| Hosting / DB | {{LOCAL_HOSTING}} · {{LOCAL_DB}} | {{ENV_2_HOSTING}} · {{ENV_2_DB}} | {{PROD_HOSTING}} · {{PROD_DB}} |
| Deployed by / Approval | Developer / No | {{ENV_2_DEPLOYER}} / {{ENV_2_APPROVAL}} | {{PROD_DEPLOYER}} / {{PROD_APPROVAL}} |

| Tool | Version | Verify |
|---|---|---|
{{#EACH prerequisites}}
| {{PREREQ_TOOL}} | `{{PREREQ_VERSION}}` | `{{PREREQ_VERIFY}}` |
{{/EACH}}

> [!WARNING]
> {{PLATFORM_WARNING}}

```bash
git clone {{REPO_URL}} && cd {{REPO_DIR}}
{{SETUP_STEP_2}}
{{SETUP_STEP_3}}
cp {{ENV_TEMPLATE}} {{ENV_TARGET}}
```

| Component | Command | Port | Notes |
|---|---|---|---|
{{#EACH run_commands}}
| {{RUN_COMPONENT}} | `{{RUN_COMMAND}}` | `{{RUN_PORT}}` | {{RUN_NOTES}} |
{{/EACH}}

## 3. Configuration & Secrets

| Variable | Purpose | Req | Secret | Evidence |
|---|---|:--:|:--:|---|
{{#EACH env_vars}}
| `{{ENV_NAME}}` | {{ENV_PURPOSE}} | {{ENV_REQUIRED}} | {{ENV_SECRET}} | `{{ENV_EVIDENCE}}` |
{{/EACH}}

| Secret | Storage | Rotation | Evidence |
|---|---|---|---|
{{#EACH secrets_mgmt}}
| `{{SM_NAME}}` | {{SM_STORAGE}} | {{SM_FREQUENCY}} | `{{SM_EVIDENCE}}` |
{{/EACH}}

> Names only — never values. Drift: undocumented={{DRIFT_UNDOCUMENTED}} · insecure={{DRIFT_INSECURE}}

## 4. Topology

<!-- ANCHOR: dep-topology -->

```mermaid
%%{init: {'theme':'base','themeVariables':{'primaryColor':'#2E74B5','primaryTextColor':'#ffffff','primaryBorderColor':'#1F4D78','lineColor':'#1F4D78','secondaryColor':'#EAF1FA','tertiaryColor':'#EAF1FA','fontFamily':'Segoe UI, Inter, sans-serif','fontSize':'13px'}}}%%
flowchart TB
    INTERNET(["{{TOPO_CLIENT}}"])
    subgraph PERIMETER["Perimeter"]
        LB["{{TOPO_LOAD_BALANCER}}"]
        PROXY["{{TOPO_PROXY}}"]
    end
    subgraph APPZONE["App"]
        APP1["{{TOPO_APP_1}}"]
        WORKER["{{TOPO_WORKER}}"]
    end
    subgraph DATAZONE["Data"]
        PRIMARY[("{{TOPO_DB_PRIMARY}}")]
        CACHE[("{{TOPO_CACHE}}")]
    end
    subgraph EXTZONE["External"]
        SAAS1(["{{TOPO_EXTERNAL_1}}"])
    end
    INTERNET --> LB --> PROXY --> APP1
    APP1 --> PRIMARY
    APP1 --> CACHE
    WORKER --> PRIMARY
    APP1 -->|"{{TOPO_EDGE_EXT_1}}"| SAAS1
    classDef core fill:#2E74B5,stroke:#1F4D78,color:#ffffff,stroke-width:1px;
    classDef store fill:#EAF1FA,stroke:#1F4D78,color:#1F4D78,stroke-width:1px;
    classDef external fill:#F0E9FA,stroke:#6B4E9E,color:#4A356F,stroke-width:1px;
    classDef warn fill:#FEF3C7,stroke:#B45309,color:#92400E,stroke-width:1px;
    class APP1,WORKER core;
    class PRIMARY,CACHE store;
    class SAAS1 external;
    class LB,PROXY warn;
```

## 5. Build, Deploy & CI/CD

```bash
{{BUILD_COMMANDS}}
```

| # | Step | Action | Verify |
|---:|---|---|---|
{{#EACH deploy_steps}}
| {{DS_N}} | {{DS_STEP}} | `{{DS_COMMAND}}` | {{DS_VERIFY}} |
{{/EACH}}

```mermaid
%%{init: {'theme':'base','themeVariables':{'primaryColor':'#2E74B5','primaryTextColor':'#ffffff','primaryBorderColor':'#1F4D78','lineColor':'#1F4D78','tertiaryColor':'#EAF1FA','fontFamily':'Segoe UI, Inter, sans-serif'}}}%%
flowchart TD
    START(["{{DF_TRIGGER}}"]) --> PRECHECK{"{{DF_PRECHECK}}"}
    PRECHECK -->|"fail"| ABORT["{{DF_ABORT}}"]
    PRECHECK -->|"pass"| BUILD["{{DF_BUILD}}"]
    BUILD --> MIGRATE{"{{DF_MIGRATION_NEEDED}}"}
    MIGRATE -->|"yes"| RUNMIG["{{DF_RUN_MIGRATION}}"]
    MIGRATE -->|"no"| DEPLOY["{{DF_DEPLOY_APP}}"]
    RUNMIG --> DEPLOY
    DEPLOY --> SMOKE{"{{DF_SMOKE_TEST}}"}
    SMOKE -->|"pass"| DONE(["{{DF_COMPLETE}}"])
    SMOKE -->|"fail"| ROLLBACK["{{DF_ROLLBACK}}"]
    classDef core fill:#2E74B5,stroke:#1F4D78,color:#ffffff,stroke-width:1px;
    classDef success fill:#E3F5EA,stroke:#1E7A4B,color:#12613A,stroke-width:1px;
    classDef danger fill:#FDE8E8,stroke:#B91C1C,color:#B91C1C,stroke-width:1px;
    class BUILD,DEPLOY,RUNMIG core;
    class DONE success;
    class ABORT,ROLLBACK danger;
```

```mermaid
%%{init: {'theme':'base','themeVariables':{'primaryColor':'#2E74B5','primaryTextColor':'#ffffff','primaryBorderColor':'#1F4D78','lineColor':'#1F4D78','tertiaryColor':'#EAF1FA','fontFamily':'Segoe UI, Inter, sans-serif'}}}%%
flowchart LR
    COMMIT(["{{CI_TRIGGER}}"]) --> LINT["{{CI_STAGE_LINT}}"] --> UNIT["{{CI_STAGE_UNIT}}"] --> BUILD["{{CI_STAGE_BUILD}}"] --> PUBLISH["{{CI_STAGE_PUBLISH}}"]
    PUBLISH --> GATE{"{{CD_APPROVAL_GATE}}"}
    GATE -->|"yes"| DEPLOY_P["{{CD_STAGE_PROD}}"]
    GATE -->|"no"| HOLD["{{CD_HOLD}}"]
    classDef core fill:#2E74B5,stroke:#1F4D78,color:#ffffff,stroke-width:1px;
    classDef warn fill:#FEF3C7,stroke:#B45309,color:#92400E,stroke-width:1px;
    classDef proposed fill:#F5F7FA,stroke:#94A3B8,color:#475569,stroke-dasharray:4 3;
    class LINT,UNIT,BUILD,PUBLISH,DEPLOY_P core;
    class GATE,HOLD warn;
```

| Stage | Exists | Tool | Evidence |
|---|:--:|---|---|
{{#EACH pipeline_stages}}
| {{PS_STAGE}} | {{PS_EXISTS}} | {{PS_TOOL}} | `{{PS_EVIDENCE}}` |
{{/EACH}}

```mermaid
%%{init: {'theme':'base','themeVariables':{'primaryColor':'#2E74B5','primaryTextColor':'#ffffff','primaryBorderColor':'#1F4D78','lineColor':'#1F4D78','fontFamily':'Segoe UI, Inter, sans-serif'}}}%%
gitGraph
    commit id: "{{GIT_C1}}"
    branch {{GIT_BRANCH_1}}
    commit id: "{{GIT_C2}}"
    checkout main
    merge {{GIT_BRANCH_1}} id: "{{GIT_MERGE_1}}"
    commit id: "{{GIT_C3}}" tag: "{{GIT_TAG_1}}"
```

**Release.** {{RELEASE_STRATEGY}} (`{{STRATEGY_EVIDENCE}}`)

## 6. Rollback

<!-- ANCHOR: dep-rollback -->

```mermaid
%%{init: {'theme':'base','themeVariables':{'primaryColor':'#2E74B5','primaryTextColor':'#ffffff','primaryBorderColor':'#1F4D78','lineColor':'#1F4D78','tertiaryColor':'#EAF1FA','fontFamily':'Segoe UI, Inter, sans-serif'}}}%%
flowchart TD
    ALERT["{{RB_TRIGGER}}"] --> SEVERITY{"{{RB_SEVERITY}}"}
    SEVERITY -->|"{{RB_SEV_CRITICAL}}"| IMMEDIATE["{{RB_IMMEDIATE}}"]
    SEVERITY -->|"{{RB_SEV_DEGRADED}}"| ASSESS{"{{RB_ASSESS}}"}
    SEVERITY -->|"{{RB_SEV_MINOR}}"| FORWARD["{{RB_FIX_FORWARD}}"]
    ASSESS -->|"no mitigation"| IMMEDIATE
    IMMEDIATE --> DBCHECK{"{{RB_DB_CHANGED}}"}
    DBCHECK -->|"no"| APPROLL["{{RB_APP_ROLLBACK}}"]
    DBCHECK -->|"yes"| RESTORE["{{RB_DB_RESTORE}}"]
    APPROLL --> STABLE(["{{RB_STABLE}}"])
    RESTORE --> STABLE
    FORWARD --> STABLE
    classDef core fill:#2E74B5,stroke:#1F4D78,color:#ffffff,stroke-width:1px;
    classDef success fill:#E3F5EA,stroke:#1E7A4B,color:#12613A,stroke-width:1px;
    classDef danger fill:#FDE8E8,stroke:#B91C1C,color:#B91C1C,stroke-width:1px;
    classDef warn fill:#FEF3C7,stroke:#B45309,color:#92400E,stroke-width:1px;
    class APPROLL,FORWARD core;
    class STABLE success;
    class IMMEDIATE,RESTORE danger;
    class ALERT warn;
```

| # | Step | Command | Data-loss risk |
|---:|---|---|---|
{{#EACH rollback_steps}}
| {{RS_N}} | {{RS_STEP}} | `{{RS_COMMAND}}` | {{RS_DATA_RISK}} |
{{/EACH}}

## 7. Observability, Backup, Readiness & Gaps

| Signal / Asset | Tool / Method | Gap / Freq | Evidence |
|---|---|---|---|
{{#EACH monitoring}}
| {{MON_SIGNAL}} | {{MON_TOOL}} | {{MON_GAP}} | `{{MON_EVIDENCE}}` |
{{/EACH}}
{{#EACH backups}}
| {{BK_ASSET}} | {{BK_METHOD}} | {{BK_FREQUENCY}} · tested={{BK_TESTED}} | `{{BK_EVIDENCE}}` |
{{/EACH}}

| # | Gate | Status | Blocking? | TODO |
|---|---|:--:|:--:|---|
{{#EACH readiness_gates}}
| G-{{INDEX}} | {{GATE_CRITERION}} | {{GATE_STATUS}} | {{GATE_BLOCKING}} | {{GATE_TODO}} |
{{/EACH}}

**Verdict.** {{READINESS_VERDICT}}

| ID / Gap | Detail | Impact |
|---|---|---|
{{#EACH ops_assumptions}}
| `{{ASSUMPTION_ID}}` | {{ASSUMPTION_TEXT}} | {{ASSUMPTION_IMPACT}} · § {{ASSUMPTION_SECTION}} |
{{/EACH}}
{{#EACH ops_gaps}}
| GAP | {{GAP_ITEM}} · `{{GAP_SEARCH}}` | {{GAP_CONSEQUENCE}} |
{{/EACH}}

<!-- ANCHOR: dep-end -->
*End of `{{PROJECT_SLUG}}-DEP-001` → *`Review and TODO.md`*.*
