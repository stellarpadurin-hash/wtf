# Inject a Verification Compilation Step

- To ensure that an automated upgrade—wheher it's a minor JAR update or a complex Parent POM shift—doesn't break the application, we must inject a Verification Compilation Step right after the modification runs, but before we make the final decision to commit or open a Pull Request.
- If the project compiles and its unit tests pass, the upgrade is classified as Non-Breaking and the pipeline proceeds. If compilation or testing fails, the code changes are rolled back, and the pipeline falls back to Path B (The Breaking PR path) so a human can fix the breaking changes.
------------------------------
## The Verification Framework Logic
Here is how the automated validation flow behaves inside the container:

```
[ Apply Auto-Upgrade ]
          │
          ▼
[ Run: mvn clean test-compile ]
          │
          ├──> SUCCESSFUL? ──> Run Unit Tests ──> PASSED? ──> [ Merge / Continue Build ]
          │                                         │
          └──> NO ──────────────────────────────────┴───────> [ Rollback & Open Breaking PR ]
```
------------------------------
## Upgraded Tekton Task with Automated Verification
- This full, end-to-end shell execution script integrates directly into the Tekton Task's execution block.
- It tracks the outcome of **mvn clean test** to determine if the upgrade is safe.

```
#!/bin/sh# Fail the shell script if unexpected errors happen, but handle maven outcomes manuallyset -e
apk add --no-cache git curl jq

echo "🔍 Step 1: Scanning for vulnerabilities..."
curl -sfL https://githubusercontent.com | sh -s -- -b /usr/local/bin
trivy fs --format json --output trivy-results.json .

FLAWED_JAR=$(jq -r '.Results[0].Vulnerabilities[0].PkgName' trivy-results.json)
FIXED_VERSION=$(jq -r '.Results[0].Vulnerabilities[0].FixedVersion' trivy-results.json)
if [ "$FLAWED_JAR" = "null" ] || [ -z "$FLAWED_JAR" ]; then
  echo "✅ Codebase is clean. Moving to compilation phase."
  exit 0fi

echo "⚠️ Vulnerability found in: $FLAWED_JAR. Attempting upgrade to $FIXED_VERSION..."
# Stash current git state so we can easily roll back if verification fails
git stash clear || true
git add pom.xml
git stash
# Apply the version upgrade (Works for properties or dependencyManagement)
git stash pop
mvn versions:set-dependency-version -Ddependency="$FLAWED_JAR" -DnewVersion="$FIXED_VERSION"
# -----------------------------------------------------------------# STEP 2: VERIFICATION BUILD (The Safety Net)# -----------------------------------------------------------------
echo "🧪 Running verification compilation and testing suite..."
# We disable strict bash failure (-e) temporarily to safely evaluate Maven's exit codeset +e
mvn clean test -DfailIfNoTests=false
MAVEN_EXIT_CODE=$?set -e
# -----------------------------------------------------------------# EVALUATION LAYER# -----------------------------------------------------------------if [ $MAVEN_EXIT_CODE -eq 0 ]; then
  # ---------------------------------------------------------------
  # PATH A: The upgrade compiled cleanly and tests passed!
  # ---------------------------------------------------------------
  echo "✅ Verification successful! Upgrade to $FIXED_VERSION is non-breaking."
  echo "Proceeding with the primary deployment pipeline steps..."
  exit 0
else
  # ---------------------------------------------------------------
  # PATH B: The upgrade broke compilation or failed a test case!
  # ---------------------------------------------------------------
  echo "🚨 Verification FAILED. The upgrade introduces breaking changes or API incompatibilities."
  echo "Rolling back workspace changes and routing to the Human Review path..."

  # Wipe away the broken pom.xml modifications and reset back to original branch state
  git reset --hard HEAD
  git clean -fd

  BRANCH_NAME="security-fix/breaking-${FLAWED_JAR##*:}-to-${FIXED_VERSION}"
  
  git config --global user.email "tekton-bot@yourcompany.com"
  git config --global user.name "Tekton Java-Remediation Bot"
  git checkout -b "$BRANCH_NAME"

  echo "Applying breaking upgrade back onto isolated review branch..."
  mvn versions:set-dependency-version -Ddependency="$FLAWED_JAR" -DnewVersion="$FIXED_VERSION"
  
  git add pom.xml
  git commit -m "security(deps): breaking dependency change requiring refactoring ($FLAWED_JAR -> $FIXED_VERSION)"

  PUSH_URL=$(echo "$(params.repo-url)" | sed "s|https://|https://x-token-auth:${BITBUCKET_TOKEN}@|")
  git push "$PUSH_URL" "$BRANCH_NAME" --force

  echo "Opening a Breaking-Change Pull Request against $(params.target-branch)..."
  curl -X POST -H "Authorization: Bearer ${BITBUCKET_TOKEN}" \
       -H "Content-Type: application/json" \
       -d "{
         \"title\": \"⚠️ Breaking Security Fix: Upgrade ${FLAWED_JAR##*:}\",
         \"description\": \"Automated upgrade failed compilation or unit tests. A developer must pull down this branch, refactor the code to fix compile issues, and merge manually.\",
         \"fromRef\": {\"id\": \"refs/heads/${BRANCH_NAME}\"},
         \"toRef\": {\"id\": \"refs/heads/$(params.target-branch)\"}
       }" \
       "https://yourcompany.com"

  # Explicitly fail the task to block the current flawed master build from advancing
  exit 1fi
```
------------------------------
## Production Tuning Checklist
To optimize this compilation step inside an enterprise environment, we need to ensure to apply these configurations:

* **Cache the .m2 Repository**: Maven downloads internet dependencies from scratch on every run. You must attach a Persistent Volume Claim (PVC) to your Tekton Task workspace mapping to /root/.m2 or /home/user/.m2 [1]. This reduces your compile validation times from minutes to seconds.
* **Isolate Test Databases**: If the unit or integration tests require a live database connection (e.g., PostgreSQL/MySQL), we can use a Tekton Sidecar Container to spin up an ephemeral database container alongside your Maven validation execution step.
* **Skip Heavy Integration Tests (Optional)**: If the full integration test suite takes over an hour, we might want to only run surface compilation checks. We can adjust the verification command to **mvn clean test-compile** to only catch syntax/API breakage while skipping heavy test execution blocks.



