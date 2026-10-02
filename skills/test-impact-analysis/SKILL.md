---
name: test-impact-analysis
description: Test Impact Analysis (TIA) — run only the subset of an existing test suite affected by a code change instead of the full suite on every CI run. Use when a regression/E2E/unit suite has grown slow (10+ minutes) and most changes only touch a small part of the codebase. Covers two approaches — per-test coverage-based skipping (Datadog ITR-style) and dependency-graph-based selection (Nx-affected-style for monorepos) — plus the pitfalls that make blind adoption unsafe. Triggers on "test impact analysis", "TIA", "selective test execution", "skip unaffected tests", "speed up CI test suite", "nx affected", "only run tests for changed files".
---

# Test Impact Analysis (TIA) — Run Only the Tests That Matter

TIA doesn't change *what* tests exist — it changes *which already-written tests run on a given change*. It's orthogonal to `behavioral-coverage-matrix` (what to test) and `pairwise-combinatorial-testing` (how to reduce input combinations): those shrink the suite once, at authoring time; TIA re-selects a subset of the existing suite on every run, based on the diff.

## When to reach for this

- CI test suite takes long enough that "run everything, every time" is the bottleneck, and most PRs touch a small fraction of the codebase.
- You already have a full suite and want faster PR feedback — not a substitute for having good coverage in the first place.

## Approach 1 — Per-test coverage-based skipping

Collect **per-test code coverage** during a baseline full run (which files each test actually exercises). On a subsequent run, diff the changed files against the base branch, then skip any test whose recorded coverage doesn't include a changed file.

Concrete mechanics (verified against Datadog's Intelligent Test Runner, the most fully-documented implementation):

- Requires git available in the test environment; the coverage-to-test mapping is collected during normal test execution (file-level granularity), then cross-referenced against the changed-file diff on later runs.
- Supported per-language implementations exist for .NET, Java, JavaScript, Swift, Python, Ruby, Go — this is a per-language integration, not a generic wrapper.
- Collecting per-test coverage has a real performance cost on the baseline run itself (excluded/instrumented branches pay for full per-test coverage collection).
- Override mechanisms, because the mapping can be wrong or you need a forced full run:
  - A trigger string in the commit message (e.g. `ITR:NoSkip`) forces a full run for that commit.
  - A PR label (`ITR:NoSkip`) does the same at the PR level.
  - Individual tests can be marked **unskippable** — always run regardless of the coverage mapping.
  - Specific files can be marked as **tracked files** — any change to them forces a full run even though the file itself has no direct test coverage (config files, schemas, migrations).
- Settings cascade org → repo → test-service level, with the more specific level winning.

## Approach 2 — Dependency-graph-based selection (monorepos)

For monorepos with many independent packages/apps, coverage-based mapping doesn't compose well across package boundaries. Build-graph tools instead:

1. Diff changed files between a base and head ref (`git diff base..head`).
2. Reverse-lookup which project(s) in the workspace's dependency graph own those files.
3. Walk the graph forward to find every project that **depends on** an affected project (a change to a shared lib affects every app that imports it).
4. Run the target (e.g. `test`) only for that affected set.

Example (Nx):

```bash
nx affected -t test --base=main --head=HEAD
```

- Configure **named inputs** so only files that actually influence a target's output count toward "affected" — e.g. editing a test spec file should invalidate the `test` target but not the `build` target for that project; editing a lockfile should invalidate everything.
- Combine with `--focus`/graph intersection when you only care whether a specific deployable app is affected, to avoid re-running tests for unrelated leaf packages that happen to be "affected" but aren't part of what's shipping.
- Equivalent affected-graph concepts exist in Bazel and Turborepo — same core idea (git diff → build/dependency graph → downstream closure), different CLI surface.

## The pitfall that makes blind adoption unsafe

Neither approach can see *everything* that determines test outcome:

- Coverage-based mapping cannot detect changes to library dependencies, compiler/build config, external services, or data files read by data-driven tests — none of these show up as "a file this test's recorded coverage touches."
- Dependency-graph mapping only sees the graph edges it's configured to see — dynamic imports, reflection, config-driven behavior, and cross-service calls are invisible to a static file-ownership graph.

Mitigations, use both:
- Tag payment/auth/destructive-action tests **unskippable** — never let a heuristic silently drop critical-path coverage, mirroring the same rule this repo's `pairwise-combinatorial-testing` skill applies to combinatorial reduction.
- Mark known blind spots (schema files, feature-flag config, shared fixtures) as **tracked files** that force a full run.
- Schedule a full regression run on a cadence (nightly, pre-release) regardless of what TIA selected that day — treat TIA as a PR-feedback accelerant, not the system of record for "is this change safe."

## Built-in option for Playwright suites: `--only-changed` (1.46+)

Before adopting an external TIA platform for a Playwright E2E suite, try the native flag:

```bash
npx playwright test --only-changed=main   # files changed vs `main` + test files that import them
npx playwright test --only-changed        # default: uncommitted changes
```

It is file/import-graph based (Git only), so it has the same blind spot as Approach 2: a change
to app code that the spec files don't import (most E2E specs only import page objects) selects
nothing. Treat it as a PR-feedback shortcut — keep the scheduled full run.

## Decision table

| Situation | Use |
|---|---|
| Playwright E2E suite, quick win in CI | `--only-changed=<base>` for PR runs + nightly full run |
| Single repo/service, coverage instrumentation already exists (Jest/pytest/JUnit coverage) | Coverage-based selective testing |
| True monorepo with multiple independent packages/apps | Dependency-graph-based (Nx/Bazel/Turborepo affected) |
| Payment/auth/destructive-action tests, regardless of which approach you adopt | Mark unskippable — don't trust the heuristic |
| Config/schema/fixture files with no direct test coverage | Mark as tracked files — force full run on change |

## Sources
- [Datadog Test Impact Analysis docs](https://docs.datadoghq.com/tests/test_impact_analysis/) (fetched directly — coverage granularity, supported languages, override mechanisms, config cascade)
- [Nx: Run Only Tasks Affected by a PR](https://nx.dev/docs/features/ci-features/affected) (direct fetch returned HTTP 403 to the fetcher; corroborated via WebSearch summary and cross-checked against [Nx Deep Dive](https://smartsdlc.dev/blog/deep-dive-into-nx-affected/) and [LeanIX Engineering: smarter nx affected checks](https://engineering.leanix.net/blog/smarter-nx-affected-checks/))
- Background/pitfalls corroboration (direct fetches 403'd to the fetcher, used as WebSearch-summary corroboration only): [Martin Fowler — The Rise of Test Impact Analysis](https://martinfowler.com/articles/rise-test-impact-analysis.html), [CloudBees — Test Impact Analysis](https://www.cloudbees.com/blog/test-impact-analysis), [Testkube — Test Impact Analysis glossary](https://testkube.io/glossary/test-impact-analysis-tia)
