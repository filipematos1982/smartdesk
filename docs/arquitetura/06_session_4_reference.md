# Session 4 reference and validation boundaries

## Confirmed scope

The user authorized automated testing, Jenkins reproducibility and failure gates, Docker image build and non-root validation, a local image workflow, local Kubernetes deployment preparation, PostgreSQL integration against a verified disposable target, and reproducible browser/performance checks where supported. Work starts from Session 3 commit `7dbe1ce743c4c8f791a2486f6c4a43644e788c32`.

The user handed over the Session 4 files and confirmed that no other SmartDesk specialist or editing tool was active. DevOps and QA must work sequentially. Image publication, Git push, external deployment, and Azure resource creation remain outside authorization.

## Available instructor evidence

The public [instructor SmartDesk repository](https://github.com/smartlearningci/smartdesk) README was reviewed anonymously on 16 November 2026. It describes unit, HTTP integration, pytest-bdd and PostgreSQL suites, JUnit/HTML reporting, and explicit incomplete performance and Chrome/Edge acceptance. It states that source publication does not demonstrate execution. These points inform the local implementation; the personal Git origin remains unchanged.

The full Session 4 outline/notebooks, exact Jenkins configuration, agent labels, plugin versions, credential identifiers, registry namespace, prescribed deployment commands, screenshots, and assessment thresholds were not provided. Public Jenkinsfile and raw source retrieval attempts returned cache-miss errors; these attempts do not establish whether such instructor files exist. No instructor-specific pipeline or deployment acceptance is certified.

## Existing product acceptance

The approved [requirements](../produto/02_requisitos_e_user_stories.md) define authentication, role permissions, ticket lifecycle, required fields, real Chrome/Edge compatibility, and a provisional three-second response target. Performance conditions must be documented before measurement. Synthetic local timing under a stated workload is evidence for that workload only; it is not a production capacity or instructor certification. Real browsers must use new temporary profiles and synthetic data; existing browser profiles and credentials are never opened.

## Implementation references

- [Jenkins Declarative Pipeline syntax](https://www.jenkins.io/doc/book/pipeline/syntax/)
- [Jenkins JUnit step](https://www.jenkins.io/doc/pipeline/steps/junit/): empty reports can conceal failures when explicitly allowed; SCM checks publication can be disabled.
- [Jenkins pipeline development tools](https://www.jenkins.io/doc/book/pipeline/development/): controller-backed linting and actual execution are separate evidence from local script tests.
- [Dockerfile reference](https://docs.docker.com/reference/dockerfile/): digest-based base image selection and runtime user configuration.
- [Playwright browser channels](https://playwright.dev/python/docs/browsers): branded Chrome/Edge checks differ from generic Chromium checks.

## Delivery and Session 5 boundary

Local build IDs and source hashes do not demonstrate Docker Hub publication or remote pulls. Registry ownership, target architecture, approved publication, immutable registry digest, target-cluster identity, and deployment permissions must be established before any external delivery. Session 5 may proceed with architecture and prerequisite preparation; Azure authentication, subscriptions, resources, or deployment require separate authorization. Existing databases, volumes, configuration, Git history, and private reports must be preserved.
