# Trigger a Checkmarx scan using this exact same DevSecOps workflow. [1] 
- Because [Checkmarx](https://checkmarx.com/) provides a lightweight, official [Checkmarx One CLI / CxFlow CLI](https://docs.checkmarx.com/en/34965-68643-scan.html), you can swap out the Trivy task from the previous architecture and insert a custom Tekton Task that packages your code and pushes it to Checkmarx. [2, 3] 
------------------------------
## How the Flow Changes
The webhook routing, the trigger binding, and the final status notification to Bitbucket remain exactly the same. The only element that changes is Task 2 inside the Tekton Pipeline:

   1. git-clone copies the code down to the workspace.
   2. checkmarx-scan (New) executes the Checkmarx CLI wrapper tool inside a container. It compresses your source code into a .zip archive and uploads it directly to the Checkmarx server via REST APIs.
   3. The CLI flag --break-on-policy or a custom threshold check forces the Tekton task to fail if critical vulnerabilities or policy violations are found. [1, 2, 3, 4] 

------------------------------
## Custom Tekton Task for Checkmarx
You can drop this reusable custom Task directly into your Kubernetes cluster to execute the scan. It uses a Kubernetes Secret to securely store your Checkmarx credentials (API Keys/Client Secrets): [5, 6] 
```
apiVersion: tekton.dev/v1beta1
kind: Taskmetadata:
  name: checkmarx-sast-scan
spec:
  workspaces:
    - name: source-dir
  params:
    - name: project-name
      type: string
      description: "The targeted Checkmarx project name"
    - name: checkmarx-base-url
      type: string
      default: "https://checkmarx.net" # Update to match your environment region
  steps:
    - name: run-cx-cli
      image: checkmarx/ast-cli:latest # Official enterprise container image
      workingDir: $(workspaces.source-dir.path)
      env:
        # Securely pass API Client Credentials into the environment
        - name: CX_CLIENT_ID
          valueFrom:
            secretKeyRef:
              name: checkmarx-creds
              key: client-id
        - name: CX_CLIENT_SECRET
          valueFrom:
            secretKeyRef:
              name: checkmarx-creds
              key: client-secret
      script: |
        #!/bin/sh
        
        echo "Initiating Checkmarx security scan for project: $(params.project-name)..."
        
        # Executes the scan, targets the workspace folder, and breaks the build on policy failure
        /app/cx scan create \
          --project-name "$(params.project-name)" \
          --sources . \
          --base-uri "$(params.checkmarx-base-url)" \
          --client-id "$CX_CLIENT_ID" \
          --client-secret "$CX_CLIENT_SECRET" \
          --scan-types sast \
          --report-format json \
          --async=false # Setting async=false forces Tekton to wait for the scan result before continuing

------------------------------
## Incorporating it Into the Pipeline
To use this, simply modify the tasks layout inside your main Pipeline YAML block like this:

  tasks:
    - name: clone-code
      taskRef:
        name: git-clone
      workspaces:
        - name: output
          workspace: shared-workspace
      params:
        - name: url
          value: $(params.repo-url)
        - name: revision
          value: $(params.revision)

    # REPLACED: Trivy out, Checkmarx in!
    - name: vulnerability-scan
      runAfter: [clone-code]
      taskRef:
        name: checkmarx-sast-scan
      workspaces:
        - name: source-dir
          workspace: shared-workspace
      params:
        - name: project-name
          value: $(params.repo-slug) # Dynamically creates/uses a Checkmarx project named after your repo
```
## Architectural Benefits of this Approach

* Real-time Feedback: Developers will see a "Checkmarx-Security-Gate" status check appear right next to their commits directly inside the Bitbucket Pull Request interface.
* No Orphaned Scans: Because async=false is used in the task, if a developer fixes their code and pushes a new commit, Tekton cancels the older pipeline run, saving your Checkmarx licensing scan slots.

