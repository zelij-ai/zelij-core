# Zelij Core : le bureau et les agents, un seul conteneur ; le schéma se crée au démarrage.
# Le processus tourne sans privilège (utilisateur `core`), le système de fichiers de l'image est en lecture seule (voir compose).
FROM python:3.13-slim
WORKDIR /srv/app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 CORE_ENV=production HOME=/home/core
RUN apt-get update && apt-get install -y --no-install-recommends openssh-client postgresql-client ca-certificates && rm -rf /var/lib/apt/lists/* \
    && groupadd -r -g 10001 core && useradd -r -u 10001 -g core -d /home/core -s /usr/sbin/nologin core \
    && mkdir -p /home/core /data/sauvegardes /srv/app/modules && chown -R core:core /home/core /data /srv/app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY --chown=core:core core ./core
COPY --chown=core:core agents ./agents
COPY --chown=core:core portraits ./portraits
USER core
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=5 CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=4)"
# Les en-têtes X-Forwarded-* ne sont crus que s'ils viennent d'une adresse de FORWARDED_ALLOW_IPS (lue par uvicorn ; par défaut
# la boucle locale seulement). docker-compose.tls.yml y met le réseau du serveur Caddy : personne d'autre ne peut se dire « l'adresse du visiteur ».
CMD ["sh", "-c", "python -m core.schema && uvicorn core.bureau.app:app --host 0.0.0.0 --port 8000 --proxy-headers"]
