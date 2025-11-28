"""
Adaptive Deception Engine

Tracks attacker behavior, detects skill levels, and adapts deception strategies in real-time.
"""

import re
from datetime import datetime
from typing import Dict, List, Set, Tuple, Optional
from enum import Enum
from collections import defaultdict, Counter
import json


class SkillLevel(Enum):
    """Attacker skill level classification"""
    NOVICE = "novice"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class InterestCategory(Enum):
    """Types of assets attackers may be interested in"""
    CREDENTIALS = "credentials"
    FINANCIAL = "financial"
    SYSTEM_INFO = "system_info"
    NETWORK = "network"
    DATA_EXFILTRATION = "data_exfiltration"
    LATERAL_MOVEMENT = "lateral_movement"
    PERSISTENCE = "persistence"
    PRIVILEGE_ESCALATION = "privilege_escalation"


class AdaptiveDeceptionEngine:
    """
    Main engine for adaptive deception that analyzes attacker behavior
    and generates appropriate responses.
    """

    def __init__(self):
        # Session tracking
        self.sessions: Dict[str, Dict] = {}

        # Command pattern databases
        self.novice_patterns = self._load_novice_patterns()
        self.intermediate_patterns = self._load_intermediate_patterns()
        self.advanced_patterns = self._load_advanced_patterns()
        self.expert_patterns = self._load_expert_patterns()

        # Interest detection patterns
        self.interest_patterns = self._load_interest_patterns()

        # Statistics
        self.stats = {
            'total_sessions': 0,
            'skill_distribution': defaultdict(int),
            'interest_distribution': defaultdict(int),
        }

    def track_session(self, session_id: str, command: str, ip: str, username: str) -> None:
        """
        Track a command from an attacker session.

        Args:
            session_id: Unique session identifier
            command: Command executed by attacker
            ip: Attacker IP address
            username: Username used in session
        """
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'session_id': session_id,
                'ip': ip,
                'username': username,
                'start_time': datetime.now(),
                'commands': [],
                'interests': set(),
                'skill_indicators': defaultdict(int),
                'current_skill_level': SkillLevel.NOVICE,
                'command_count': 0,
            }
            self.stats['total_sessions'] += 1

        session = self.sessions[session_id]
        session['commands'].append({
            'command': command,
            'timestamp': datetime.now(),
        })
        session['command_count'] += 1
        session['last_seen'] = datetime.now()

        # Analyze command
        self._analyze_command(session_id, command)

    def _analyze_command(self, session_id: str, command: str) -> None:
        """Analyze a command and update session profile."""
        session = self.sessions[session_id]

        # Detect skill level indicators
        self._detect_skill_level(session_id, command)

        # Detect interests
        interests = self._detect_interests(command)
        for interest in interests:
            session['interests'].add(interest)
            self.stats['interest_distribution'][interest.value] += 1

    def _detect_skill_level(self, session_id: str, command: str) -> None:
        """Detect and update skill level based on command patterns."""
        session = self.sessions[session_id]

        # Check against pattern databases
        if self._matches_patterns(command, self.expert_patterns):
            session['skill_indicators'][SkillLevel.EXPERT] += 3
        elif self._matches_patterns(command, self.advanced_patterns):
            session['skill_indicators'][SkillLevel.ADVANCED] += 2
        elif self._matches_patterns(command, self.intermediate_patterns):
            session['skill_indicators'][SkillLevel.INTERMEDIATE] += 1
        else:
            # Default novice indicators
            session['skill_indicators'][SkillLevel.NOVICE] += 1

        # Update skill level based on accumulated indicators
        self._update_skill_level(session_id)

    def _update_skill_level(self, session_id: str) -> None:
        """Update the assessed skill level of a session."""
        session = self.sessions[session_id]
        indicators = session['skill_indicators']

        # Calculate weighted score
        total_score = (
            indicators[SkillLevel.EXPERT] * 8 +
            indicators[SkillLevel.ADVANCED] * 4 +
            indicators[SkillLevel.INTERMEDIATE] * 2 +
            indicators[SkillLevel.NOVICE] * 1
        )

        total_commands = sum(indicators.values())
        if total_commands == 0:
            return

        avg_score = total_score / total_commands

        # Classify based on average score
        old_level = session['current_skill_level']
        if avg_score >= 6:
            session['current_skill_level'] = SkillLevel.EXPERT
        elif avg_score >= 4:
            session['current_skill_level'] = SkillLevel.ADVANCED
        elif avg_score >= 2:
            session['current_skill_level'] = SkillLevel.INTERMEDIATE
        else:
            session['current_skill_level'] = SkillLevel.NOVICE

        # Update stats if level changed
        if old_level != session['current_skill_level']:
            self.stats['skill_distribution'][old_level.value] -= 1
            self.stats['skill_distribution'][session['current_skill_level'].value] += 1

    def _detect_interests(self, command: str) -> List[InterestCategory]:
        """Detect what the attacker is interested in based on command."""
        interests = []

        for category, patterns in self.interest_patterns.items():
            if self._matches_patterns(command, patterns):
                interests.append(category)

        return interests

    def _matches_patterns(self, command: str, patterns: List[str]) -> bool:
        """Check if command matches any pattern in the list."""
        for pattern in patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return True
        return False

    def get_session_profile(self, session_id: str) -> Optional[Dict]:
        """Get the complete profile of a session."""
        if session_id not in self.sessions:
            return None

        session = self.sessions[session_id]
        return {
            'session_id': session_id,
            'ip': session['ip'],
            'username': session['username'],
            'skill_level': session['current_skill_level'].value,
            'interests': [i.value for i in session['interests']],
            'command_count': session['command_count'],
            'duration': (session['last_seen'] - session['start_time']).total_seconds(),
        }

    def get_deception_strategy(self, session_id: str) -> Dict:
        """
        Get the recommended deception strategy for a session.

        Returns:
            Dictionary with deception recommendations
        """
        if session_id not in self.sessions:
            return self._default_strategy()

        session = self.sessions[session_id]
        skill_level = session['current_skill_level']
        interests = session['interests']

        strategy = {
            'skill_level': skill_level.value,
            'complexity': self._get_complexity_level(skill_level),
            'target_interests': [i.value for i in interests],
            'breadcrumbs': self._generate_breadcrumbs(interests, skill_level),
            'response_delay': self._calculate_response_delay(skill_level),
            'realism_level': self._get_realism_level(skill_level),
        }

        return strategy

    def _get_complexity_level(self, skill_level: SkillLevel) -> str:
        """Determine content complexity based on skill level."""
        mapping = {
            SkillLevel.NOVICE: "simple",
            SkillLevel.INTERMEDIATE: "moderate",
            SkillLevel.ADVANCED: "complex",
            SkillLevel.EXPERT: "highly_realistic",
        }
        return mapping[skill_level]

    def _generate_breadcrumbs(self, interests: Set[InterestCategory],
                             skill_level: SkillLevel) -> List[str]:
        """Generate appropriate breadcrumb paths based on interests."""
        breadcrumbs = []

        # Map interests to directory/file hints
        interest_paths = {
            InterestCategory.CREDENTIALS: [
                '/home/admin/.ssh',
                '/var/backups/credentials',
                '/opt/app/config/.env',
            ],
            InterestCategory.FINANCIAL: [
                '/var/data/payroll',
                '/home/finance/reports',
                '/opt/billing/database',
            ],
            InterestCategory.SYSTEM_INFO: [
                '/var/log/auth.log',
                '/etc/shadow',
                '/proc/cpuinfo',
            ],
            InterestCategory.NETWORK: [
                '/etc/hosts',
                '/var/log/nginx',
                '/home/admin/.bash_history',
            ],
            InterestCategory.DATA_EXFILTRATION: [
                '/var/backups/customer_data',
                '/mnt/shared/documents',
                '/home/users/sensitive',
            ],
        }

        for interest in interests:
            if interest in interest_paths:
                breadcrumbs.extend(interest_paths[interest])

        # Adjust number of breadcrumbs based on skill level
        if skill_level == SkillLevel.NOVICE:
            return breadcrumbs[:2]  # Fewer, more obvious
        elif skill_level == SkillLevel.INTERMEDIATE:
            return breadcrumbs[:4]
        else:
            return breadcrumbs  # All breadcrumbs for advanced users

    def _calculate_response_delay(self, skill_level: SkillLevel) -> float:
        """Calculate realistic response delay in seconds."""
        # Advanced users might detect instant responses
        delays = {
            SkillLevel.NOVICE: 0.01,
            SkillLevel.INTERMEDIATE: 0.05,
            SkillLevel.ADVANCED: 0.1,
            SkillLevel.EXPERT: 0.2,
        }
        return delays[skill_level]

    def _get_realism_level(self, skill_level: SkillLevel) -> int:
        """Get realism level (1-10) based on skill."""
        levels = {
            SkillLevel.NOVICE: 5,
            SkillLevel.INTERMEDIATE: 7,
            SkillLevel.ADVANCED: 9,
            SkillLevel.EXPERT: 10,
        }
        return levels[skill_level]

    def _default_strategy(self) -> Dict:
        """Return default deception strategy for unknown sessions."""
        return {
            'skill_level': SkillLevel.NOVICE.value,
            'complexity': 'simple',
            'target_interests': [],
            'breadcrumbs': [],
            'response_delay': 0.01,
            'realism_level': 5,
        }

    def export_statistics(self) -> Dict:
        """Export current statistics."""
        return {
            'timestamp': datetime.now().isoformat(),
            'total_sessions': self.stats['total_sessions'],
            'active_sessions': len(self.sessions),
            'skill_distribution': dict(self.stats['skill_distribution']),
            'interest_distribution': dict(self.stats['interest_distribution']),
        }

    def save_state(self, filepath: str) -> None:
        """Save engine state to file."""
        state = {
            'stats': self.stats,
            'sessions': {
                sid: {
                    **session,
                    'interests': [i.value for i in session['interests']],
                    'current_skill_level': session['current_skill_level'].value,
                    'start_time': session['start_time'].isoformat(),
                    'last_seen': session['last_seen'].isoformat(),
                }
                for sid, session in self.sessions.items()
            },
        }

        with open(filepath, 'w') as f:
            json.dump(state, f, indent=2, default=str)

    # Pattern databases
    def _load_novice_patterns(self) -> List[str]:
        """Load novice-level command patterns."""
        return [
            r'^ls$',
            r'^pwd$',
            r'^whoami$',
            r'^id$',
            r'^cat\s+\w+',
            r'^cd\s+',
            r'^wget\s+',
            r'^curl\s+http',
            r'^uname\s+-a',
            r'^echo\s+',
        ]

    def _load_intermediate_patterns(self) -> List[str]:
        """Load intermediate-level command patterns."""
        return [
            r'find\s+.*-name',
            r'grep\s+-r',
            r'nc\s+-',
            r'python\s+-c',
            r'perl\s+-e',
            r'bash\s+-i',
            r'chmod\s+\+x',
            r'\.\/\w+',
            r'sudo\s+',
            r'su\s+-',
            r'ps\s+aux',
            r'netstat\s+-',
            r'ss\s+-',
            r'history\s*\|',
        ]

    def _load_advanced_patterns(self) -> List[str]:
        """Load advanced-level command patterns."""
        return [
            r'nmap\s+',
            r'metasploit',
            r'msfvenom',
            r'socat\s+',
            r'ssh\s+-[DLR]',
            r'sshuttle',
            r'/dev/tcp/',
            r'awk\s+.*system',
            r'perl\s+.*socket',
            r'python.*pty\.spawn',
            r'script\s+/dev/null',
            r'stty\s+raw',
            r'base64\s+-d.*\|',
            r'openssl\s+enc',
            r'gpg\s+-d',
        ]

    def _load_expert_patterns(self) -> List[str]:
        """Load expert-level command patterns."""
        return [
            r'iptables\s+-t\s+nat',
            r'nftables',
            r'bpf',
            r'ldpreload',
            r'LD_PRELOAD',
            r'ptrace',
            r'strace\s+-e\s+inject',
            r'gdb\s+-p',
            r'frida',
            r'radare2',
            r'objdump.*-d',
            r'readelf',
            r'ldd.*inject',
            r'volatility',
            r'mimikatz',
            r'bloodhound',
            r'crackmapexec',
            r'impacket',
        ]

    def _load_interest_patterns(self) -> Dict[InterestCategory, List[str]]:
        """Load interest detection patterns."""
        return {
            InterestCategory.CREDENTIALS: [
                r'pass(word|wd)?',
                r'\.ssh',
                r'id_rsa',
                r'\.aws',
                r'credentials',
                r'\.env',
                r'secret',
                r'token',
                r'api[_-]?key',
                r'/etc/shadow',
                r'/etc/passwd',
                r'\.git-credentials',
                r'\.netrc',
            ],
            InterestCategory.FINANCIAL: [
                r'bank',
                r'payment',
                r'payroll',
                r'finance',
                r'invoice',
                r'transaction',
                r'credit',
                r'billing',
            ],
            InterestCategory.SYSTEM_INFO: [
                r'uname',
                r'hostname',
                r'ifconfig',
                r'ip\s+addr',
                r'/proc/',
                r'/sys/',
                r'lsb_release',
                r'os-release',
            ],
            InterestCategory.NETWORK: [
                r'netstat',
                r'ss\s+-',
                r'iptables',
                r'route',
                r'tcpdump',
                r'wireshark',
                r'nmap',
                r'/etc/hosts',
            ],
            InterestCategory.DATA_EXFILTRATION: [
                r'tar\s+.*czf',
                r'zip\s+-r',
                r'scp\s+',
                r'rsync',
                r'curl.*-T',
                r'wget.*--post',
                r'nc.*>',
                r'base64.*<',
            ],
            InterestCategory.LATERAL_MOVEMENT: [
                r'ssh\s+\w+@',
                r'psexec',
                r'wmiexec',
                r'sshpass',
                r'pivot',
                r'tunnel',
                r'proxy',
            ],
            InterestCategory.PERSISTENCE: [
                r'crontab',
                r'systemctl',
                r'\.bashrc',
                r'\.profile',
                r'/etc/rc\.',
                r'init\.d',
                r'\.ssh/authorized_keys',
            ],
            InterestCategory.PRIVILEGE_ESCALATION: [
                r'sudo\s+-l',
                r'sudo\s+su',
                r'SUID',
                r'capabilities',
                r'docker\s+.*-v.*:/root',
                r'kernel.*exploit',
                r'pkexec',
                r'polkit',
            ],
        }
