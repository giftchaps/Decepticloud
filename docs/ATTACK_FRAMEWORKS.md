# Cloud Attack Frameworks for DeceptiCloud Testing

This document outlines well-known, documented autonomous attack frameworks for testing cloud honeynets. These tools enable realistic comparison between RL-based adaptive honeynets and traditional static honeynets.

## Overview

To validate DeceptiCloud's effectiveness, we need realistic attack traffic that mimics actual adversary behavior. The following frameworks are industry-standard tools used by security teams for adversary emulation and detection testing.

---

## 1. Stratus Red Team ⭐ (Recommended for DeceptiCloud)

**Website:** https://stratus-red-team.cloud/
**GitHub:** https://github.com/DataDog/stratus-red-team

### Description
"Atomic Red Team for the Cloud" - Granular, actionable adversary emulation specifically designed for cloud environments (AWS, Azure, GCP, Kubernetes).

### Why It's Ideal for DeceptiCloud
- **Cloud-Native**: Built specifically for AWS attack emulation
- **Automated**: Self-contained attack techniques with automatic infrastructure setup
- **MITRE ATT&CK Mapped**: Each attack maps to tactics (persistence, privilege escalation, etc.)
- **Detection-Focused**: Designed to test blue team detection capabilities
- **Terraform-Based**: Automatically manages attack infrastructure lifecycle

### Key Features
- 50+ attack techniques for AWS
- Automatic CloudTrail log generation
- Clean setup and teardown
- Detailed output showing expected telemetry
- Written in Go with Terraform integration

### Attack Techniques Relevant to Honeynets
```bash
# Instance/Compute attacks (triggers SSH honeypot)
stratus detonate aws.execution.ec2-launch-unusual-instances
stratus detonate aws.execution.ec2-user-data-script

# Web/API attacks (triggers web honeypot)
stratus detonate aws.initial-access.console-login-without-mfa
stratus detonate aws.discovery.ec2-enumerate-from-instance

# Persistence attacks
stratus detonate aws.persistence.iam-create-backdoor-role
stratus detonate aws.persistence.lambda-backdoor-function
```

### Installation
```bash
# Install Stratus Red Team
wget -q -O /tmp/stratus-red-team-linux-amd64.tar.gz https://github.com/DataDog/stratus-red-team/releases/latest/download/stratus-red-team_linux_amd64.tar.gz
tar -xzf /tmp/stratus-red-team-linux-amd64.tar.gz -C /usr/local/bin/
chmod +x /usr/local/bin/stratus

# Verify installation
stratus --version
```

### Integration with DeceptiCloud
See `src/advanced_attacker.py` for implementation examples.

---

## 2. CALDERA

**Website:** https://caldera.mitre.org/
**GitHub:** https://github.com/mitre/caldera

### Description
MITRE's automated adversary emulation platform for running autonomous breach-and-simulation exercises.

### Key Features
- **Autonomous Operations**: Can run multi-step attack chains without human intervention
- **Plugin Architecture**: Extensible with community plugins
- **Agent-Based**: Deploy agents on target systems for realistic C2 behavior
- **Planning Engine**: AI-driven attack path selection
- **MITRE ATT&CK Integration**: Direct mapping to adversary tactics

### Attack Capabilities
- Credential dumping
- Lateral movement
- Privilege escalation
- Data exfiltration
- Persistence mechanisms

### Use Cases for DeceptiCloud
- **Long-Running Campaigns**: Test honeypot effectiveness over extended periods
- **Adaptive Adversary**: CALDERA agents adapt to defenses, testing RL agent's response
- **Multi-Vector Attacks**: Simultaneous SSH and web exploitation

### Installation
```bash
git clone https://github.com/mitre/caldera.git --recursive
cd caldera
pip3 install -r requirements.txt
python3 server.py --insecure
```

### Integration Approach
Deploy CALDERA agents to continuously probe honeypots with realistic attack patterns.

---

## 3. Pacu (AWS Exploitation Framework)

**GitHub:** https://github.com/RhinoSecurityLabs/pacu
**Documentation:** https://rhinosecuritylabs.com/aws/pacu-open-source-aws-exploitation-framework/

### Description
The "Metasploit for AWS" - modular exploitation framework for offensive AWS security testing.

### Key Features
- **50+ Modules**: Covers reconnaissance, privilege escalation, persistence, exfiltration
- **Session Management**: Multiple AWS account sessions
- **Data Tracking**: SQLite database minimizes API calls
- **Modular Design**: Easy to extend with custom modules

### Attack Modules Relevant to Honeynets
```python
# Reconnaissance modules
pacu > run iam__enum_users
pacu > run ec2__enum
pacu > run s3__bucket_finder

# Exploitation modules
pacu > run iam__privesc_scan
pacu > run ec2__startup_shell_script
pacu > run lambda__backdoor_new_roles

# Persistence
pacu > run iam__backdoor_users
pacu > run ec2__backdoor_ec2_sec_groups
```

### Installation
```bash
git clone https://github.com/RhinoSecurityLabs/pacu
cd pacu
bash install.sh
python3 pacu.py
```

### Use Case for DeceptiCloud
- **Cloud-Specific Attacks**: Tests honeypot's ability to detect AWS-native exploitation
- **Multi-Stage Attacks**: Enumerate → Exploit → Persist workflow
- **Privilege Escalation**: Tests detection of IAM manipulation

---

## 4. Atomic Red Team

**GitHub:** https://github.com/redcanaryco/atomic-red-team
**Website:** https://atomicredteam.io/

### Description
Library of 1200+ simple, focused adversary techniques mapped to MITRE ATT&CK for detection testing.

### Key Features
- **1225 Atomic Tests**: Covering 261 ATT&CK techniques
- **Cross-Platform**: Windows, Linux, macOS, AWS, Azure, GCP
- **Simple Execution**: Each test is a single command or script
- **Detection-Focused**: Designed to validate security controls

### Cloud Attack Examples
```bash
# AWS credential access
Invoke-AtomicTest T1552.005  # Cloud Instance Metadata API

# Initial access
Invoke-AtomicTest T1078.004  # Cloud Accounts

# Persistence
Invoke-AtomicTest T1098.001  # Additional Cloud Credentials

# Defense evasion
Invoke-AtomicTest T1562.008  # Disable Cloud Logs
```

### Installation
```powershell
# Windows
Install-Module -Name invoke-atomicredteam
Import-Module invoke-atomicredteam

# Or manual download
git clone https://github.com/redcanaryco/atomic-red-team.git
```

### Integration
Can be combined with CALDERA or run standalone against honeypot infrastructure.

---

## 5. Additional Tools

### Cloud Security Suite (cs-suite)
- **GitHub:** https://github.com/SecurityFTW/cs-suite
- Automated auditing and attack tool for AWS, GCP, Azure
- Compliance checking with offensive capabilities

### Infection Monkey
- **Website:** https://www.akamai.com/resources/product-brief/infection-monkey-data-center-edition
- Automated breach and attack simulation
- Lateral movement testing

### Metasploit Cloud Modules
- Traditional Metasploit framework with cloud-specific modules
- AWS, Azure, GCP exploitation modules
- Well-documented and widely used

---

## Attack Scenario Recommendations

### Scenario 1: SSH Brute Force + Lateral Movement
**Tools:** Stratus Red Team + Custom Scripts
**Duration:** 4 hours
**Expected Behavior:**
- Initial SSH brute force (Cowrie detection)
- Successful honeypot compromise
- Lateral movement attempts
- **RL Agent Response:** Deploy Cowrie honeypot, monitor for credential reuse

### Scenario 2: Web Application Reconnaissance
**Tools:** Atomic Red Team + Web scanners
**Duration:** 2 hours
**Expected Behavior:**
- Directory enumeration
- SQL injection attempts
- API endpoint discovery
- **RL Agent Response:** Deploy nginx honeypot, track attack patterns

### Scenario 3: Multi-Vector Cloud Attack
**Tools:** Pacu + Stratus Red Team
**Duration:** 8 hours
**Expected Behavior:**
- Cloud API enumeration
- EC2 instance enumeration
- SSH and web exploitation
- Privilege escalation attempts
- **RL Agent Response:** Dynamically switch between honeypots based on attack type

### Scenario 4: Autonomous Adversary Campaign
**Tools:** CALDERA
**Duration:** 24 hours
**Expected Behavior:**
- Adaptive attack planning
- Multi-stage exploitation
- Persistence mechanisms
- Data exfiltration attempts
- **RL Agent Response:** Learn attack patterns over time, optimize honeypot deployment

---

## Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    DeceptiCloud RL Agent                     │
│                 (Adaptive Honeypot Manager)                  │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ Monitors Attacks
                      │
┌─────────────────────▼───────────────────────────────────────┐
│                    EC2 Honeypot Instance                     │
│  ┌──────────────┐              ┌──────────────┐            │
│  │ SSH Honeypot │◄─────────────┤ Web Honeypot │            │
│  │  (Cowrie)    │              │   (nginx)    │            │
│  └───────▲──────┘              └───────▲──────┘            │
└──────────┼─────────────────────────────┼───────────────────┘
           │                             │
           │ Attack Traffic              │
           │                             │
┌──────────┴─────────────────────────────┴───────────────────┐
│               Attack Framework Orchestrator                 │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐        │
│  │   Stratus   │  │   CALDERA   │  │    Pacu     │        │
│  │  Red Team   │  │             │  │             │        │
│  └─────────────┘  └─────────────┘  └─────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

---

## Experimental Protocol

### Phase 1: Baseline Static Honeypot
1. Deploy static SSH honeypot (Cowrie only)
2. Run Stratus Red Team EC2 attacks for 4 hours
3. Measure: interactions captured, attack diversity, detection rate

### Phase 2: Baseline Static Web Honeypot
1. Deploy static web honeypot (nginx only)
2. Run Stratus Red Team web/API attacks for 4 hours
3. Measure: same metrics

### Phase 3: Adaptive RL Honeypot
1. Deploy DeceptiCloud RL agent
2. Run mixed Stratus Red Team attacks (SSH + web) for 4 hours
3. Measure: honeypot switching frequency, match rate, total detections

### Phase 4: Autonomous Adversary
1. Deploy DeceptiCloud RL agent
2. Run CALDERA autonomous campaign for 24 hours
3. Measure: long-term adaptation, attack chain disruption

### Phase 5: Cloud-Native Exploitation
1. Deploy DeceptiCloud RL agent
2. Run Pacu AWS exploitation modules for 8 hours
3. Measure: cloud-specific attack detection, API abuse detection

---

## Metrics for Comparison

| Metric | Static SSH | Static Web | RL Adaptive |
|--------|------------|------------|-------------|
| Total Interactions Captured | X | Y | Z |
| Attack Type Match Rate | Low | Low | High |
| Unique Attack Techniques Seen | Limited | Limited | Comprehensive |
| Resource Efficiency (uptime cost) | Medium | Medium | Optimized |
| Detection Diversity | Single-vector | Single-vector | Multi-vector |
| Adaptation Time | N/A | N/A | Measured |

---

## Safety and Legal Considerations

⚠️ **IMPORTANT: Authorized Testing Only**

- Only run these tools against infrastructure YOU OWN or have WRITTEN PERMISSION to test
- DeceptiCloud experiments should be in isolated AWS accounts
- Use VPCs and security groups to prevent unintended exposure
- Monitor costs - some attack techniques create billable resources
- Review AWS acceptable use policy
- Consider using AWS Organizations with SCPs to limit blast radius

---

## References

1. MITRE ATT&CK Cloud Matrix: https://attack.mitre.org/matrices/enterprise/cloud/
2. AWS Security Best Practices: https://aws.amazon.com/security/best-practices/
3. Stratus Red Team Documentation: https://stratus-red-team.cloud/attack-techniques/list/
4. CALDERA Documentation: https://caldera.readthedocs.io/
5. Pacu Wiki: https://github.com/RhinoSecurityLabs/pacu/wiki

---

## Next Steps

1. Install Stratus Red Team on attack orchestration machine
2. Configure attack scenarios in `config/attack_scenarios.yaml`
3. Update `src/advanced_attacker.py` to invoke Stratus techniques
4. Run baseline static experiments with realistic attacks
5. Run adaptive experiments with same attack profiles
6. Analyze results with statistical significance testing

This realistic attack testing will provide strong evidence for your research hypothesis about RL-based adaptive honeynets vs static deployments.
