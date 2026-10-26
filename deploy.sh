#!/bin/bash
# Put the latest GitHub version live on peaccion.com: pulls on the server and restarts the app.
# The server only gets what is pushed to GitHub, so commit and push first.
set -euo pipefail
cd "$(dirname "$0")"

GCLOUD=$(command -v gcloud || echo /usr/local/share/google-cloud-sdk/bin/gcloud)

if [ -n "$(git status --porcelain -- '*.py' '*.js' requirements.txt)" ]; then
    echo "⚠️  You have code changes that aren't committed; they won't be deployed."
fi
if [ -n "$(git log --oneline '@{u}..' 2>/dev/null)" ]; then
    echo "⚠️  You have commits that aren't pushed to GitHub; they won't be deployed:"
    git log --oneline '@{u}..'
fi

"$GCLOUD" compute ssh --zone "us-west1-a" "instance-20250917-041530" --project "leafy-clone-472404-d1" \
    --command "sudo /usr/local/bin/autumn-deploy"
