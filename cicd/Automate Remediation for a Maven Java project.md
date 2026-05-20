# Automate remediation for a Maven/Java project
- To automate remediation for a Maven/Java project, you cannot use npm-style commands. Instead, you must use the native mvn versions-maven-plugin alongside a vulnerability scanner (like Trivy or OWASP Dependency-Check) that can export flaws in a machine-readable JSON format.
- Here is how to structure the pipeline logic, the custom Tekton Task, and the specialized Maven configuration.
------------------------------
## Step 1: Add the Versions Plugin to your pom.xml

To allow the Tekton bot to safely query and modify dependency versions without breaking your build, ensure the versions-maven-plugin is declared in your project's pom.xml:
```
<build>
    <plugins>
        <plugin>
            <groupId>org.codehaus.mojo</groupId>
            <artifactId>versions-maven-plugin</artifactId>
            <version>2.18.0</version> <!-- Use the latest stable version -->
        </plugin>
    </plugins>
</build>
```
------------------------------
## Step 2: The Maven Auto-Remediation Tekton Task
This custom Tekton Task executes a two-phase process:

   1. Safe/Non-Breaking Upgrades: It uses versions:use-next-releases restricting updates to incremental patches (e.g., bugfixes/minor updates within SemVer). If that resolves the issue, it commits the changes and continues the build.
   2. Breaking Upgrades: If a critical flaw remains that requires a Major upgrade (e.g., migrating from Spring Boot 2.x to 3.x), it creates an isolated branch, forces the upgrade via versions:set-dependency-version, and submits a Bitbucket Pull Request.
```
apiVersion: tekton.dev/v1beta1
kind: Task
metadata:
  name: maven-auto-remediatespec:
  workspaces:
    - name: source-dir
  params:
    - name: repo-url
      type: string
    - name: target-branch
      type: string
  steps:
    - name: analyze-and-remediate-java
      image: maven:3.9-eclipse-temurin-17-alpine
      workingDir: $(workspaces.source-dir.path)
      env:
        - name: BITBUCKET_TOKEN
          valueFrom:
            secretKeyRef:
              name: bitbucket-creds
              key: token
      script: |
        #!/bin/sh
        apk add --no-cache git curl jq

        echo "🔍 Step 1: Running vulnerability scan on Java dependencies..."
        # Runs Trivy scanner to look specifically for flawed pom.xml dependencies
        # (Assuming trivy is pre-installed or downloaded into the container)
        curl -sfL https://githubusercontent.com | sh -s -- -b /usr/local/bin
        trivy fs --format json --output trivy-results.json .

        # Parse the JSON to see if vulnerabilities exist
        VULN_COUNT=$(jq '.Results[0].Vulnerabilities | length' trivy-results.json)
        if [ "$VULN_COUNT" -eq 0 ] || [ "$VULN_COUNT" = "null" ]; then
          echo "✅ No vulnerabilities found. Proceeding with build."
          exit 0
        fi

        echo "⚠️ Found $VULN_COUNT vulnerabilities. Attempting safe, non-breaking remediation..."

        # Extract the package name and fixed version from Trivy results
        # This extracts the first high/critical vulnerability for demonstration
        FLAWED_JAR=$(jq -r '.Results[0].Vulnerabilities[0].PkgName' trivy-results.json)
        FIXED_VERSION=$(jq -r '.Results[0].Vulnerabilities[0].FixedVersion' trivy-results.json)
        CURRENT_VERSION=$(jq -r '.Results[0].Vulnerabilities[0].InstalledVersion' trivy-results.json)

        # Extract major versions to check for breaking changes
        CURRENT_MAJOR=$(echo "$CURRENT_VERSION" | cut -d. -f1)
        FIXED_MAJOR=$(echo "$FIXED_VERSION" | cut -d. -f1)

        # ----------------------------------------------------
        # PATH A: NON-BREAKING REMEDIATION (Same Major Version)
        # ----------------------------------------------------
        if [ "$CURRENT_MAJOR" = "$FIXED_MAJOR" ] && [ "$FIXED_VERSION" != "null" ]; then
          echo "🔄 Safe patch available. Upgrading $FLAWED_JAR to $FIXED_VERSION..."
          
          # Match Maven coordinates (GroupId:ArtifactId) and update version in pom.xml
          # Trivy returns PkgName as 'groupId:artifactId' natively for Java
          mvn versions:set-dependency-version \
            -Ddependency="$FLAWED_JAR" \
            -DnewVersion="$FIXED_VERSION"

          echo "✅ Clean update applied. Continuing the deployment pipeline..."
          exit 0
        fi

        # ----------------------------------------------------
        # PATH B: BREAKING REMEDIATION (Major Version Upgrade Required)
        # ----------------------------------------------------
        echo "🚨 Upgrade requires a major/breaking change ($CURRENT_VERSION -> $FIXED_VERSION)."
        echo "Creating an isolated branch and opening a Bitbucket PR..."

        BRANCH_NAME="security-fix/maven-${FLAWED_JAR##*:}-to-${FIXED_VERSION}"
        
        # Git config setup inside container
        git config --global user.email "tekton-bot@yourcompany.com"
        git config --global user.name "Tekton Java-Remediation Bot"
        
        git checkout -b "$BRANCH_NAME"

        # Force the major breaking change into the pom.xml file
        mvn versions:set-dependency-version \
          -Ddependency="$FLAWED_JAR" \
          -DnewVersion="$FIXED_VERSION"

        git add pom.xml
        git commit -m "security(deps): auto-remediate breaking vulnerability in $FLAWED_JAR"

        # Push branch securely using tokens
        PUSH_URL=$(echo "$(params.repo-url)" | sed "s|https://|https://x-token-auth:${BITBUCKET_TOKEN}@|")
        git push "$PUSH_URL" "$BRANCH_NAME" --force

        # Fire API request to Bitbucket Data Center to open the Pull Request
        curl -X POST -H "Authorization: Bearer ${BITBUCKET_TOKEN}" \
             -H "Content-Type: application/json" \
             -d "{
               \"title\": \"Security Patch (Java): Upgrade ${FLAWED_JAR} to ${FIXED_VERSION}\",
               \"description\": \"Automated breaking dependency change raised by Tekton.\",
               \"fromRef\": {\"id\": \"refs/heads/${BRANCH_NAME}\"},
               \"toRef\": {\"id\": \"refs/heads/$(params.target-branch)\"}
             }" \
             "https://yourcompany.com"

        # Explicitly crash this task execution path to block the unsafe codebase build
        echo "🛑 Pipeline halted. Human review required for breaking changes on PR."
        exit 1
```
------------------------------
## Step 3: Best Practice Rules for Maven Automation
When writing Java automation code, keep these rules in mind to avoid corrupted builds:

   1. Manage Parent POMs Carefully: If your dependencies are controlled inside a parent multi-module architecture, run the Maven execution command from the root folder containing your parent pom.xml. The plugin will automatically cascade version updates down to sub-modules.
   2. Utilize Maven Properties: If your versions are managed via properties blocks (e.g., <spring.version>2.7.1</spring.version>), use the specialized mvn versions:update-property -Dproperty=spring.version -DnewVersion=3.0.0 goal instead of set-dependency-version. This keeps your project configuration organized.
   3. Run a Verification Compilation: After patching a "non-breaking" change, consider adding an immediate mvn clean test-compile step within the same task. If the compile fails due to hidden API changes, catch the error, roll back, and force it down Path B (The Breaking PR path) instead.


