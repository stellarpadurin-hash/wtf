# Visual Architecture of Auto-Remediation Pipeline
- Here is the comprehensive visual architecture of the auto-remediation pipeline.
- This diagram maps exactly how Tekton analyzes vulnerabilities (whether they are isolated JARs or complex Parent POM frameworks), attempts an automated fix, and evaluates the codebase via the Verification Compilation Step before deciding the next engineering action.
  
## Automated Remediation & Verification Sequence

    [ Tekton Pipeline Step: Maven Auto-Remediation ]
                          │
                          ▼
             ┌─────────────────────────┐
             │ Run Trivy File Scan     │
             └─────────────────────────┘
                          │
                          ▼
               / Vulnerabilities \
              <   Discovered?     >
               \─────────────────/
                  /           \
               NO /             \ YES
                 ▼               ▼
         [ Proceed Build ]   [ Track Root Cause Package ]
                                         │
                                         ▼
                             / Is it a Parent POM \
                            <   or Core Framework  >
                             \────────────────────/
                                /              \
                            YES /              \ NO
                               ▼                ▼
                     ┌────────────────┐   ┌───────────────────────┐
                     │ Run:           │   │ Run:                  │
                     │ mvn versions:  │   │ mvn versions:         │
                     │ update-parent  │   │ use-dependency-version│
                     └────────────────┘   └───────────────────────┘
                                \              /
                                 \            /
                                  ▼          ▼
                       ┌────────────────────────────┐
                       │ Git Stash & Apply Upgrade  │
                       └────────────────────────────┘
                                      │
                                      ▼
                        ============================
                        VERIFICATION COMPILATION STEP
                        ============================
                        │ Run: mvn clean test      │
                        ============================
                                      │
                                      ▼
                           / Did Maven Compile \
                          <   & Tests Pass?     >
                           \───────────────────/
                              /             \
                          YES /               \ NO (API Broken / Test Failed)
                             ▼                 ▼
                     ┌──────────────┐   ┌──────────────────────────────┐
                     │ Commit Fix & │   │ Run: git reset --hard        │
                     │ Continue     │   │ (Wipe bad pom.xml changes)   │
                     │ Deployment   │   └──────────────────────────────┘
                     └──────────────┘                  │
                                                       ▼
                                        ┌──────────────────────────────┐
                                        │ git checkout -b security-fix │
                                        │ Re-apply upgrade to branch   │
                                        └──────────────────────────────┘
                                                       │
                                                       ▼
                                        ┌──────────────────────────────┐
                                        │ git push & open Bitbucket    │
                                        │ Pull Request for Human Review│
                                        └──────────────────────────────┘
                                                       │
                                                       ▼
                                        [ Terminate Current Pipeline ]

------------------------------
## Understanding the Visual Decision Points

   1. **The Scanner Branching**: The script doesn't just read vulnerability names; it evaluates the metadata. If a vulnerability is widespread because your corporate template or framework parent (like spring-boot-starter-parent) is from three years ago, it uses specialized Maven parent tools rather than generic dependency overrides.
   2. **The "Sandboxed" Upgrade Execution**: When the upgrade is made, the workspace is temporarily mutated. It is critical that this modification stays in a detached state until the validation process gives it a green light.
   3. **The Sandbox Verdict**:
   * **Success Path**: If mvn clean test exits safely with code 0, Tekton treats the upgrade as an invisible, self-healing background action. The developer's feature branch builds seamlessly using the fresh, secure code.
   * **Failure Path**: If a method signature was deprecated or deleted in the new version, the unit tests or compiler will instantly throw an error. The bot cleanly undoes all local file edits (git reset --hard) so it doesn't pollute the user's workspace, clones a separate safety branch, pushes the breaking upgrade there, and leaves an explicit warning trail on Bitbucket for the engineers to refactor manually.
   


