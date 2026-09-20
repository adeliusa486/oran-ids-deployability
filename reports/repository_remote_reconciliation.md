# EXP-024 — Repository / remote reconciliation

**Date:** 2026-09-20
**Phase:** 24
**Verdict:** **NO DISCREPANCY.** Local and remote are byte-identical. No recovery
action was needed, and none was taken.

---

## Why this phase existed

The campaign brief opened with a reported conflict:

> The previous session report says 24 commits were pushed, but the currently
> visible public repository page presently shows a different state: the page
> displays only one commit and describes the repository as a skeleton with
> research modules unimplemented.

A repository whose history had been lost, rewritten or pushed to the wrong remote
would invalidate every later phase, so this was settled before any experiment ran.
The instruction was explicit that neither the session report nor the web page
should be assumed correct. Both were checked against git itself.

## What was measured

```
$ git rev-parse HEAD
faa2849d5e6f949021c8f988461b7d4559df5f02

$ git ls-remote origin
faa2849d5e6f949021c8f988461b7d4559df5f02    HEAD
faa2849d5e6f949021c8f988461b7d4559df5f02    refs/heads/main

$ git fetch origin && git rev-parse origin/main
faa2849d5e6f949021c8f988461b7d4559df5f02

$ git diff --stat HEAD origin/main
(no output)

$ git branch -a
* main
  remotes/origin/main

$ git status --short
(no output)
```

`git ls-remote` asks the remote directly rather than reading a cached ref, so this
is the remote's own answer, not a local mirror of it.

## Verification against the required checklist

| Required check | Result |
|---|---|
| `local HEAD == intended canonical commit` | PASS — `faa2849`, 25 commits |
| `remote main == canonical commit` | PASS — identical SHA |
| `MEMORY.md` exists remotely | PASS |
| results exist remotely | PASS — `results/EXP-000` … `EXP-005` in `origin/main` tree |
| reports exist remotely | PASS — including `SESSION_REPORT.md` |
| paper exists remotely | PASS — `paper/main.tex`, `paper/measured_results.tex` |

Remote tree membership was confirmed with `git ls-tree -r origin/main`, which
reads the fetched remote tree object rather than the working directory.

## Reconciling the reported conflict

Each hypothesis the brief asked to be considered, and what the evidence says:

| Hypothesis | Verdict | Evidence |
|---|---|---|
| Push failed | **No** | `ls-remote` returns the local SHA |
| Remote changed under us | **No** | Single branch, no divergence, clean tree |
| Wrong repository was pushed | **No** | `origin` is `adeliusa486/oran-ids-deployability` |
| Local repository differs | **No** | `git diff HEAD origin/main` is empty |
| History was rewritten | **No** | 25 commits, `6d657fe` → `faa2849`, linear |
| Another branch holds the work | **No** | `main` is the only branch, local or remote |
| **GitHub display was stale** | **Consistent with all evidence** | The described page — one commit, "skeleton", research modules unimplemented — is an exact description of `6d657fe`, the repository's **first** commit |

The observation in the brief is best explained by a page rendered or cached before
the session's pushes landed. `6d657fe` is literally titled "Repository skeleton",
and at that commit `src/` did contain 11 empty `__init__.py` files and nothing
else. The description matches that commit precisely and matches no later one.

One note for whoever looks next: the git repository is **not** at the top of the
working folder. It is `oran-ids-deployability/` inside it. Running `git log` one
level up reports `not a git repository`, which on a quick look resembles a lost
history and is not one.

## Action taken

None to the history. No reset, no force-push, no branch surgery — the brief's
instruction not to force-push blindly was moot, since there was nothing to
reconcile.

This report and the phase's registry entry are the only artefacts.

## Standing recommendation

Before trusting a GitHub web view of this repository again, run:

```bash
git ls-remote origin refs/heads/main
```

It is one command, it asks the server, and it cannot be stale.
