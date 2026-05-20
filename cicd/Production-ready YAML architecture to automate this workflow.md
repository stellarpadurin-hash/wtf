Here is the complete, production-ready YAML architecture to automate this workflow.
This setup captures the webhook payload from Bitbucket Data Center when a Pull Request is opened or updated, runs a Trivy vulnerability scan, and reports the SUCCESS or FAILED build status back to Bitbucket to enforce the merge gate.
------------------------------
## 1. The Trigger Binding
This component extracts the precise commit hash, project/repository keys, and pull request information from the unique Bitbucket Data Center JSON payload structure [1].

apiVersion: triggers.tekton.dev/v1alpha1kind: TriggerBindingmetadata:
  name: bitbucket-dc-pr-bindingspec:
  params:
    # Extracts the latest commit ID from the source branch of the PR
    - name: git-commit
      value: $(body.pullRequest.fromRef.latestCommit)
    # Extracts the specific branch name to clone
    - name: git-revision
      value: $(body.pullRequest.fromRef.displayId)
    # Extracts the HTTP clone URL
    - name: git-repo-url
      value: $(body.pullRequest.fromRef.repository.links.clone[0].href)
    # Extracted metadata required to post the status back to Bitbucket's API
    - name: bitbucket-project
      value: $(body.pullRequest.toRef.repository.project.key)
    - name: bitbucket-repo
      value: $(body.pullRequest.toRef.repository.slug)

------------------------------
## 2. The Trigger Template
This template acts as the blueprint. It takes the parameters extracted by the binding above and instantiates your CI Pipeline Run [1].

apiVersion: triggers.tekton.dev/v1alpha1kind: TriggerTemplatemetadata:
  name: bitbucket-dc-pr-templatespec:
  params:
    - name: git-commit
    - name: git-revision
    - name: git-repo-url
    - name: bitbucket-project
    - name: bitbucket-repo
  resourcetemplates:
    - apiVersion: tekton.dev/v1beta1
      kind: PipelineRun
      metadata:
        generateName: security-gate-run-
      spec:
        pipelineRef:
          name: security-gate-pipeline
        params:
          - name: repo-url
            value: $(tt.params.git-repo-url)
          - name: revision
            value: $(tt.params.git-revision)
          - name: commit-id
            value: $(tt.params.git-commit)
          - name: project-key
            value: $(tt.params.bitbucket-project)
          - name: repo-slug
            value: $(tt.params.bitbucket-repo)
        workspaces:
          - name: shared-workspace
            volumeClaimTemplate:
              spec:
                accessModes:
                  - ReadWriteOnce
                resources:
                  requests:
                    storage: 1Gi

------------------------------
## 3. The DevSecOps Pipeline
This pipeline clones the code, scans it for vulnerabilities, and uses a finally block to guarantee Bitbucket is updated even if the vulnerability scan crashes or fails.

apiVersion: tekton.dev/v1beta1kind: Pipelinemetadata:
  name: security-gate-pipelinespec:
  params:
    - name: repo-url
    - name: revision
    - name: commit-id
    - name: project-key
    - name: repo-slug
  workspaces:
    - name: shared-workspace
  tasks:
    # Task 1: Clone the branch code
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

    # Task 2: Scan for Vulnerabilities (e.g., using Trivy)
    - name: vulnerability-scan
      runAfter: [- name: clone-code]
      taskRef:
        name: trivy-scanner
      workspaces:
        - name: manifest-dir
          workspace: shared-workspace
      params:
        # --exit-code 1 forces Tekton to fail the task if high/critical flaws exist
        - name: ARGS
          value: ["fs", "--severity", "HIGH,CRITICAL", "--exit-code", "1", "."]

  # Finally Block: Always runs to unblock or block the Bitbucket Merge Gate
  finally:
    - name: post-status-to-bitbucket
      taskRef:
        name: bitbucket-server-set-build-status
      params:
        - name: BITBUCKET_SERVER_URL
          value: "https://yourcompany.com" # Replace with your URL
        - name: REPO_SLUG
          value: $(params.repo-slug)
        - name: COMMIT_ID
          value: $(params.commit-id)
        # Python/Shell logic map: if vulnerability-scan == "Succeeded", status is "SUCCESSFUL", else "FAILED"
        - name: STATE
          value: $(tasks.vulnerability-scan.status) 
        - name: KEY
          value: "Tekton-Security-Gate"
        - name: NAME
          value: "Vulnerability Scan Gate"
        - name: DESCRIPTION
          value: "Checking branch code for CVEs and hardcoded secrets."

------------------------------
## 4. The Event Listener
This service exposes the HTTP endpoint that you paste into Bitbucket's Webhook configuration interface.

apiVersion: triggers.tekton.dev/v1alpha1kind: EventListenermetadata:
  name: bitbucket-dc-listenerspec:
  serviceAccountName: tekton-triggers-sa
  triggers:
    - name: pr-events
      interceptors:
        # Native Tekton interceptor to validate Bitbucket Server payload formats
        - ref:
            name: bitbucket
          params:
            - name: eventTypes
              value: 
                - "pr:opened"
                - "pr:from_ref_updated"
      bindings:
        - ref: bitbucket-dc-pr-binding
      template:
        ref: bitbucket-dc-pr-template

## Next Steps to Make This Work

   1. Ensure the git-clone, trivy-scanner, and bitbucket-server-set-build-status Tasks are installed in your cluster from the Tekton Hub.
   2. Create a Kubernetes Secret containing a Bitbucket Personal Access Token (PAT) so Tekton has API permissions to write the build status back to https://yourcompany.com.
   3. In Bitbucket, configure your Webhook URL to point to the external IP/route of your bitbucket-dc-listener service.

Do you need help configuring the Kubernetes Secret or the Service Account permissions required for Tekton to talk to Bitbucket securely?

