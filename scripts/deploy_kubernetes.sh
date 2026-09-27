#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p evidence .cloud-state
exec > >(tee -a evidence/kubernetes-deployment.log) 2>&1
TASK_NAMESPACE="$(kubectl config view --minify -o 'jsonpath={..namespace}')"
case "$TASK_NAMESPACE" in sn-labs-*) ;; *) echo 'Use the enrolled Skills Network Kubernetes lab.'; exit 1;; esac
: "${SENTIMENT_URL:?Set the verified Code Engine sentiment HTTPS URL}"
: "${APP_HOST:?Set the exact hostname from the lab Launch Application URL}"
export SENTIMENT_URL APP_HOST
python3 - <<'PY'
import os,re,urllib.parse
u=urllib.parse.urlsplit(os.environ['SENTIMENT_URL'])
assert u.scheme=='https' and u.hostname.endswith('.appdomain.cloud') and not u.query and not u.fragment
assert re.fullmatch(r'[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:labs|proxy)\.cognitiveclass\.ai',os.environ['APP_HOST'])
PY
if [[ ! -e .cloud-state/owned ]]; then
 for TASK_RESOURCE in deployment/openroad-web deployment/openroad-mongo deployment/openroad-dealers secret/openroad-secrets; do
  if kubectl get "$TASK_RESOURCE" >/dev/null 2>&1; then echo "Existing $TASK_RESOURCE requires inspection; stopping."; exit 1; fi
 done
 touch .cloud-state/owned
fi
if ! kubectl get secret openroad-secrets >/dev/null 2>&1; then
 umask 077
 python3 - <<'PY'
import secrets
from pathlib import Path
pw=secrets.token_hex(32)
values={'MONGO_PASSWORD':pw,'MONGODB_URI':f'mongodb://openroad:{pw}@openroad-mongo:27017/openroad?authSource=admin','SERVICE_KEY':secrets.token_urlsafe(48),'DJANGO_SECRET_KEY':secrets.token_urlsafe(64)}
Path('.cloud-secrets').write_text(''.join(f'{k}={v}\n' for k,v in values.items()))
PY
 kubectl create secret generic openroad-secrets --from-env-file=.cloud-secrets
 rm .cloud-secrets
fi
TASK_REVISION="$(git rev-parse "${IMAGE_REVISION:-HEAD}^{commit}")"
# Packaging-only changes may reuse images, but application code must be identical.
git diff --quiet "$TASK_REVISION" HEAD -- server ':!server/deployment.yaml' || { echo 'Image revision differs from application source.'; exit 1; }
TASK_TAG="$(git rev-parse --short "$TASK_REVISION")"
for TASK_PART in web dealers; do
 TASK_DIR=server
 [[ "$TASK_PART" = dealers ]] && TASK_DIR=server/database
 TASK_IMAGE="us.icr.io/$TASK_NAMESPACE/openroad-$TASK_PART:$TASK_TAG"
 if [[ "$(docker image inspect --format='{{index .Config.Labels "org.opencontainers.image.revision"}}' "$TASK_IMAGE" 2>/dev/null || true)" != "$TASK_REVISION" ]]; then
  docker build --label "org.opencontainers.image.revision=$TASK_REVISION" -t "$TASK_IMAGE" "$TASK_DIR"
 else
  echo "Using verified prebuilt image for source commit $TASK_REVISION: $TASK_IMAGE"
 fi
 docker push "$TASK_IMAGE" | tee "evidence/push-$TASK_PART.txt"
 docker inspect --format='{{index .RepoDigests 0}}' "$TASK_IMAGE" > ".cloud-state/$TASK_PART.image"
done
export WEB_IMAGE="$(cat .cloud-state/web.image)" DEALERS_IMAGE="$(cat .cloud-state/dealers.image)"
python3 - <<'PY'
import json,os,string
from pathlib import Path
text=string.Template(Path('server/deployment.yaml').read_text()).substitute({k:os.environ[k] for k in ['WEB_IMAGE','DEALERS_IMAGE','SENTIMENT_URL','APP_HOST']})
manifest=json.loads(text)
if os.environ.get('LAB_EPHEMERAL') == '1':
 # The enrolled sandbox has zero PVC quota and does not permit network policies.
 manifest['items']=[item for item in manifest['items'] if item['kind'] not in {'PersistentVolumeClaim','NetworkPolicy'}]
 for item in manifest['items']:
  if item['kind']=='Deployment':
   pod=item['spec']['template']['spec']
   for volume in pod.get('volumes',[]):
    if 'persistentVolumeClaim' in volume:
     del volume['persistentVolumeClaim']
     volume['emptyDir']={'sizeLimit':'1Gi'}
   if pod.get('volumes'):
    pod['securityContext']={'fsGroup':10001}
 print('Temporary course-lab storage enabled; data lasts for the lifetime of each pod.')
Path('evidence/deployment.yaml').write_text(json.dumps(manifest,indent=2)+'\n')
PY
kubectl apply -f evidence/deployment.yaml
for TASK_DEPLOYMENT in openroad-mongo openroad-dealers openroad-web; do
 kubectl rollout status "deployment/$TASK_DEPLOYMENT" --timeout=600s
done
kubectl get deployment,pods,svc,pvc -l project=openroad-capstone | tee evidence/24-kubernetes-deployment.txt
printf 'https://%s\n' "$APP_HOST" > evidence/deploymentURL
# The lab HTTPS proxy reaches this loopback port; no public database or backend route is created.
if ! curl -fsS http://127.0.0.1:8000/healthz >/dev/null; then
 nohup kubectl port-forward deployment/openroad-web 8000:8000 > evidence/port-forward.log 2>&1 < /dev/null &
 echo "$!" > .cloud-state/forward.pid
fi
for TASK_TRY in $(seq 1 30); do
 if curl -fsS http://127.0.0.1:8000/healthz > evidence/24-live-health.json; then break; fi
 sleep 2
done
python3 - <<'PY'
import json
assert json.load(open('evidence/24-live-health.json'))['status']=='ok'
PY
printf '\nKUBERNETES DEPLOYMENT HEALTHY\n'
cat evidence/deploymentURL
