# Private container delivery and SBOM

`containers.yml` builds frontend and backend for Linux/amd64. Pull requests only build, smoke-check and generate SBOMs; they do not receive package write permission. Pushes on `main` and the explicitly listed temporary validation branch can promote the same built images to private GHCR packages after a successful CI run for the exact source commit. Workflow dispatch performs build-only validation.

Images are transferred between jobs as SHA-256-checked Docker archives. Publication does not rebuild them. A complete commit-based tag is used; existing tags are not overwritten. The registry digest is pulled back and the Docker image ID must match the built image. Consumers should use the recorded digest, not assume that a tag is an immutable registry object.

## Privacy requirement

Images must remain private. Publication first requires a private repository with a personal-account owner. An existing package must report `visibility: private`; public packages, permission errors and unknown states stop publication. A 404 permits first creation because new personal GHCR packages are private by default. Immediately after pushing, the package API must again report private. The workflow never changes visibility. It publishes only to `ghcr.io/j0770/turtl-cicd-private/{frontend,backend}`. Authentication uses the short-lived repository `GITHUB_TOKEN`; no personal publishing token is stored.

References: [GitHub registry defaults](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry), [Package visibility](https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility). The temporary validation branch uses `validation-sha-<full commit>` tags; these are not production releases. No deployment, public image or public repository is created by the workflow.

## Runtime configuration and packaging

The frontend image contains `deploy/frontend/nginx.container.conf`, with a generic server name and the forwarded Host header. Certificates are supplied at runtime. Existing manually configured `deploy/frontend/nginx.conf` is mounted by the Compose setup, preserving environment-specific settings without baking them into the image. The installation guide's copy-and-edit step remains required for that Compose setup.

The backend copies only application directories and manage.py. Repository metadata, frontend dependencies, local environment files and certificates are not copied. The existing Daphne startup and non-root user remain. Both Dockerfiles still use moving base tags and package repositories; bit-for-bit reproducibility and complete action pinning across the entire project are not claimed. New container-workflow actions are pinned to full commits.

## Actual checks and SBOM scope

The backend smoke check imports core libraries, checks application packaging and invokes Daphne help. It does not start Django against PostgreSQL/Redis or Proxmox. The frontend smoke check starts Nginx with a short-lived test certificate and checks the HTTPS SPA entry. It does not validate backend proxying, authentication or an actual target deployment.

Syft 1.56.0 produces CycloneDX JSON 1.6 and native Syft JSON from the built image. The evidence script validates against the vendored official CycloneDX schemas without network resolution, checks image ID, commit label and non-root user, and records hashes, timestamp, platform, selected package detections and missing license fields. Three tests cover valid and invalid license data and an empty inventory. The schema source commit and Apache 2.0 license are retained under `schemas/cyclonedx-1.6/`.

After publication, a second SBOM is generated directly from the private registry digest. Sidecar evidence binds commit, workflow URL, image ID, registry digest and SBOM hashes. OS and Python packages can be recognized from runtime metadata. Bundled/minified browser dependencies may not be identifiable in the final Nginx image; missing Vue/Axios detections must be documented, not inferred absent. This image inventory is not a substitute for the source-lock dependency audit.

SBOM generation is neither an image vulnerability scan nor a license-compliance assessment. Current dependency findings remain open. No signing, formal SLSA level, automatic release-version promotion or full license allowlist is claimed.

Docker archive artifacts are retained for seven days, SBOM and publication evidence for 90 days subject to GitHub limits. Save thesis evidence before expiration. A workflow configuration or a successful build alone is not evidence of successful private publication; record the actual run and package visibility response.
