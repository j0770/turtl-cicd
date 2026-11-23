#!/usr/bin/env bash
set -euo pipefail
umask 077

: "${STATE_DIRECTORY:?Set STATE_DIRECTORY to a writable deployment state directory}"
release_url=https://github.com/j0770/turtl-cicd/releases/latest/download/deployment.json
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)

exec 9>"$STATE_DIRECTORY/check-release.lock"
flock -n 9 || exit 0
candidate=$(mktemp "$STATE_DIRECTORY/deployment.XXXXXX")
trap 'rm -f -- "$candidate"' EXIT

curl --fail --silent --show-error --location --proto '=https' --proto-redir '=https' --connect-timeout 10 --max-time 30 "$release_url" -o "$candidate"

images=$(jq -ers '
  select(length == 1) | .[0]
  | select(.schema_version == 1 and (.commit | test("^[0-9a-f]{40}$")))
  | .images
  | select(.frontend | test("^ghcr[.]io/j0770/turtl-cicd-private/frontend@sha256:[0-9a-f]{64}$"))
  | select(.backend | test("^ghcr[.]io/j0770/turtl-cicd-private/backend@sha256:[0-9a-f]{64}$"))
  | [.frontend, .backend] | @tsv
' "$candidate")
IFS=$'\t' read -r frontend backend <<< "$images"

active="$STATE_DIRECTORY/deployment.json"
if [[ -f $active ]] && jq -e --arg frontend "$frontend" --arg backend "$backend" '
  .images.frontend == $frontend and .images.backend == $backend
' "$active" > /dev/null; then
  echo 'The latest released images are already deployed.'
  exit 0
fi

bash "$script_dir/deploy-ghcr.sh" "$frontend" "$backend"
mv -f -- "$candidate" "$active"
