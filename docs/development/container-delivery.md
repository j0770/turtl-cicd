# Container delivery and SBOM

`containers.yml` builds frontend and backend for Linux/amd64. Pull requests build images, run smoke tests and generate SBOMs with read-only permissions. Pushes on `main` can publish the same built images to GHCR after a successful CI run for the exact source commit. Workflow dispatch performs build-only validation.

Images are transferred between jobs as SHA-256-checked Docker archives. Publication does not rebuild them. A complete commit-based tag is used; existing tags are not overwritten. The registry digest is pulled back and the config digest, runtime configuration and rootfs layer IDs must match the built archive. Consumers should use the recorded digest, not assume that a tag is an immutable registry object.

## Package visibility

The workflow accepts both private and public GHCR packages and records package metadata before and after each push. It publishes to the package paths `ghcr.io/j0770/turtl/{frontend,backend}` using the short-lived repository `GITHUB_TOKEN`. GHCR creates new packages as private by default. To allow anonymous pulls, set the package visibility to public in its GitHub settings after the first publish. Deployment also accepts the original `turtl-cicd-private` digest references so existing releases remain deployable.

References: [GitHub registry defaults](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry), [Package visibility](https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility).

## Runtime configuration and packaging

The frontend image contains `deploy/frontend/nginx.container.conf`, with a generic server name and the forwarded Host header. Certificates are supplied at runtime. Existing manually configured `deploy/frontend/nginx.conf` is mounted by the Compose setup, preserving environment-specific settings without baking them into the image. The installation guide's copy-and-edit step remains required for that Compose setup.

The backend copies only application directories and manage.py. Repository metadata, frontend dependencies, local environment files and certificates are not copied. The existing Daphne startup and non-root user remain. Both Dockerfiles still use moving base tags and package repositories; bit-for-bit reproducibility and complete action pinning across the entire project are not claimed. New container-workflow actions are pinned to full commits.

## Deployment on the target host

Copy the `deploy/` configuration to the target and provision its `.env`, Nginx configuration and certificates as documented in the installation guide. Use the same directory and Compose project name as the existing installation to retain its volumes. The host needs Docker Compose, Bash, `curl` and `flock`. If the GHCR packages are private, authenticate the host to the registry with credentials that can read both packages.

Take both image digest references from the same successful Container delivery run's `published-frontend` and `published-backend` evidence. Run the script on the approved target with the HTTPS URL and an absolute path to a protected backup directory.

```bash
export TURTL_BASE_URL=https://turtl.example.org
export TURTL_BACKUP_DIR=/var/backups/turtl
bash deploy/deploy-ghcr.sh "$frontend_digest_ref" "$backend_digest_ref"
```

The script uses the existing Compose services and the `compose.ghcr.yaml` overrides. It records the current frontend and backend images, pulls the selected images, makes a PostgreSQL dump and checks its archive listing before running migrations and collecting static assets. It then starts the stack and checks the frontend and Django admin over HTTPS. The backup directory also holds the selected image references after a successful deployment.

### Release and automatic deployment

From `main`, run **Prepare deployment release** with a stable version tag and the full commit SHA of a successful Container delivery run. The workflow verifies both publication records and attaches `deployment.json` to a draft GitHub Release. Review the draft and publish it as the latest release to approve deployment. The public release asset contains the two digest references and their source commit and run ID.

On the target VM, install `jq` and copy the deployment configuration to `/opt/turtl/deploy`. The systemd service runs as `turtl-deploy`. Give this account access to Docker, the local deployment configuration, the backups directory and both GHCR packages. Configure the registry login for this account so the service can pull the images.

Set `TURTL_BASE_URL` and `TURTL_BACKUP_DIR` in `/etc/turtl/deployment.env`. Install the units and start the timer after the first release is published:

```bash
sudo install -m 0644 deploy/systemd/turtl-deploy.{service,timer} /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now turtl-deploy.timer
```

The timer checks the latest release every five minutes after each completed check. A different image pair triggers the deployment script. The service records the manifest in `/var/lib/turtl-deploy/deployment.json` after the script succeeds. Inspect runs with `journalctl -u turtl-deploy.service`. An isolated test VM can set `TURTL_RELEASE_URL` to a trusted HTTPS endpoint serving its own test manifest.

### Rollback

Stop `turtl-deploy.timer` before a manual rollback and let any active deployment finish. With a compatible database schema, set `TURTL_FRONTEND_IMAGE` and `TURTL_BACKEND_IMAGE` to the previous digest references. In the deployment directory, use `docker compose --env-file .env -f docker-compose.yaml -f compose.ghcr.yaml pull frontend backend` followed by `docker compose --env-file .env -f docker-compose.yaml -f compose.ghcr.yaml up -d --no-build --wait`. Decide separately whether recovery requires restoring the database backup. Before resuming the timer, make the desired release the latest release and remove the saved deployment manifest so the next check reconciles the recorded and running versions.

## Actual checks and SBOM scope

The backend smoke check imports core libraries, checks application packaging and invokes Daphne help. It does not start Django against PostgreSQL/Redis or Proxmox. The frontend smoke check starts Nginx with a short-lived test certificate and checks the HTTPS SPA entry. It does not validate backend proxying, authentication or an actual target deployment.

Syft 1.56.0 produces CycloneDX JSON 1.6 and native Syft JSON from the built image. The evidence script validates against the vendored official CycloneDX schemas without network resolution, checks the SHA-256 digest of the Syft source configuration against the config blob of the built Docker archive, inspected runtime configuration, rootfs layer IDs, commit label and non-root user, and records hashes, timestamp, platform, selected package detections and missing license fields. Four tests cover valid and invalid license data, a current SPDX identifier and an empty inventory. The schema source commit and Apache 2.0 license are retained under `schemas/cyclonedx-1.6/`.

After publication, a second SBOM is generated directly from the registry digest. Sidecar evidence binds commit, workflow URL, image ID, registry digest and SBOM hashes. OS and Python packages can be recognized from runtime metadata. Bundled/minified browser dependencies may not be identifiable in the final Nginx image; missing Vue/Axios detections must be documented, not inferred absent. This image inventory is not a substitute for the source-lock dependency audit.

SBOM generation is neither an image vulnerability scan nor a license-compliance assessment. Current dependency findings remain open. No signing, formal SLSA level, automatic release-version promotion or full license allowlist is claimed.

Docker archive artifacts are retained for seven days, SBOM and publication evidence for 90 days subject to GitHub limits. Save thesis evidence before expiration. To demonstrate publication, record the actual run and package visibility response.

Docker with a containerd image store can report an OCI manifest digest as its image ID, while Syft reports a config digest. These identifiers are recorded separately and are not incorrectly required to be equal. Their association is established through the saved image archive and matching configuration/filesystem identities.
