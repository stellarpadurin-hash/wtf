The distinction between a breaking and non-breaking change is determined programmatically by the exit status of your verification compiler (Maven) combined with Semantic Versioning (SemVer) analysis.
Because static analysis tools cannot predict with 100% certainty if an API method signature was deleted or altered inside a new JAR, your Tekton pipeline must use a Try-Catch-Rollback execution pattern to classify the change.
------------------------------
## The Classification Matrix

| Metric | Non-Breaking Change | Breaking Change |
|---|---|---|
| SemVer Jump | Patch or Minor level (1.2.0 ➔ 1.2.5) [1]. | Major level (1.2.0 ➔ 2.0.0) [1]. |
| mvn clean test-compile | Exits with code 0 (Success). | Exits with code 1 (Compilation Error). |
| Unit/Integration Tests | All assertions pass cleanly. | Test failures or runtime exceptions. |
| Pipeline Action | Merges immediately / proceeds with build. | Rolls back workspace and opens a PR. |

------------------------------
## Step 1: Programmatic Identification Logic
To identify which category a vulnerability fix falls into, your automation task script executes the following classification sequence:

# 1. Apply the upgrade using the Versions plugin
mvn versions:use-dep-version -Ddependency="$FLAWED_JAR" -DdepVersion="$FIXED_VERSION" -DforceVersion=true
# 2. RUN THE SAFTEY NET CHECK# We temporarily disable strict bash exit-on-error (+e) to safely capture Maven's crash statusset +e
mvn clean test-compile
COMPILE_EXIT_CODE=$?

mvn test -DfailIfNoTests=false
TEST_EXIT_CODE=$?set -e
# 3. EVALUATION MATRIXif [ $COMPILE_EXIT_CODE -eq 0 ] && [ $TEST_EXIT_CODE -eq 0 ]; then
    # -----------------------------------------------------------------
    # IDENTIFIED AS: NON-BREAKING CHANGE
    # -----------------------------------------------------------------
    echo "✅ CLASSIFICATION: Non-Breaking Change."
    echo "The code compiles perfectly and all tests passed. Proceeding with pipeline..."
    exit 0else
    # -----------------------------------------------------------------
    # IDENTIFIED AS: BREAKING CHANGE
    # -----------------------------------------------------------------
    echo "🚨 CLASSIFICATION: Breaking Change Detected."
    
    if [ $COMPILE_EXIT_CODE -ne 0 ]; then
        echo " -> Reason: Compilation failure (likely deleted classes, changed method signatures, or modified packages)."
    elif [ $TEST_EXIT_CODE -ne 0 ]; then
        echo " -> Reason: Test suite regression (the library upgraded successfully, but its internal behavior altered application logic)."
    fi
    
    # Trigger the safety rollback mechanism immediately
    echo "🔄 Rolling back local workspace modifications..."
    git reset --hard HEAD
    
    # Proceed to isolate this change on a branch and notify the developer via Bitbucket PR
    exit 1fi

------------------------------
## Why "Successful Compilation" is Not Enough (The Test Suite Rule)
A dependency update can pass compilation but still be a breaking change at runtime. Your verification phase must run unit and integration tests for complete validation.

* Example of Compile Pass / Runtime Break: Upgrading a database driver (e.g., Hibernate or a JDBC driver). The Java code will compile without errors because the interface classes look exactly the same. However, when the app boots up, a SQL query syntax change inside the new driver could trigger a runtime crash.
* The Pipeline Defense: By linking both test-compile and test execution outcomes together, your pipeline catches hidden behavioral regressions and correctly flags them as breaking changes.

------------------------------
## Advanced Tooling: Java API Compliance Checker
If you want to catch breaking API changes before compiling your code, you can integrate an open-source tool called revapi or the Java API Compliance Checker into your pipeline workflow.
These tools compare the binary structure of the old JAR against the new JAR. They generate a report detailing exact backward-compatibility breaks, such as:

* Method removed: A method used by your app no longer exists.
* Interface template changed: A class implementing an updated interface now lacks required methods.

If Revapi flags a BREAKING binary compatibility issue, your script can instantly classify the dependency upgrade as a breaking change and bypass the compilation loop entirely to save pipeline processing time.
Would you like to see how to embed the Revapi Maven Plugin configuration into your pom.xml to automate this structural binary check?

