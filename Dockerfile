FROM python:3.12-slim

# Sem .pyc na imagem; logs saem na hora (sem buffer) para o Portainer mostrar;
# o banco fica no volume /data (ver docker-compose.yml).
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DJANGO_DB_PATH=/data/db.sqlite3

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# collectstatic só precisa importar o settings: a chave abaixo é descartável e
# não fica configurada no contêiner (o ENTRYPOINT exige DJANGO_SECRET_KEY real).
RUN DJANGO_SECRET_KEY=apenas-para-collectstatic-nao-e-segredo DJANGO_DEBUG=1 \
    python manage.py collectstatic --noinput \
 && chmod +x bin/*.sh \
 && useradd --create-home --uid 1000 mercado \
 && mkdir -p /data \
 && chown -R mercado:mercado /app /data

# Processo sem root: uma falha na app não vira root dentro do contêiner.
USER mercado

VOLUME ["/data"]

EXPOSE 8000

ENTRYPOINT ["/app/bin/iniciar-container.sh"]
