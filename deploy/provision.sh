#!/usr/bin/env bash
# Install on a dedicated Amazon Linux 2023 EC2 instance. Run with sudo.
set -Eeuo pipefail
if [ "$EUID" -ne 0 ]; then
  echo "Run this script as root (sudo bash deploy/provision.sh)." >&2
  exit 1
fi
SOURCE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
dnf install -y python3.11 python3.11-pip nginx

if ! id mangoapp >/dev/null 2>&1; then
  useradd --system --home-dir /var/lib/mango-todo --shell /sbin/nologin mangoapp
fi
install -d -o mangoapp -g mangoapp -m 0700 /var/lib/mango-todo
install -d -o root -g root -m 0755 /opt/mango-todo
install -m 0644 "$SOURCE_DIR/app.py" "$SOURCE_DIR/requirements.txt" /opt/mango-todo/
cp -r "$SOURCE_DIR/templates" "$SOURCE_DIR/static" /opt/mango-todo/
chown -R root:root /opt/mango-todo
chmod -R a+rX /opt/mango-todo
python3.11 -m venv /opt/mango-todo/venv
/opt/mango-todo/venv/bin/python -m pip install -r /opt/mango-todo/requirements.txt

if [ ! -f /etc/mango-todo.env ]; then
  umask 077
  {
    echo "APP_ENV=production"
    echo "DATABASE_PATH=/var/lib/mango-todo/tasks.sqlite3"
    /opt/mango-todo/venv/bin/python -c 'import secrets; print("SECRET_KEY=" + secrets.token_hex(32))'
  } > /etc/mango-todo.env
fi
chown root:root /etc/mango-todo.env
chmod 0600 /etc/mango-todo.env
install -m 0644 "$SOURCE_DIR/deploy/mango-todo.service" /etc/systemd/system/mango-todo.service
install -m 0644 "$SOURCE_DIR/deploy/nginx.conf" /etc/nginx/nginx.conf

# On hosts that enforce SELinux, allow Nginx to proxy to loopback.
# Do not disable SELinux to solve an upstream permission error.
if command -v getenforce >/dev/null && [ "$(getenforce)" = "Enforcing" ]; then
  setsebool -P httpd_can_network_connect 1
fi

nginx -t
systemctl daemon-reload
systemctl enable mango-todo nginx
systemctl restart mango-todo
systemctl restart nginx
curl --fail --silent --show-error --retry 20 --retry-connrefused --retry-all-errors --retry-delay 2 --max-time 10 http://127.0.0.1/health
echo
echo "Taskboard is ready. Verify the public HTTP link as well."
