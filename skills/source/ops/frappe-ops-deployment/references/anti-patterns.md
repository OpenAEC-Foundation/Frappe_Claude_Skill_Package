# Deployment Anti-Patterns

## 1. Running bench as root

```bash
# WRONG — creates permission issues, security risk
sudo bench init frappe-bench
sudo bench new-site mysite.com

# CORRECT — ALWAYS use a dedicated non-root user
sudo adduser frappe
su - frappe
bench init frappe-bench
```

**Why**: Running as root means all files are owned by root. Supervisor/gunicorn workers running as root is a critical security vulnerability.

## 2. Exposing internal ports to the internet

```bash
# WRONG — Redis, MariaDB, gunicorn directly accessible
sudo ufw allow 3306/tcp   # MariaDB
sudo ufw allow 6379/tcp   # Redis
sudo ufw allow 8000/tcp   # Gunicorn

# CORRECT — only expose HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow ssh
```

**Why**: Redis has no authentication by default. MariaDB exposed = database breach. Gunicorn should ALWAYS be behind Nginx.

## 3. Forgetting to disable default nginx site

```bash
# WRONG — default nginx config conflicts with Frappe on port 80
bench setup nginx
sudo systemctl reload nginx
# ERROR: port 80 already in use

# CORRECT — disable default site first
sudo rm /etc/nginx/sites-enabled/default
sudo rm -f /etc/nginx/conf.d/default.conf
bench setup nginx
sudo systemctl reload nginx
```

## 4. Editing generated nginx/supervisor configs directly

```nginx
# WRONG — editing config/nginx.conf manually
# These changes are OVERWRITTEN by next bench setup nginx

# CORRECT — use bench config or site_config.json
bench set-config ssl_certificate "/path/to/cert.pem"
bench set-config ssl_certificate_key "/path/to/key.pem"
bench setup nginx  # Regenerates with your settings
```

## 5. Skipping DNS multitenancy for multi-site

```bash
# WRONG — creating multiple sites without DNS multitenancy
bench new-site site1.com
bench new-site site2.com
# Both sites unreachable — nginx doesn't know which to serve

# CORRECT — enable DNS multitenancy BEFORE creating sites
bench config dns_multitenant on
bench new-site site1.com
bench new-site site2.com
bench setup nginx
sudo systemctl reload nginx
```

## 6. No SSL in production

```bash
# WRONG — serving ERPNext over plain HTTP
# All passwords, session tokens, and business data transmitted in cleartext

# CORRECT — ALWAYS enable SSL
sudo -H bench setup lets-encrypt mysite.com
# Free, automatic renewal, no excuse to skip
```

## 7. Running bench update without --backup

```bash
# WRONG — updating without safety net
bench update

# CORRECT — ALWAYS backup before update
bench backup --with-files
bench update --pull --patch --build --requirements
```

## 8. Docker: Using bind mounts instead of named volumes

```yaml
# WRONG — data loss if container path changes
volumes:
  - ./sites:/home/frappe/frappe-bench/sites

# CORRECT — named volumes persist independently
volumes:
  sites:
    driver: local
```

## 9. Not setting MariaDB character set

```bash
# WRONG — default character set causes emoji/unicode issues
# MariaDB installed with default latin1

# CORRECT — ALWAYS configure utf8mb4
# /etc/mysql/mariadb.conf.d/50-server.cnf
[mysqld]
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

[mysql]
default-character-set = utf8mb4
```

## 10. Ignoring Redis security in multi-bench setups

```bash
# WRONG — multiple benches sharing Redis without auth
# One bench can read/write another bench's cache

# CORRECT — create RQ users with authentication
bench create-rq-users --set-admin-password
# Each bench gets unique Redis credentials
```
