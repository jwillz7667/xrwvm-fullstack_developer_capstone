"""Generate the Kubernetes template; rendered values are supplied by the lab script."""
import json
from pathlib import Path

items = []
def add(kind, name, spec, api='v1'):
    items.append({'apiVersion': api, 'kind': kind, 'metadata': {'name': name, 'labels': {'project': 'openroad-capstone'}}, 'spec': spec})
def secret(key):
    return {'secretKeyRef': {'name': 'openroad-secrets', 'key': key}}
def env(name, value=None, key=None):
    return {'name': name, **({'valueFrom': secret(key)} if key else {'value': value})}
def deployment(name, image, port, variables, memory, mount=None, probe='/healthz', args=None):
    container = {'name': name, 'image': image, 'ports': [{'containerPort': port}], 'env': variables,
      'resources': {'requests': {'cpu': '10m', 'memory': memory}, 'limits': {'cpu': '250m', 'memory': memory}},
      'securityContext': {'allowPrivilegeEscalation': False, 'capabilities': {'drop': ['ALL']}}}
    pod = {'containers': [container]}
    if args:
        container['args'] = args
    if probe:
        container['readinessProbe'] = {'httpGet': {'path': probe, 'port': port, 'httpHeaders': [{'name': 'Host', 'value': 'localhost'}]}, 'initialDelaySeconds': 10, 'periodSeconds': 10}
        container['livenessProbe'] = {'httpGet': {'path': probe, 'port': port, 'httpHeaders': [{'name': 'Host', 'value': 'localhost'}]}, 'initialDelaySeconds': 60, 'periodSeconds': 20}
    if mount:
        container['volumeMounts'] = [{'name': 'data', 'mountPath': mount}]
        pod['volumes'] = [{'name': 'data', 'persistentVolumeClaim': {'claimName': name+'-data'}}]
    add('Deployment', name, {'replicas': 1, 'strategy': {'type': 'Recreate'}, 'selector': {'matchLabels': {'app': name}}, 'template': {'metadata': {'labels': {'app': name, 'project': 'openroad-capstone'}}, 'spec': pod}}, 'apps/v1')
    add('Service', name, {'selector': {'app': name}, 'ports': [{'port': port, 'targetPort': port}]})
for name in ['openroad-mongo', 'openroad-web']:
    add('PersistentVolumeClaim', name+'-data', {'accessModes': ['ReadWriteOnce'], 'resources': {'requests': {'storage': '1Gi'}}})
deployment('openroad-mongo', 'mongo:8.0', 27017, [env('MONGO_INITDB_ROOT_USERNAME', 'openroad'), env('MONGO_INITDB_ROOT_PASSWORD', key='MONGO_PASSWORD')], '768Mi', '/data/db', probe=None, args=['--wiredTigerCacheSizeGB', '0.25'])
deployment('openroad-dealers', '${DEALERS_IMAGE}', 3030, [env('MONGODB_URI', key='MONGODB_URI'), env('SERVICE_KEY', key='SERVICE_KEY')], '128Mi')
deployment('openroad-web', '${WEB_IMAGE}', 8000, [env('DJANGO_SECRET_KEY', key='DJANGO_SECRET_KEY'), env('SERVICE_KEY', key='SERVICE_KEY'), env('BACKEND_URL', 'http://openroad-dealers:3030'), env('SENTIMENT_URL', '${SENTIMENT_URL}'), env('ALLOWED_HOSTS', '${APP_HOST},localhost,127.0.0.1'), env('CSRF_TRUSTED_ORIGINS', 'https://${APP_HOST}'), env('SECURE_COOKIES','1'), env('TRUST_HTTPS_PROXY','1'), env('GUNICORN_CMD_ARGS','--no-control-socket')], '256Mi', '/data')
for name, source, port in [('openroad-mongo','openroad-dealers',27017), ('openroad-dealers','openroad-web',3030)]:
    add('NetworkPolicy', name, {'podSelector': {'matchLabels': {'app': name}}, 'policyTypes': ['Ingress'], 'ingress': [{'from': [{'podSelector': {'matchLabels': {'app': source}}}], 'ports': [{'protocol': 'TCP', 'port': port}]}]}, 'networking.k8s.io/v1')
Path('server/deployment.yaml').write_text(json.dumps({'apiVersion': 'v1', 'kind': 'List', 'items': items}, indent=2)+'\n')
