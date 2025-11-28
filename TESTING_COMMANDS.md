# DeceptiCloud Testing Commands

## 1. Start Honeypots
```powershell
# Start both honeypots
docker-compose -f docker-compose.local.yml up -d

# Check status
docker ps --filter "name=honeypot_local"
```

## 2. Run RL Training
```powershell
# Basic training (5 episodes, 10 timesteps each)
python main_local.py --episodes 5 --timesteps 10

# Extended training
python main_local.py --episodes 10 --timesteps 15
```

## 3. Attack Simulation
```powershell
# Start enhanced attack simulator (3 minutes)
python scripts\enhanced_attack_simulator.py --duration 180

# Custom attack simulation
python scripts\enhanced_attack_simulator.py --target localhost --ssh-port 2222 --web-port 80 --duration 300
```

## 4. Manual Attack Testing
```powershell
# SSH attacks (try different credentials)
ssh root@localhost -p 2222
ssh admin@localhost -p 2222
ssh user@localhost -p 2222

# Web attacks
curl http://localhost/.env
curl http://localhost/admin
curl http://localhost/wp-admin
```

## 5. Combined Testing (Recommended)
```powershell
# Terminal 1: Start containers
docker-compose -f docker-compose.local.yml up -d

# Terminal 2: Start attack simulation
python scripts\enhanced_attack_simulator.py --duration 600

# Terminal 3: Run RL training
python main_local.py --episodes 8 --timesteps 12
```

## 6. Monitor System
```powershell
# Check container logs
docker logs cowrie_honeypot_local --tail 20
docker logs nginx_honeypot_local --tail 20

# Monitor in real-time
docker logs -f cowrie_honeypot_local
```

## 7. Quick Test Commands
```powershell
# Test SSH honeypot response
echo "Testing SSH..." && ssh -o ConnectTimeout=5 root@localhost -p 2222

# Test web honeypot response  
echo "Testing Web..." && curl -m 5 http://localhost/

# Check if containers are responding
docker exec cowrie_honeypot_local ps aux
docker exec nginx_honeypot_local nginx -t
```

## 8. Cleanup
```powershell
# Stop all containers
docker-compose -f docker-compose.local.yml down

# Remove containers
docker rm -f cowrie_honeypot_local nginx_honeypot_local
```

## 9. View Results
```powershell
# Check training results
type results\local_episodes.csv
type results\local_timesteps.csv

# View saved models
dir models\
```

## 10. One-Line Full Test
```powershell
docker-compose -f docker-compose.local.yml up -d && start /B python scripts\enhanced_attack_simulator.py --duration 120 && python main_local.py --episodes 3 --timesteps 8
```