# CORIC_AGRAR — Nginx reverse proxy image (production)
# Story 9.1: stabilna alpine bazna slika + naš conf.d/default.conf.
FROM nginx:1.27-alpine

# Ukloni default welcome konfiguraciju (default.conf sa "Welcome to nginx").
RUN rm -f /etc/nginx/conf.d/default.conf

# Naš config ide u conf.d/ — bazni /etc/nginx/nginx.conf ga uključuje
# unutar `http {}` bloka (`include /etc/nginx/conf.d/*.conf;`), pa upstream/server
# direktive iz nginx.conf-a su validne (http-kontekst).
COPY compose/nginx/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80 443
