# Pipeline Trigger from Different Scenarios
- To build a comprehensive enterprise security model, you should actually trigger this pipeline in all three scenarios, but configure each trigger to behave slightly differently based on its context.
- Running the auto-remediation step at different points in the lifecycle creates a layered defense, catching vulnerabilities early in development and continuously monitoring older code.
  
The below is the  structure and configure of each trigger option.
------------------------------
## Trigger Strategy Matrix

| Scenario | Trigger Type | Ideal Action | Loop Prevention Rule |
|---|---|---|---|
| 1. PR to Main Branch | Webhook | Non-breaking: Apply in-place. Breaking: Fail build, reject merge, open isolated bot PR. | Mandatory. Must ignore branches matching security-fix/*. |
| 2. Active Build Request | Manual / CI Hook | Non-breaking: Apply in-place to ensure secure artifact. Breaking: Fail build instantly. | Not required (ephemeral runner). |
| 3. Scheduled Nightly Review | Cron Timer | Non-breaking: Commit directly to main. Breaking: Open isolated bot PR. | Not required (scans static list). |

------------------------------
## Scenario 1: Whenever a Pull Request is Raised (The Shift-Left Gate)
This is the most critical trigger. It acts as a gatekeeper, preventing new vulnerabilities from being merged into your production code.

* **How it works**: Bitbucket Data Center fires a webhook (pr:opened or pr:from_ref_updated) to your Tekton EventListener.
* **The Workflow**: The pipeline scans the developer's incoming feature branch code. If a non-breaking fix is found, it heals the code automatically in-place, allowing the build to pass. If a breaking fix is found, it intentionally fails the build to block the merge and spins off a dedicated security-fix/* branch for the developer to fix.
* **Crucial Rule (Loop Prevention)**: You must configure your Tekton Interceptor to ignore pushes or PRs coming from the bot's own prefix:

# Drop this filter inside your EventListener to prevent infinite loops
```
- ref:
    name: "cel"
  params:
    - name: "filter"
      value: "!body.pullRequest.fromRef.id.matches('refs/heads/security-fix/.*')"

```
------------------------------
## Scenario 2: Whenever a Request for a New Build is Made (The Artifact Guard)
This trigger fires during traditional manual or automated CI builds (e.g., when packaging a release, deploying to testing environments, or when an engineer clicks "Run Pipeline").

* **How it works**: It runs as an inline, mandatory early step inside your standard build blueprint.
* **The Workflow**: It ensures that your final compiled artifact (like a Docker image or a production .jar file) is always patched against the latest vulnerabilities, even if those flaws were discovered after the PR was merged.
* **Behavior on Failur**e: If a vulnerability requires a breaking change at this stage, the pipeline must fail immediately and halt the deployment. You do not want the bot to open a new PR during a live production release path, as that would delay the deployment and require immediate human intervention to resolve.

------------------------------
## Scenario 3: On a Schedule (The Continuous Monitor)
Code that sat securely in your repository yesterday can become vulnerable today when a new Zero-Day vulnerability or CVE is published. A scheduled trigger ensures your entire repository catalog remains secure over time.

* **How it work**s: You deploy a Kubernetes Tekton CronTrigger / Trigger CRD or an external cron utility to fire a request every night at midnight.
* **The Workflow**: The script loops through your core repository list, checks out the main branch, and runs the Trivy scanner.
* **Behavior on Failure**:
* If it finds a non-breaking change, the bot applies it and pushes it directly back to main (or raises a clean, pre-approved PR that auto-merges after passing validation).
   * If it finds a breaking change, it opens a **security-fix/* PR** against main and posts a message to your team's chat room (e.g., Slack or Microsoft Teams) alerting them that a major library upgrade requires manual refactoring.

------------------------------
## Recommendation for Best Results
If we are setting this up for the first time, we can **start with Scenario 1 (The PR Trigger)**. It provides immediate value by catching flaws before they are merged and teaches the  development team how the automated remediation sandbox behaves.** Once that workflow is stable, we can implement Scenario 3** (The Scheduled Nightly Scan) to clean up older, inactive codebases automatically.

