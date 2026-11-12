# Session 3 reference and acceptance boundaries

## Confirmed training scope

The user confirmed PostgreSQL persistence, Docker Compose, local Kubernetes using k3s, Headlamp, Docker image preparation, and the Docker Hub workflow. The instructor references Notebook 09A (initialization, image, and Docker Hub) and Notebook 09B (k3s, PostgreSQL, and Headlamp).

The full notebooks were not supplied. Exact notebook commands, expected screenshots, image naming conventions, prescribed Kubernetes objects, and assessment thresholds cannot be certified or invented.

## Public implementation reference

The public instructor repository, [smartlearningci/smartdesk](https://github.com/smartlearningci/smartdesk), was reviewed anonymously on 12 November 2026. The README and original `compose.k3s.yaml` and `headlamp-lab.yaml` establish the existing local training topology. The local starting files matched those reference manifests. This reference is for implementation comparison; the personal Git origin remains `https://github.com/filipematos1982/smartdesk.git`.

The instructor reference uses a privileged k3s-in-Docker lab, PostgreSQL 16, and a Headlamp viewer configuration. Privilege is limited to a separately created local training cluster; it is not a production deployment recommendation. Local validation must not use ambient Kubernetes contexts, existing database volumes, or company resources.

## Image preparation and Docker Hub workflow

Local image build and import into the dedicated k3s cluster are permitted for this session. Local image import verifies Kubernetes deployment without publishing anything or requiring registry credentials.

For a future separately authorized Docker Hub publication:

1. Confirm the personal Docker Hub namespace and a unique release tag with the user. A GitHub username does not establish a Docker Hub namespace.
2. Select the required target architecture or multi-platform manifest and build a reviewed image from the personal repository.
3. Check the image contents and vulnerability findings, capture the source commit and image digest, and verify the tag on the personal namespace.
4. Obtain explicit approval before registry authentication or publication. Use a personal scoped token through secure standard input or an approved credential store; never put tokens in command arguments, manifests, Git, or logs.
5. After approved publication, verify the remote digest and update the approved deployment to an immutable image reference. Do not use mutable `latest` as evidence of a reproducible release.

Docker Hub authentication, namespace ownership, publication, remote pulls of the personal image, and notebook-specific registry acceptance are not validated by a local build/import. No publication commands are executed in Session 3.

## Evidence required

Record actual automated tests, target identity checks, Compose application/database behavior, synthetic ticket persistence, backup/restore into a new target, and local Kubernetes/Headlamp checks in a separate Session 3 validation record. Distinguish static configuration checks, running-system checks, failures, skips, and unavailable instructor acceptance.

Never remove an existing database or Docker volume to satisfy an exercise. Use unique, labelled local validation resources, preserve evidence, and stop only resources created for the current validation. Public deployment and Session 4 are outside this session.
