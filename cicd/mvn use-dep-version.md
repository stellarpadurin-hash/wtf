# Using Maven versions:use-dep-version
- In the Versions Maven Plugin, the specific goal responsible for forcing an explicit library string update is named exactly **versions:use-dep-version**
------------------------------
## Execution Parameters for versions:use-dep-version
When integrating this goal into an automated DevSecOps script loop, we must supply three critical flags to prevent the execution engine from prompting for human user interaction:
```
mvn versions:use-dep-version \
  -Ddependency="org.yaml:snakeyaml" \
  -DdepVersion="2.0" \
  -DforceVersion=true
```
## Why -DforceVersion=true is Critical for Pipelines
By default, versions:use-dep-version attempts to pull down metadata from Maven Central or the private Nexus repo to verify if the specified version actually exists. [5] 
If the pipeline runner is executing in an isolated offline container or dealing with an advanced upstream build, setting -DforceVersion=true bypasses the network lookup check entirely. It forces the plugin to overwrite the XML file string immediately, saving significant testing overhead time. [5] 

