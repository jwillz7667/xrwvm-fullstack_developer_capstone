FROM node:24-alpine AS frontend
WORKDIR /ui
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
FROM python:3.13-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 DATA_DIR=/data
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home appuser && mkdir /data && chown appuser /data
COPY --chown=appuser:appuser . ./
COPY --from=frontend --chown=appuser:appuser /ui/dist ./frontend/dist
RUN DJANGO_SECRET_KEY=build-only-not-used-at-runtime SERVICE_KEY=build-only-not-used-at-runtime ALLOWED_HOSTS=localhost python manage.py collectstatic --noinput
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py seed_catalog && exec gunicorn --bind 0.0.0.0:8000 --workers 2 --timeout 40 djangoproj.wsgi:application"]
