#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p evidence
exec > >(tee -a evidence/sentiment-deployment.log) 2>&1
: "${SN_ICR_NAMESPACE:?Use the enrolled Skills Network Code Engine lab}"
case "$SN_ICR_NAMESPACE" in sn-labs-*) ;; *) exit 1;; esac
ibmcloud ce project current
if ! ibmcloud ce application get --name openroad-sentiment >/dev/null 2>&1; then
 ibmcloud ce application create --name openroad-sentiment --image "us.icr.io/$SN_ICR_NAMESPACE/openroad-sentiment" --registry-secret icr-secret --port 5050 --build-source https://github.com/jwillz7667/xrwvm-fullstack_developer_capstone.git --build-context-dir server/djangoapp/microservices --min-scale 0 --max-scale 1 --cpu 0.25 --memory 0.5G
fi
ibmcloud ce application get --name openroad-sentiment | tee evidence/16-sentiment-deployment.txt
ibmcloud ce application get --name openroad-sentiment --output url > evidence/sentiment.url
TASK_URL="$(cat evidence/sentiment.url)"
curl --fail --retry 5 --max-time 120 "$TASK_URL/analyze/Fantastic%20services." | tee evidence/16-sentiment-cloud.json
python3 - <<'PY'
import json
assert json.load(open('evidence/16-sentiment-cloud.json'))['sentiment']=='positive'
PY
printf '\nLIVE SENTIMENT CHECK PASSED\n%s\n' "$TASK_URL"
