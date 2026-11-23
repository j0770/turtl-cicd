#!/usr/bin/env bash
set -euo pipefail
umask 077

if [[ $# -ne 2 ]]; then
  echo 'Usage: bash deploy-ghcr.sh FRONTEND_IMAGE BACKEND_IMAGE' >&2
  exit 2
fi

export TURTL_FRONTEND_IMAGE=$1 TURTL_BACKEND_IMAGE=$2
: "${TURTL_BACKUP_DIR:?Set TURTL_BACKUP_DIR to an absolute directory for deployment records and database backups}"
: "${TURTL_BASE_URL:?Set TURTL_BASE_URL to the target HTTPS address}"

if [[ ! $TURTL_FRONTEND_IMAGE =~ ^ghcr\.io/j0770/turtl-cicd-private/frontend@sha256:[0-9a-f]{64}$ ||
      ! $TURTL_BACKEND_IMAGE =~ ^ghcr\.io/j0770/turtl-cicd-private/backend@sha256:[0-9a-f]{64}$ ||
      $TURTL_BACKUP_DIR != /* || $TURTL_BASE_URL != https://?* ]]; then
  echo 'Expected the TURTL GHCR digest references, an absolute backup path and an HTTPS address.' >&2
  exit 2
fi

cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
compose=(docker compose --env-file .env -f docker-compose.yaml -f compose.ghcr.yaml)
"${compose[@]}" config --quiet

mkdir -p -- "$TURTL_BACKUP_DIR"
exec 9>"$TURTL_BACKUP_DIR/deploy.lock"
if ! flock -n 9; then
  echo 'A deployment is already running in this backup directory.' >&2
  exit 1
fi
record_dir=$(mktemp -d "$TURTL_BACKUP_DIR/deployment-$(date -u +%Y%m%dT%H%M%SZ)-XXXXXX")
echo "Deployment records: $record_dir"

for service in frontend backend; do
  container=$("${compose[@]}" ps --quiet "$service")
  if [[ -n $container ]]; then
    docker inspect --format '{{.Config.Image}} {{.Image}}' "$container" > "$record_dir/$service.previous"
  fi
done

"${compose[@]}" pull frontend backend
"${compose[@]}" up -d --no-recreate --wait postgres redis
"${compose[@]}" exec -T postgres sh -ec 'exec pg_dump --format=custom --username "$POSTGRES_USER" --dbname "$POSTGRES_DB"' > "$record_dir/postgres.dump.partial"
test -s "$record_dir/postgres.dump.partial"
"${compose[@]}" exec -T postgres pg_restore --list < "$record_dir/postgres.dump.partial" > /dev/null
mv -- "$record_dir/postgres.dump.partial" "$record_dir/postgres.dump"

"${compose[@]}" run --rm --no-deps backend python manage.py migrate --noinput
"${compose[@]}" run --rm --no-deps backend python manage.py collectstatic --noinput
"${compose[@]}" up -d --no-build --wait

base_url=${TURTL_BASE_URL%/}
curl --fail --silent --show-error --max-time 15 --retry 3 "$base_url/" -o "$record_dir/frontend.html"
grep -Fq 'id="app"' "$record_dir/frontend.html"
curl --fail --silent --show-error --max-time 15 --retry 3 "$base_url/django-admin/login/" -o "$record_dir/backend.html"
grep -Fq 'name="csrfmiddlewaretoken"' "$record_dir/backend.html"
rm -- "$record_dir/frontend.html" "$record_dir/backend.html"

printf 'frontend=%s\nbackend=%s\n' "$TURTL_FRONTEND_IMAGE" "$TURTL_BACKEND_IMAGE" > "$record_dir/images.deployed"
echo 'Deployment passed the frontend and backend checks.'
