FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && useradd --uid 10001 --create-home appuser
COPY --chown=appuser:appuser app.py ./
COPY --chown=appuser:appuser sentiment ./sentiment
USER appuser
EXPOSE 5050
CMD ["gunicorn", "--bind", "0.0.0.0:5050", "--workers", "2", "--timeout", "30", "app:app"]
