#!/bin/sh
# Ponto de entrada do contêiner: prepara o banco e sobe o servidor de aplicação.
# Idempotente: roda a cada reinício sem duplicar dados (cada passo confere antes).
set -eu

# Bancos criados antes de 18/10/2026 guardam nomes antigos de migração;
# o reparo é idempotente e precisa vir ANTES do migrate.
python manage.py reparar_historico_migracoes

# Cria/atualiza as tabelas no volume /data (banco novo na primeira subida).
python manage.py migrate --noinput

# Carga inicial com os dados que já existiam no repositório original; só roda
# se o banco estiver vazio.
python manage.py semear_dados_iniciais

# Conta técnica do Django (/admin/) a partir de DJANGO_SUPERUSER_*; e o
# administrador do MERCADO a partir de MERCADO_ADMIN_*. Nenhum dos dois faz
# nada se faltar variável ou se o usuário já existir.
python manage.py criar_admin_inicial
python manage.py criar_administrador_do_mercado

# `exec` troca o shell pelo gunicorn: o contêiner recebe SIGTERM direto no
# servidor e para rápido. PORT vem do Cloud Run; na stack fica 8000.
exec gunicorn config.wsgi:application \
  --bind "0.0.0.0:${PORT:-8000}" \
  --workers "${GUNICORN_WORKERS:-2}" \
  --access-logfile - \
  --error-logfile -
