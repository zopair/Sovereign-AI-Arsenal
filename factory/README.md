# Factory GitHub Repository Inspector

A dependency-free, read-only repository inspection utility for the Sovereign AI Application Factory.

## What it does

- Resolves the repository's default branch to its commit and Git tree.
- Inspects repository metadata, license signals, README content, and file-path signals.
- Detects likely capabilities such as web, mobile, Python, Node.js, databases, AI, agents, automation, Docker, and tests.
- Produces JSON recommendations for missing engineering controls.
- Recovers a truncated recursive Git tree through bounded, non-recursive traversal.
- Retries transient GitHub API failures and rate limits within a strict wait budget.

## Quick start

Python 3.11+; standard library only.

```bash
export GITHUB_TOKEN="YOUR_READ_ONLY_GITHUB_TOKEN"
python -m factory.manager owner/repository
```

The token is optional for public repositories, but authenticated read-only access provides a higher GitHub API rate limit. The inspector never writes to GitHub and never executes repository code.

## Reliability boundaries

- Maximum 3 API attempts per request.
- Maximum 10 seconds of waiting per retry delay.
- Maximum 1,000 directory-tree objects during truncated-tree recovery.
- If GitHub still returns a truncated directory during fallback, inspection fails explicitly rather than reporting a partial inventory as complete.
- A missing README (404) is optional; authorization and rate-limit errors are not suppressed.

## Proof of Concept & Enterprise Customization Readiness

<badge>Proof of Concept</badge>

The inspector is a reusable read-only capability, not a complete AI orchestration engine. Capability detection is heuristic and must be reviewed before making release or security decisions. Enterprise extensions can add repository policy packs, richer evidence scoring, organization-wide pagination, and audit persistence without changing the read-only boundary.

## Intellectual Property & Authorship

Authored for the Zubair AI ecosystem by **Aly Hussein Zopair (علي حسين زبير ALY HUSSEIN ZOPAIR)**.
