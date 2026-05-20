# Post Actions for PR raised for breaking security fix

- When a Pull Request (PR) is raised for a breaking security fix, the Tekton bot intentionally halts the current build path to prevent unsafe code from moving forward, while simultaneously creating a isolated sandbox environment for review.
- Here is exactly how the system reacts, step-by-step, to handle a breaking version upgrade safely without risking production stability.
------------------------------
## 1. The Original Feature Branch Pipeline is Blocked
When the remediation script realizes a fix requires a major version upgrade (e.g., upgrading framework v2.x to v3.x), it executes two critical safety steps:

* Fails the Current Build: The Tekton task exits with code 1.
* Locks the Original PR: This failure sends a FAILED status back to Bitbucket Data Center [1]. Because of your branch permissions, the developer's original PR cannot be merged with the vulnerable dependencies intact [1].

------------------------------
## 2. A Dedicated "Security-Fix" PR is Born
The bot isolated the dangerous dependency change by branching off your target branch (e.g., main), applying the forced upgrade (npm install framework@3.0.0), and creating a brand new PR inside Bitbucket:

* Source Branch: security-fix/framework-to-3.0.0
* Target Branch: main (or your development trunk)

------------------------------
## 3. The Interceptor Filter Directs Traffic (Loop Prevention)
To prevent your automation from getting stuck in an infinite loop, your Tekton EventListener must use an interceptor filter. It intercepts the webhook from this new bot PR and treats it differently than a human PR.

# Add this CEL filter to your EventListener to control the breaking-fix PR loopinterceptors:
  - ref:
      name: "cel"
    params:
      - name: "filter"
        # ONLY trigger full testing builds if the PR did NOT come from the security bot
        value: "!body.pullRequest.fromRef.id.matches('refs/heads/security-fix/.*')"

------------------------------
## 4. The Human Review Workflow Takes Over
At this stage, automation stops, and human engineering takes over. Because it is a breaking change, a developer must manually intervene to fix broken code patterns.
```
[ Security-Fix PR Opened ] 
            │
            ▼
┌──────────────────────────────────────┐
│  Developer Clones Bot Branch Locally │
└──────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────┐
│ Rewrites Code to Match New API Spec  │
└──────────────────────────────────────┘
            │
            ▼
┌──────────────────────────────────────┐
│   Pushes Code Back to Bot Branch     │
└──────────────────────────────────────┘
            │
            ▼
[ Tekton Re-Scans & Pass Status Sent ] ───> [ PR Unlocked & Merged Manually ]
```

   1. The Developer Reviews the Bot PR: The developer inspects the automated PR in Bitbucket to see exactly which framework version was forced.
   2. Local Code Correction: The developer pulls down the bot's branch (security-fix/framework-to-3.0.0) onto their local machine. They fix any syntax changes, deprecated methods, or broken integration configurations caused by the major version leap.
   3. Pushing the Remediation: The developer pushes their refactored, updated code back to that same bot branch.
   4. Final Tekton Gate Validation: This new push triggers a traditional, clean Tekton test pipeline. If the security scanner sees 0 vulnerabilities, and the unit tests pass, Tekton sends a SUCCESSFUL status back to Bitbucket [1].
   5. The Safe Merge: The team safely clicks Merge on the breaking-fix PR, updating the foundation of the repository.

## Summary of State
```

| Action Item | Non-Breaking Fix | Breaking Fix |
|---|---|---|
| Pipeline Action | Patch applied in-place during build. | Build aborted; new branch pushed. |
| Bitbucket Status | Marks PR as PASSED [1]. | Marks original PR as FAILED [1]. |
| Human Effort | Zero. Merges automatically. | Required. Must refactor code changes. |

