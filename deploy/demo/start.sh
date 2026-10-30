#!/bin/sh
set -eu
# S3Mock uses a minimal image with no healthcheck client. Seeding uploads
# receipts, so it also verifies storage readiness before starting the app.
attempt=0
until cashflow-seed -if-empty; do
  attempt=$((attempt + 1))
  if [ "$attempt" -ge 30 ]; then
    echo "Demo initialization failed after 30 attempts" >&2
    exit 1
  fi
  sleep 2
done
exec cashflow
