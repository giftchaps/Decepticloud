# Local Testing Guide

This directory contains everything needed to test DeceptiCloud honeypots locally.

## Quick Start

```bash
# 1. Run setup (creates directories and content)
bash scripts/setup_local_test.sh

# 2. Start honeypots
docker-compose -f docker-compose.local.yml up -d

# 3. Test honeypots
python scripts/test_local_honeypots.py

# 4. View logs
docker-compose -f docker-compose.local.yml logs -f
```

## Access Honeypots

**SSH Honeypot (Cowrie):**
```bash
ssh -p 2222 root@localhost
# Try passwords: password, 123456, admin
```

**Web Honeypot:**
```bash
# In browser or curl
curl http://localhost:8080/
curl http://localhost:8080/.env
curl http://localhost:8080/robots.txt
```

## View Logs

**Cowrie logs (SSH attacks):**
```bash
docker logs cowrie_honeypot_local
cat data/cowrie/logs/cowrie.json
```

**nginx logs (web attacks):**
```bash
docker logs nginx_honeypot_local
cat data/nginx/logs/access.log
```

## Stop Honeypots

```bash
docker-compose -f docker-compose.local.yml down
```

## Clean Up

```bash
# Remove containers and volumes
docker-compose -f docker-compose.local.yml down -v

# Remove data directories
rm -rf data/
```
