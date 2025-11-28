# DeceptiCloud Enhanced Deception System

## 🎭 Overview

A production-ready, AI-powered adaptive deception system for honeypots that uses behavioral analysis, skill level detection, and dynamic content generation to maximize attacker engagement and intelligence gathering.

## ✨ Key Features

- **🧠 Behavioral Analysis**: Tracks commands to identify attacker interests and skill levels
- **🎯 Adaptive Responses**: Generates contextually appropriate fake content
- **📊 Comprehensive Metrics**: Tracks engagement, effectiveness, and attacker profiling
- **🤖 RL Integration**: Enhances reinforcement learning rewards with deception metrics
- **☁️ AWS Ready**: Fully deployable on AWS with minimal additional cost
- **🐳 Docker Native**: Runs as a containerized service alongside honeypots

## 🚀 Quick Start

### 1. Deploy Locally

```bash
# Clone repository
git clone https://github.com/yourusername/decepticloud.git
cd decepticloud

# Run deployment script
chmod +x scripts/deploy_deception.sh
./scripts/deploy_deception.sh local
```

### 2. Test the System

```bash
# Connect to SSH honeypot
ssh root@localhost -p 2222

# Try these commands to trigger deception:
ls -la
cat .env
find / -name "password*"
grep -r "AWS" /home
```

### 3. Run Training

```bash
# Train RL agent with deception
python3 main_enhanced.py --mode local --episodes 10
```

### 4. View Results

```bash
# Check deception metrics
ls -lh data/deception/

# View effectiveness report
cat data/deception/deception_metrics_*.json | jq '.effectiveness_report'
```

## 📁 Project Structure

```
decepticloud/
├── src/
│   ├── deception/                      # Deception system modules
│   │   ├── adaptive_deception.py       # Behavioral analysis & skill detection
│   │   ├── content_generator.py        # Dynamic fake content generation
│   │   ├── deception_metrics.py        # Engagement tracking & profiling
│   │   ├── command_interceptor.py      # Command interception & response
│   │   └── cowrie_integration.py       # Cowrie honeypot integration
│   ├── enhanced_environment.py         # RL environment with deception
│   └── ...
├── docker/
│   └── Dockerfile.deception            # Deception service container
├── docker-compose.local.yml            # Local deployment (UPDATED)
├── scripts/
│   ├── deploy_deception.sh             # Deployment script
│   └── test_deception.py               # Test suite
├── data/
│   └── deception/                      # Deception data & metrics
├── DECEPTION_GUIDE.md                  # Comprehensive guide
├── DECEPTION_README.md                 # This file
└── main_enhanced.py                    # Enhanced training script
```

## 🎯 What Makes This Different

### Traditional Honeypots
- Static content
- Same responses for all attackers
- Limited engagement tracking
- No adaptation

### DeceptiCloud Enhanced Deception
- **Dynamic content** generated based on attacker behavior
- **Adaptive responses** tailored to skill level
- **Comprehensive metrics** tracking engagement and effectiveness
- **Real-time adaptation** to maximize dwell time
- **RL integration** for continuous improvement

## 📊 Features in Detail

### 1. Behavioral Analysis

Tracks every command and builds attacker profiles:

```python
Profile {
  skill_level: "advanced",          # novice | intermediate | advanced | expert
  interests: ["credentials", "financial"],
  command_count: 28,
  duration: 145.3 seconds
}
```

### 2. Dynamic Content Generation

Generates realistic fake content:

- **Credential files**: `.env`, SSH keys, AWS credentials, passwords
- **Financial data**: Payroll, invoices, transaction records
- **Configurations**: Database configs, nginx configs, app settings
- **System files**: Logs, backups, scripts

All content is:
- ✓ Contextually relevant
- ✓ Properly formatted
- ✓ Skill-level appropriate
- ✓ Internally consistent

### 3. Intelligent Command Responses

Intercepts and responds to:

| Command | Response |
|---------|----------|
| `ls` | Fake directory listings with breadcrumbs |
| `cat` | Contextually generated file content |
| `find` | Targeted fake file paths |
| `grep` | Realistic fake matches |
| `ps` | Fake process listings |
| `netstat` | Fake network connections |

### 4. Deception Metrics

Tracks comprehensive metrics:

**Engagement Tracking**
- Deception event count
- Commands with deception rate
- Engagement score (0-10)
- Dwell time analysis

**Effectiveness Scoring**
- Baseline vs. deception dwell time
- Improvement percentage
- Success rate by type
- ROI analysis

**Interest Profiling**
- What attackers search for
- Popularity distribution
- Temporal patterns

### 5. RL Integration

Enhances reinforcement learning:

```python
# Base reward function
+10: Attack matches honeypot type

# Deception bonuses
+0.5: Per deception event
+0.1 * engagement_score
+0.5: Per skill level detected
+1.0: For fooling advanced attackers
+2.0: For fooling expert attackers
```

## 🏗️ Architecture

```
Attacker → Cowrie → Deception Service → {
                                          Behavioral Analysis
                                          Content Generation
                                          Metrics Tracking
                                        } → Enhanced RL Rewards
```

## 📈 Metrics & Analytics

### Effectiveness Report

```json
{
  "dwell_time_analysis": {
    "avg_baseline_seconds": 45.2,
    "avg_with_deception_seconds": 145.8,
    "improvement_percentage": 222.6
  },
  "engagement_metrics": {
    "total_deception_events": 234,
    "avg_engagement_by_skill": {
      "novice": 3.2,
      "intermediate": 5.7,
      "advanced": 7.8,
      "expert": 9.1
    }
  }
}
```

### Session Profile

```json
{
  "session_id": "abc123",
  "ip": "192.168.1.100",
  "skill_level": "advanced",
  "interests": ["credentials", "system_info"],
  "duration": 145.3,
  "deception_events": 18,
  "deception_rate": 0.64,
  "engagement_score": 45.6
}
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
python3 scripts/test_deception.py

# Expected output:
[TEST] Adaptive Deception Engine
✓ Session profile: intermediate
✓ Interests: ['credentials']
✓ Commands: 3
✓ Adaptive Deception Engine: PASS

[TEST] Content Generator
✓ Generated directory listing: 856 characters
✓ Generated .env file: 1234 characters
✓ Content Generator: PASS

...

✓ ALL TESTS PASSED
```

## 🌐 AWS Deployment

### Deploy to AWS

```bash
# Set environment variables
export EC2_HOST="your-ec2-ip"
export EC2_KEY_FILE="path/to/key.pem"

# Or use SSM
export USE_SSM="true"
export SSM_INSTANCE_ID="i-xxxxx"

# Deploy
./scripts/deploy_deception.sh aws

# Run training
python3 main_enhanced.py --mode aws --episodes 20
```

### Cost Analysis

Additional monthly cost: **~$10**

- Compute: $7.20/mo (t3.micro, 24/7)
- Storage: $1.00/mo (10GB metrics)
- Transfer: $0.50/mo (typical honeypot traffic)

## 📚 Documentation

- **[DECEPTION_GUIDE.md](DECEPTION_GUIDE.md)** - Comprehensive guide (100+ pages)
  - Architecture details
  - Deployment instructions
  - Usage examples
  - Troubleshooting
  - Advanced topics

## 🔧 Configuration

### Deception Service Environment Variables

```bash
COWRIE_LOG_PATH=/cowrie/var/log/cowrie/cowrie.json
DECEPTION_DATA_DIR=/data/deception
PYTHONPATH=/app
```

### Docker Compose

```yaml
deception:
  build:
    context: .
    dockerfile: docker/Dockerfile.deception
  volumes:
    - ./data/cowrie/logs:/cowrie/var/log/cowrie:ro
    - ./data/deception:/data/deception
  environment:
    - COWRIE_LOG_PATH=/cowrie/var/log/cowrie/cowrie.json
    - DECEPTION_DATA_DIR=/data/deception
```

## 🎓 Examples

### Example 1: Basic Usage

```python
from src.deception.command_interceptor import CommandInterceptor

# Initialize
interceptor = CommandInterceptor('./data/deception')

# Process command
response, intercepted = interceptor.process_command(
    session_id='attacker-1',
    command='cat /home/ubuntu/.env',
    ip='192.168.1.100',
    username='root'
)

if intercepted:
    print(f"Deceptive response:\n{response}")
```

### Example 2: Get Metrics

```python
# Get effectiveness report
report = interceptor.get_metrics_report()

print(f"Dwell time improvement: {report['dwell_time_analysis']['improvement_percentage']:.1f}%")
print(f"Total deception events: {report['engagement_metrics']['total_deception_events']}")

# Export metrics
json_path = interceptor.export_metrics('json')
csv_path = interceptor.export_metrics('csv')
```

### Example 3: Custom Content

```python
from src.deception.content_generator import ContentGenerator

generator = ContentGenerator()

# Generate fake .env file
fake_env = generator.generate_file_content(
    filename='.env',
    interests=['credentials', 'financial'],
    skill_level='advanced'
)

print(fake_env)
# Output:
# DB_PASSWORD=S3cur3P@ssw0rd2024
# AWS_ACCESS_KEY_ID=AKIA...
# STRIPE_SECRET_KEY=sk_live_...
```

## 🤝 Contributing

Contributions welcome! Areas for improvement:

- Additional content templates
- More skill detection patterns
- SIEM integrations
- Visualization dashboards
- Additional honeypot integrations

## ⚠️ Security Considerations

- Never expose real credentials
- Keep honeypot isolated from production
- Monitor for honeytoken usage
- Regularly update Docker images
- Review generated content for accuracy

## 📄 License

See [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

Built on:
- [Cowrie](https://github.com/cowrie/cowrie) - SSH/Telnet honeypot
- PyTorch - Deep learning framework
- Docker - Containerization

## 📞 Support

- **Documentation**: [DECEPTION_GUIDE.md](DECEPTION_GUIDE.md)
- **Issues**: GitHub Issues
- **Email**: support@decepticloud.io

---

**Made with ❤️ for security researchers and honeypot operators**

**Ready for production deployment on AWS** ☁️
