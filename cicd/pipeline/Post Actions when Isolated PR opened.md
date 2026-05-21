# Post Actions when bot PR is Opened for Breaking Change

- When an isolated bot Pull Request (PR) is opened for a breaking change, it creates a sandboxed preview environment. It pauses further automation and alerts developers that human code refactoring is needed.

## Step-by-step across your tools when that bot PR goes live.
------------------------------
## 1. The Original Feature PR is Blocked
The pipeline run on the developer's original feature branch fails because it contains a vulnerability that cannot be fixed automatically.

* Bitbucket locks the Merge button on the developer's original PR.
* A comment or status update points the developer to the new, secondary Bot PR to fix the underlying issue.

------------------------------
## 2. A Dedicated Review PR is Born in Bitbucket
The Tekton bot pushes a new branch (e.g., security-fix/breaking-snakeyaml-to-2.0) and opens a new PR against your main branch.

* **The Code State**: This branch contains the exact breaking dependency upgrade (e.g., a major framework jump inside your pom.xml), but none of the source code fixes required to make it compile.
* **The PR Description**: The bot uses the Bitbucket API to post a clear, actionable description:
```
"⚠️ Automated Security Remediation Failed Validation
This PR was opened because upgrading snakeyaml to version 2.0 fixes a Critical CVE, but it broke your project's compilation or unit tests. Action Required: A developer must check out this branch locally, refactor the code to match the new version's API, and push the fixes."
```

------------------------------
## 3. The Interceptor Silences the CI Loop (Crucial Step)

- Because a new PR was opened, Bitbucket sends a standard webhook notification back to Tekton.
- To prevent your pipeline from getting stuck in an infinite loop of scanning, failing, and opening duplicate PRs, the Tekton EventListener uses a CEL Interceptor Filter.
- It catches the webhook and says: "This is a bot branch (security-fix/*). Do not run the auto-remediation workflow on it."
------------------------------
## 4. Human Refactoring Workflow
At this stage, the automation pauses and a developer steps in to fix the breaking changes:
```
[ Bot PR Opened ] ──> Developer checks out branch locally ──> Fixes broken APIs ──> Pushes code back to Bot branch
```

   1. **Local Checkout**: A developer checks out the bot's branch onto their local machine:
   
   ```
   git fetch origin
   git checkout security-fix/breaking-snakeyaml-to-2.0
   ```
   2. **Code Repair**: The developer runs mvn clean test-compile locally, sees exactly what broke (e.g., a method signature changed or a class was renamed in the new library version), and rewrites the Java code to fix it.
   3. **Pushing the Fix**: The developer commits and pushes the fixes directly back to that same bot branch.

------------------------------
## 5. Final Gate Clearance and Merge
When the developer pushes their manual code fixes to the bot branch, it triggers a clean, standard validation pipeline run.
```
[ Developer Pushes Code ] ──> Tekton runs full build & tests ──> Passes ──> Bitbucket unlocks Merge button
```

* **The Validation Run**: Tekton clones the branch, runs the Trivy scanner (which now finds 0 vulnerabilities), and runs mvn clean test.
* **The Pass Status**: Because the developer fixed the broken code, the compiler passes and the unit tests succeed. Tekton sends a SUCCESSFUL build status back to the Bitbucket API.
* **The Merge**: Bitbucket unlocks the Merge button on the Bot PR. The team reviews the refactored code changes, clicks merge, and the secure library along with the corrected code are safely merged into the main trunk.

------------------------------
## Summary of the Lifecycle
```
[ Bot PR Created ] ──> [ CI Loop Paused ] ──> [ Developer Refactors Code ] ──> [ Tests Pass ] ──> [ Merged to Main ]
```

