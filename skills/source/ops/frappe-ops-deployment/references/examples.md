# Deployment Examples

## Complete Traditional Production Setup Script

```bash
#!/bin/bash
# production-setup.sh — Full Frappe/ERPNext production deployment
# Run as non-root user with sudo privileges

set -e

FRAPPE_USER=$(whoami)
BENCH_DIR="$HOME/frappe-bench"
SITE_NAME="erp.example.com"
FRAPPE_BRANCH="version-15"
ERPNEXT_BRANCH="version-15"

# 1. System dependencies (Ubuntu 22.04)
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3-dev python3-pip python3-venv \
    redis-server mariadb-server mariadb-client \
    nginx supervisor curl git \
    libffi-dev libssl-dev libjpeg-dev \
    xvfb libfontconfig wkhtmltopdf

# 2. Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
sudo npm install -g yarn

# 3. MariaDB configuration
sudo mysql -e "ALTER USER 'root'@'localhost' IDENTIFIED BY 'your_db_root_password';"
sudo mysql -e "FLUSH PRIVILEGES;"

# 4. Install bench
sudo pip3 install frappe-bench

# 5. Initialize bench
bench init $BENCH_DIR --frappe-branch $FRAPPE_BRANCH
cd $BENCH_DIR

# 6. Create site
bench new-site $SITE_NAME \
    --db-root-password your_db_root_password \
    --admin-password your_admin_password

# 7. Install ERPNext
bench get-app erpnext --branch $ERPNEXT_BRANCH
bench --site $SITE_NAME install-app erpnext

# 8. Production setup
sudo bench setup production $FRAPPE_USER

# 9. SSL
bench config dns_multitenant on
bench setup nginx
sudo systemctl reload nginx
sudo -H bench setup lets-encrypt $SITE_NAME

# 10. Firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

echo "Deployment complete: https://$SITE_NAME"
```

## Docker Production Compose (Complete)

```yaml
# docker-compose.yml — Production Frappe/ERPNext
version: "3.8"

services:
  configurator:
    image: frappe/erpnext:v15
    command: >
      bash -c "
        bench set-config -g db_host db;
        bench set-config -g db_port 3306;
        bench set-config -g redis_cache redis://redis-cache:6379;
        bench set-config -g redis_queue redis://redis-queue:6379;
      "
    volumes:
      - sites:/home/frappe/frappe-bench/sites

  backend:
    image: frappe/erpnext:v15
    volumes:
      - sites:/home/frappe/frappe-bench/sites
    depends_on:
      configurator:
        condition: service_completed_successfully

  frontend:
    image: frappe/erpnext:v15
    command: nginx-entrypoint.sh
    environment:
      BACKEND: backend:8000
      SOCKETIO: websocket:9000
      FRAPPE_SITE_NAME_HEADER: $$host
      UPSTREAM_REAL_IP_ADDRESS: 127.0.0.1
      PROXY_READ_TIMEOUT: 120
      CLIENT_MAX_BODY_SIZE: 50m
    volumes:
      - sites:/home/frappe/frappe-bench/sites
    ports:
      - "8080:8080"
    depends_on:
      - backend
      - websocket

  websocket:
    image: frappe/erpnext:v15
    command: ["node", "/home/frappe/frappe-bench/apps/frappe/socketio.js"]
    volumes:
      - sites:/home/frappe/frappe-bench/sites
    depends_on:
      - backend

  queue-short:
    image: frappe/erpnext:v15
    command: bench worker --queue short,default
    volumes:
      - sites:/home/frappe/frappe-bench/sites
    depends_on:
      - backend

  queue-long:
    image: frappe/erpnext:v15
    command: bench worker --queue long
    volumes:
      - sites:/home/frappe/frappe-bench/sites
    depends_on:
      - backend

  scheduler:
    image: frappe/erpnext:v15
    command: bench schedule
    volumes:
      - sites:/home/frappe/frappe-bench/sites
    depends_on:
      - backend

  db:
    image: mariadb:10.11
    command: --character-set-server=utf8mb4 --collation-server=utf8mb4_unicode_ci
    environment:
      MYSQL_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
    volumes:
      - db-data:/var/lib/mysql

  redis-cache:
    image: redis:7-alpine

  redis-queue:
    image: redis:7-alpine

volumes:
  sites:
  db-data:
```

## Nginx Reverse Proxy with External SSL (Traefik)

```yaml
# docker-compose.override.yml — Add Traefik for SSL termination
services:
  frontend:
    ports: []  # Remove direct port mapping
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.erpnext.rule=Host(`erp.example.com`)"
      - "traefik.http.routers.erpnext.entrypoints=websecure"
      - "traefik.http.routers.erpnext.tls.certresolver=letsencrypt"
      - "traefik.http.services.erpnext.loadbalancer.server.port=8080"

  traefik:
    image: traefik:v2.10
    command:
      - "--providers.docker=true"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - letsencrypt:/letsencrypt

volumes:
  letsencrypt:
```

## Multi-Site Nginx Config (Generated by bench)

```nginx
# This is auto-generated by bench setup nginx
# NEVER edit directly — changes are overwritten

upstream frappe-bench-frappe {
    server 127.0.0.1:8000 fail_timeout=0;
}

upstream frappe-bench-socketio-server {
    server 127.0.0.1:9000 fail_timeout=0;
}

server {
    listen 80;
    server_name site1.example.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    server_name site1.example.com;

    ssl_certificate     /etc/letsencrypt/live/site1.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/site1.example.com/privkey.pem;

    # Proxy to gunicorn
    location / {
        proxy_pass http://frappe-bench-frappe;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket proxy
    location /socket.io {
        proxy_pass http://frappe-bench-socketio-server;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Static files
    location /assets {
        alias /home/frappe/frappe-bench/sites/assets;
        expires 1y;
        add_header Cache-Control "public";
    }
}
```

## Supervisor Config (Generated by bench)

```ini
; Auto-generated by bench setup supervisor
[program:frappe-bench-frappe-web]
command=/home/frappe/frappe-bench/env/bin/gunicorn -b 127.0.0.1:8000 -w 4 --timeout 120 frappe.app:application
priority=4
autostart=true
autorestart=true
user=frappe
directory=/home/frappe/frappe-bench/sites

[program:frappe-bench-frappe-worker-short]
command=bench worker --queue short
priority=4
autostart=true
autorestart=true
user=frappe
directory=/home/frappe/frappe-bench

[program:frappe-bench-frappe-worker-default]
command=bench worker --queue default
priority=4
autostart=true
autorestart=true
user=frappe
directory=/home/frappe/frappe-bench

[program:frappe-bench-frappe-worker-long]
command=bench worker --queue long
priority=4
autostart=true
autorestart=true
user=frappe
directory=/home/frappe/frappe-bench

[program:frappe-bench-frappe-schedule]
command=bench schedule
priority=3
autostart=true
autorestart=true
user=frappe
directory=/home/frappe/frappe-bench

[program:frappe-bench-node-socketio]
command=node /home/frappe/frappe-bench/apps/frappe/socketio.js
priority=4
autostart=true
autorestart=true
user=frappe
directory=/home/frappe/frappe-bench

[program:frappe-bench-redis-cache]
command=redis-server /home/frappe/frappe-bench/config/redis_cache.conf
priority=1
autostart=true
autorestart=true
user=frappe

[program:frappe-bench-redis-queue]
command=redis-server /home/frappe/frappe-bench/config/redis_queue.conf
priority=1
autostart=true
autorestart=true
user=frappe

[group:frappe-bench-web]
programs=frappe-bench-frappe-web,frappe-bench-node-socketio

[group:frappe-bench-workers]
programs=frappe-bench-frappe-worker-short,frappe-bench-frappe-worker-default,frappe-bench-frappe-worker-long,frappe-bench-frappe-schedule

[group:frappe-bench-redis]
programs=frappe-bench-redis-cache,frappe-bench-redis-queue
```
