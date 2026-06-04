Yes, both tools can automate the upgrades, but they approach the process slightly differently. When automated PRs introduce breaking changes, it can disrupt development teams if not managed carefully.
Here is exactly how these tools handle upgrades, what happens when a breaking change occurs, and a strategy for managing non-breaking vs. breaking upgrades.
### 1. How the Tools Upgrade Libraries
 * **Renovate:** It works strictly on version ranges and semantic versioning (SemVer). It checks your package file, looks at the latest version available on Maven Central, PyPI, or npm registry, and automatically generates a Pull Request updating the version string.
 * **Snyk / Checkmarx SCA:** These tools are security-focused. They look specifically for the **lowest possible secure version**. For example, if you are on library version 1.2.0 and it has a vulnerability, and the vendor fixed it in 1.2.5 (a patch) and 2.0.0 (a major release), these tools will intelligently open a PR for 1.2.5 to minimize code breakage.
### 2. What Happens When Breaking Changes Introduce Failures?
If a tool opens an automated PR that introduces a breaking change, your **Bitbucket Pipelines (CI/CD)** becomes your safety net:
 1. The tool creates a new branch and opens a Pull Request in Bitbucket.
 2. Bitbucket Pipelines automatically triggers your build and test suites (e.g., mvn clean test, npm test, or pytest) on that PR branch.
 3. If the library change breaks your code, **the build fails**, and the PR status changes to "Failed."
 4. **No broken code reaches your main/production branch.** The PR simply sits there failing until a human developer intervenes or the tool closes it.
### 3. Strategy: Automated Non-Breaking Upgrades vs. Manual Breaking Reviews
Your intuition is entirely correct and represents industry best practices. Trying to automatically merge major, breaking updates is a recipe for broken pipelines and alert fatigue.
To handle this efficiently, you should configure your tooling to split upgrades into two distinct paths:
#### Path A: Automate & Automerge Non-Breaking Changes (Patches & Minors)
According to Semantic Versioning (SemVer), **Patch** updates (1.0.x) are for backward-compatible bug fixes, and **Minor** updates (1.x.0) are for backward-compatible features.
You can configure Renovate or Snyk to:
 1. Open PRs *only* for Patch and Minor updates.
 2. Enable **Automerge**: If your Bitbucket Pipeline build passes and all unit/integration tests are green, the tool will **automatically merge** the PR into your main branch without requiring an engineer to click a button. This completely automates away a massive chunk of your vulnerability backlog.
#### Path B: Segregate & Manually Review Breaking Changes (Majors)
**Major** updates (x.0.0) explicitly indicate breaking architectural changes. For these, you should use the following approach:
 * **Isolate the PRs:** Configure the tool to group all major upgrades into a specific schedule (e.g., "only open major PRs once a month on a Sunday") or assign them a specific Bitbucket label like security-major-review.
 * **Do Not Automerge:** Never allow automated merging on major versions.
 * **Manual Intervention Pipeline:** If a major upgrade PR fails the build, an AppSec engineer or Tech Lead should review the failure. They can then pair with a developer to update the deprecated Java methods, Python syntax, or Node.js APIs required to make the application compatible with the new library version.
### How to Configure this Strategy in Renovate
If you use Renovate, you can easily define this exact logic in a renovate.json file at the root of your repositories. It allows you to automatically merge safe changes while keeping breaking changes isolated:
```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended"],
  "packageRules": [
    {
      "description": "Automerge patch and minor updates if CI passes",
      "matchUpdateTypes": ["patch", "minor"],
      "automerge": true,
      "automergeType": "pr",
      "platformAutomerge": true
    },
    {
      "description": "Require manual review for major (breaking) updates",
      "matchUpdateTypes": ["major"],
      "automerge": false,
      "labels": ["requires-manual-migration"]
    }
  ]
}

```
### Summary
By implementing this split strategy, your team eliminates the noise of low-risk dependencies via automation, while safely gating breaking changes in Bitbucket PRs where they can be properly triaged, refactored, and tested by engineers.
