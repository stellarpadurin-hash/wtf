Here is the visual diagrammatic view of the entire DevSecOps gating flow, mapping the interactions between the Developer, Bitbucket Data Center, and Tekton in your Kubernetes cluster.
## Architectural Sequence Flow

[ Developer ]        [ Bitbucket Data Center ]              [ Kubernetes Cluster (Tekton) ]
     │                           │                                         │
     │ 1. Pushes code &          │                                         │
     │    opens Pull Request     │                                         │
     ────────────────────────────>                                         │
     │                           │                                         │
     │                           │ 2. Evaluates Branch Permissions         │
     │                           │    (Detects "Require build status")     │
     │                           │──┐                                      │
     │                           │  │ Locks [Merge] Button                 │
     │                           │<─┘                                      │
     │                           │                                         │
     │                           │ 3. Fires HTTP Webhook Payload           │
     │                           │    (Event: pr:opened + Commit ID)       │
     │                           ──────────────────────────────────────────> [ EventListener ]
     │                           │                                                │
     │                           │                                                │ 4. Parses Payload via Interceptor
     │                           │                                                │──┐ & Extracts Parameters
     │                           │                                                │  │ (Commit ID, Repo Slug)
     │                           │                                                │<─┘
     │                           │                                                │
     │                           │                                                │ 5. Instantiates
     │                           │                                                │────────────────> [ PipelineRun ]
     │                           │                                                                         │
     │                           │                                                                         │ 6. Executes Tasks:
     │                           │                                                                         │ a) git-clone
     │                           │                                                                         │ b) trivy-scanner
     │                           │                                                                         │──┐
     │                           │                                                                         │  │ Scans code for
     │                           │                                                                         │  │ Vulnerabilities
     │                           │                                                                         │<─┘
     │                           │                                                                         │
     │                           │ 7. Posts Build Status API Call                                          │
     │                           │    (Status: SUCCESSFUL or FAILED)                                       │
     │                           <─────────────────────────────────────────────────────────────────────────│ (Finally Block)
     │                           │
     │                           │ 8. Evaluates Build Status
     │                           │──┐
     │                           │  │ If SUCCESSFUL -> Unlocks [Merge]
     │                           │  │ If FAILED     -> Keeps [Merge] Blocked
     │                           │<─┘
     │                           │
     │ 9. Sees Scan Results      │
     │    & Merge Status         │
     <───────────────────────────│

------------------------------
## Actor & Component Responsibilities
To make the architecture clear, here is what each specific component does during the process:

* 🧑‍💻 The Developer: Triggers the entire chain by pushing new commits to a feature branch or opening a Pull Request in the UI.
* 🗄️ Bitbucket Data Center:
* Acts as the Gatekeeper. Its Branch Permission rules physically hold the PR open and block human intervention.
   * Acts as the Event Broadcaster by notifying Tekton via webhooks that new code is ready to be inspected.
* 📡 Tekton EventListener & Interceptors: The front door of your CI/CD cluster. It listens for Bitbucket's call, validates that the traffic is authentic using a shared secret, and extracts data like commit-id.
* 🛠️ Tekton PipelineRun (The Workers):
* git-clone: Pulls down the exact temporary commit state from Bitbucket.
   * trivy-scanner: Inspects dependencies, configurations, and code for critical security flaws. If it catches a flaw, it intentionally crashes itself with exit code 1.
   * bitbucket-server-set-build-status: The messenger. No matter if the scanner passes or crashes, this final step takes the verdict and sends it back to Bitbucket's REST API.

Would you like to drill down into the Kubernetes role-based access control (RBAC) needed to let these Tekton actors communicate securely?

