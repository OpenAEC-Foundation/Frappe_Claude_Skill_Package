# Deployment Workflows

## Workflow 1: Fresh Traditional Production Deployment

```
1. Provision server (Ubuntu 22.04 LTS recommended)
   |
2. Create frappe user (NEVER use root)
   $ sudo adduser frappe
   $ sudo usermod -aG sudo frappe
   |
3. Install system dependencies
   $ sudo apt install python3-dev python3-pip redis-server
   $ sudo apt install mariadb-server nginx supervisor
   $ sudo apt install nodejs npm (v18.x)
   $ sudo npm install -g yarn
   |
4. Configure MariaDB
   $ sudo mysql_secure_installation
   Set character-set-server=utf8mb4
   |
5. Install bench as frappe user
   $ sudo pip3 install frappe-bench
   $ bench init frappe-bench --frappe-branch version-15
   |
6. Create site and install apps
   $ bench new-site erp.example.com
   $ bench get-app erpnext --branch version-15
   $ bench --site erp.example.com install-app erpnext
   |
7. Setup production
   $ sudo bench setup production frappe
   |
8. Verify
   $ sudo supervisorctl status (all RUNNING)
   $ sudo nginx -t (syntax ok)
   |
9. Enable DNS multitenancy (if multi-site)
   $ bench config dns_multitenant on
   $ bench setup nginx
   |
10. Enable SSL
    $ sudo -H bench setup lets-encrypt erp.example.com
    |
11. Harden security
    $ sudo ufw enable (allow 22, 80, 443 only)
    $ Disable root SSH login
    $ Install fail2ban
```

## Workflow 2: Docker Production Deployment

```
1. Provision server with Docker + Docker Compose v2
   |
2. Clone frappe_docker
   $ git clone https://github.com/frappe/frappe_docker.git
   $ cd frappe_docker
   |
3. Configure environment
   $ cp example.env .env
   Edit .env: DB_ROOT_PASSWORD, SITE_NAME, etc.
   |
4. Start services
   $ docker compose -f compose.yaml up -d
   |
5. Create site
   $ docker compose exec backend \
       bench new-site erp.example.com \
       --db-root-password $DB_ROOT_PASSWORD \
       --admin-password $ADMIN_PASSWORD
   |
6. Install apps
   $ docker compose exec backend \
       bench --site erp.example.com install-app erpnext
   |
7. Add reverse proxy (Traefik or external Nginx)
   Use compose override for SSL termination
   |
8. Verify
   $ docker compose ps (all healthy)
   $ curl -I https://erp.example.com
```

## Workflow 3: Adding a New Site (Multi-Tenancy)

```
Prerequisites: DNS multitenancy enabled, production running

1. Point DNS A record to server IP
   site2.example.com -> 203.0.113.10
   |
2. Create site
   $ bench new-site site2.example.com \
       --db-root-password $DB_ROOT_PASSWORD \
       --admin-password $ADMIN_PASSWORD
   |
3. Install apps
   $ bench --site site2.example.com install-app erpnext
   |
4. Regenerate nginx config
   $ bench setup nginx
   $ sudo systemctl reload nginx
   |
5. Setup SSL for new site
   $ sudo -H bench setup lets-encrypt site2.example.com
   |
6. Verify
   $ curl -I https://site2.example.com
```

## Workflow 4: Zero-Downtime Update (Traditional)

```
1. Backup current state
   $ bench backup --with-files
   |
2. Put site in maintenance mode (optional, for major updates)
   $ bench --site mysite.com set-maintenance-mode on
   |
3. Pull updates
   $ bench update --pull --patch --build --requirements
   |
4. Verify processes restarted
   $ sudo supervisorctl status
   |
5. Disable maintenance mode
   $ bench --site mysite.com set-maintenance-mode off
   |
6. Smoke test
   Visit https://mysite.com and verify key functions
```

## Workflow 5: Zero-Downtime Update (Docker)

```
1. Backup
   $ docker compose exec backend bench backup --with-files
   |
2. Pull new images
   $ docker compose pull
   |
3. Recreate services (rolling)
   $ docker compose up -d --no-deps backend websocket queue-short queue-long
   |
4. Run migrations
   $ docker compose exec backend bench --site mysite.com migrate
   |
5. Rebuild frontend if needed
   $ docker compose up -d --no-deps --build frontend
   |
6. Verify
   $ docker compose ps
   $ curl -I https://mysite.com
```
