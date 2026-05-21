When using Checkmarx Software Composition Analysis (SCA), deciding which version upgrade to apply is managed by the Checkmarx intelligence engine. Checkmarx mathematically determines a target version that resolves multiple CVEs affecting a package simultaneously while minimizing the upgrade path. [1] 
To automate this decision inside your Tekton pipeline, you extract the calculated remediation data from [Checkmarx](https://checkmarx.com/) via one of two distinct approaches: The API Export Method or The CLI JSON Payload Parser.
------------------------------
## Approach 1: The Remediated Manifest API (Recommended)
Checkmarx provides an automated feature called Remediated Manifest Generation. Instead of parsing JSON reports and running scripts to edit your pom.xml, you invoke the [Checkmarx Export Service API](https://docs.checkmarx.com/en/34965-145615-checkmarx-sca--rest--api---export-service.html). This endpoint reads your scan results, modifies your project's pom.xml block automatically with the safe recommended versions, and hands it back to Tekton. [2, 3, 4] 
## The Tekton Automation Flow:

   1. Trigger the standard scan using the CLI tool (cx scan create) and capture the variable $CX_SCAN_ID.
   2. Send a POST request to the Export Service endpoint requesting the format type RemediatedPackagesJson or a direct updated layout.
   3. Apply the downloaded payload block over your file system workspace. [2, 4, 5, 6] 

# Fetch the auto-remediated pom.xml configuration directly from Checkmarx One
curl -X GET \
  -H "Authorization: Bearer $CX_TOKEN" \
  "https://checkmarx.net" \
  -o pom.xml

------------------------------
## Approach 2: Programmatic Parsing via ScanReportJson
If you need granular programmatic control—such as verifying the target version's Semantic Versioning (SemVer) layer before executing the upgrade—export the scan results as a ScanReportJson block. [4] 
Inside the JSON schema generated under Checkmarx SCA Export schemas, findings are structured into a packages layout array. For each vulnerable entity, Checkmarx maps a precise sub-object block containing recommendedVersion: [4, 7] 

{
  "packages": [
    {
      "id": "org.yaml:snakeyaml",
      "name": "snakeyaml",
      "currentVersion": "1.33",
      "packageManager": "Maven",
      "remediation": {
        "recommendedVersion": "2.0",
        "safeUpgradeAvailable": true
      }
    }
  ]
}

## Stitched Automated Decision Script:
Incorporate this script block directly after your Checkmarx report generation task completes to read the choices and apply upgrades dynamically:

#!/bin/shset -e
# Generate the JSON scan report from the Checkmarx CLI
/app/cx scan create --project-name "java-app" --branch "main" --report-format json --output-name cx-report
# Parse out matching 'DependencyCoordinates=TargetVersion' strings using JQ# This isolates entries where a valid recommended upgrade version is actively provided
UPGRADE_LIST=$(jq -r '.packages[] | select(.remediation.recommendedVersion != null) | "\(.id)=\(.remediation.recommendedVersion)"' cx-report.json)
if [ -z "$UPGRADE_LIST" ]; then
  echo "✅ Checkmarx data indicates no structural upgrades are currently available or required."
  exit 0fi
# Apply decision configurations natively via Mavenfor TARGET in $UPGRADE_LIST; do
  FLAWED_JAR=$(echo "$TARGET" | cut -d= -f1)
  RECOMMENDED_VERSION=$(echo "$TARGET" | cut -d= -f2)

  echo "🛠️ Decision Matrix: Upgrading $FLAWED_JAR to Checkmarx advised version ($RECOMMENDED_VERSION)"
  
  # Run the Versions execution goal to overwrite the pom.xml parameters safely
  mvn versions:use-dep-version \
    -Ddependency="$FLAWED_JAR" \
    -DdepVersion="$RECOMMENDED_VERSION" \
    -DforceVersion=truedone

------------------------------
## The Decision Strategy: Handling Missing Recommendations
Sometimes, a package shows critical vulnerabilities, but Checkmarx leaves the field "recommendedVersion": null. This scenario occurs when an open-source library has been completely abandoned by its maintainers, and no secure version exists anywhere in public repositories. [8] 
When this happens, your automation framework must use an alternative strategy:

                  / Does Checkmarx Provide \
                 <   a recommendedVersion?  >
                  \────────────────────────/
                     /                  \
         YES (Available)                 \ NO (Null)
               ▼                          ▼
   Execute automatic upgrade      Check for alternative packages
   via Maven or Manifest paths.   or block branch for manual review.


   1. If YES: The package is processed automatically via the mvn versions:use-dep-version bulk patch engine loop.
   2. If NO: Your script captures this condition using select(.remediation.recommendedVersion == null). Because the pipeline cannot apply a fix that doesn't exist, it adds an inline warning to the Bitbucket Data Center PR code review layout, alerting developers that they must replace the abandoned library entirely with a different open-source alternative.

Would you like to examine how to parse the Checkmarx API token authentication sequence to allow your Tekton Task to communicate with the Checkmarx cloud instance securely? [4] 

[1] [https://www.youtube.com](https://www.youtube.com/watch?v=ZWEyQj972fU&t=2)
[2] [https://docs.checkmarx.com](https://docs.checkmarx.com/en/34965-322318-sca-scanner.html)
[3] [https://docs.checkmarx.com](https://docs.checkmarx.com/en/34965-162795-remediating-sca-risks.html)
[4] [https://docs.checkmarx.com](https://docs.checkmarx.com/en/34965-145615-checkmarx-sca--rest--api---export-service.html)
[5] [https://docs.checkmarx.com](https://docs.checkmarx.com/en/34965-68643-scan.html)
[6] [https://docs.checkmarx.com](https://docs.checkmarx.com/en/34965-68643-scan.html)
[7] [https://docs.checkmarx.com](https://docs.checkmarx.com/en/34965-158449-sca-scan-reports.html)
[8] [https://docs.checkmarx.com](https://docs.checkmarx.com/en/34965-253661-sca-results.html)
