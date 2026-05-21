# DevSecOps Gating Flow - Visual Architecture

Visual diagrammatic view of the entire DevSecOps gating flow, mapping the interactions between the **Developer, Bitbucket Data Center, and Tekton in the Kubernetes cluster**.

## Architectural Sequence Flow

```
┌─────────────┐         ┌──────────────────────┐         ┌──────────────────────────────┐
│  Developer  │         │ Bitbucket Data Center│         │ Kubernetes Cluster (Tekton)  │
└──────┬──────┘         └──────────┬───────────┘         └──────────────┬───────────────┘
       │                           │                                     │
       │ 1. Push code &            │                                     │
       │    open PR                │                                     │
       ├──────────────────────────>│                                     │
       │                           │                                     │
       │                           │ 2. Evaluate Branch Permissions      │
       │                           │    (Detect "Require build status")  │
       │                           ├─────────────────────────┐           │
       │                           │ Lock [Merge] Button     │           │
       │                           │<────────────────────────┘           │
       │                           │                                     │
       │                           │ 3. Fire HTTP Webhook Payload        │
       │                           │    (Event: pr:opened + Commit ID)   │
       │                           ├────────────────────────────────────>│
       │                           │                                     │
       │                           │                                ┌────▼─────┐
       │                           │                                │EventList │
       │                           │                                │  ener    │
       │                           │                                └────┬─────┘
       │                           │                                     │
       │                           │                         ┌───────────▼─────────┐
       │                           │                         │ 4. Parse Payload    │
       │                           │                         │    via Interceptor  │
       │                           │                         │    Extract: Commit  │
       │                           │                         │    ID, Repo Slug    │
       │                           │                         └───────────┬─────────┘
       │                           │                                     │
       │                           │                         ┌───────────▼──────────┐
       │                           │                         │5. Instantiate        │
       │                           │                         │   PipelineRun        │
       │                           │                         └───────────┬──────────┘
       │                           │                                     │
       │                           │                         ┌───────────▼──────────────┐
       │                           │                         │ 6. Execute Tasks:        │
       │                           │                         │    a) git-clone          │
       │                           │                         │    b) security-scanner   │
       │                           │                         │    c) Report results     │
       │                           │                         └───────────┬──────────────┘
       │                           │                                     │
       │                           │ 7. POST Build Status API            │
       │                           │    (SUCCESSFUL or FAILED)           │
       │                           │<────────────────────────────────────┤
       │                           │                                     │
       │                           │ 8. Evaluate Build Status            │
       │                           ├─────────────────────────┐           │
       │                           │ If PASS: Unlock [Merge] │           │
       │                           │ If FAIL: Keep [Merge]   │           │
       │                           │         Blocked         │           │
       │                           │<────────────────────────┘           │
       │                           │                                     │
       │ 9. View Scan Results      │                                     │
       │    & Merge Status         │                                     │
       │<──────────────────────────┤                                     │
       │                           │                                     │

```

---

## Actor & Component Responsibilities

### 🧑‍💻 **The Developer**
- Triggers the entire CI/CD chain by:
  - Pushing new commits to a feature branch
  - Opening a Pull Request in Bitbucket UI
- Waits for security scan results before merge

### 🗄️ **Bitbucket Data Center**
Acts in dual capacity:

1. **Gatekeeper Role:**
   - Enforces Branch Permission rules
   - Blocks PR merge button until build status passes
   - Prevents unauthorized code merges

2. **Event Broadcaster Role:**
   - Sends HTTP webhook notifications to Tekton
   - Includes commit ID and PR metadata
   - Authenticates webhook calls with shared secrets

### 📡 **Tekton EventListener & Interceptors**
The front-door of your CI/CD cluster:
- Listens for incoming Bitbucket webhook events
- Validates traffic authenticity using shared secrets
- Extracts parameters (Commit ID, Repo Slug, Branch)
- Prevents unauthorized pipeline executions

### 🛠️ **Tekton PipelineRun (The Workers)**

| Task | Purpose | Behavior |
|------|---------|----------|
| **git-clone** | Fetch source code | Pulls exact temporary commit state from Bitbucket |
| **trivy-scanner** | Security scanning | Inspects dependencies, configurations, and code for vulnerabilities. Exits with code 1 on failure |
| **bitbucket-server-set-build-status** | Report results | Sends verdict back to Bitbucket REST API regardless of scan outcome |

---

## Complete Flow Walkthrough

| Step | Actor | Action | Result |
|------|-------|--------|--------|
| 1 | Developer | Push code / Open PR | PR created in Bitbucket |
| 2 | Bitbucket | Check branch rules | Merge button locked (status pending) |
| 3 | Bitbucket | Send webhook | EventListener receives payload |
| 4 | Tekton | Parse & validate | Extract commit ID, repo details |
| 5 | Tekton | Create PipelineRun | Security scan pipeline starts |
| 6a | Tekton | git-clone task | Source code downloaded |
| 6b | Tekton | security-scanner task | Vulnerability scan executed |
| 6c | Tekton | Report task | Results sent to Bitbucket API |
| 7 | Tekton | POST build status | Send PASS/FAIL to Bitbucket |
| 8 | Bitbucket | Evaluate status | Unlock merge (PASS) or keep blocked (FAIL) |
| 9 | Developer | Review results | Decide on merge or fix required |

---

## Key Security Gates

✅ **Webhook Validation** - Only authentic Bitbucket events trigger pipelines  
✅ **Automatic Scanning** - Code scanned before human merge decision  
✅ **Failed-Safe** - Merge blocked until security scan passes  
✅ **Audit Trail** - All scan results visible in Bitbucket PR  

---

## Notes

- The entire flow is **event-driven** and **automated**
- Scanning happens in **isolated Tekton cluster** (not Bitbucket)
- Build status **blocks merge** until scan completes
- Developers get **immediate feedback** on security issues
