"""
Command Interceptor

Intercepts honeypot commands and generates intelligent, context-aware responses
based on attacker profile and behavior.
"""

import re
import time
from typing import Dict, List, Optional, Tuple
from .adaptive_deception import AdaptiveDeceptionEngine, InterestCategory
from .content_generator import ContentGenerator
from .deception_metrics import DeceptionMetrics


class CommandInterceptor:
    """
    Intercepts commands and generates adaptive deceptive responses.

    This is the main integration point that connects the deception engine,
    content generator, and metrics tracking.
    """

    def __init__(self, data_dir: str = "./data/deception"):
        self.deception_engine = AdaptiveDeceptionEngine()
        self.content_generator = ContentGenerator()
        self.metrics = DeceptionMetrics(data_dir)

        # Command handlers
        self.handlers = {
            'ls': self._handle_ls,
            'dir': self._handle_ls,  # Alias
            'cat': self._handle_cat,
            'type': self._handle_cat,  # Windows equivalent
            'find': self._handle_find,
            'grep': self._handle_grep,
            'ps': self._handle_ps,
            'netstat': self._handle_netstat,
            'ss': self._handle_netstat,  # Modern netstat
            'ifconfig': self._handle_ifconfig,
            'ip': self._handle_ip,
        }

    def process_command(self, session_id: str, command: str, ip: str,
                       username: str) -> Tuple[Optional[str], bool]:
        """
        Process a command and generate adaptive response.

        Args:
            session_id: Unique session identifier
            command: Command executed by attacker
            ip: Attacker IP address
            username: Username used in session

        Returns:
            Tuple of (response_text, should_intercept)
            - response_text: Generated response or None to use real output
            - should_intercept: True if we generated fake output, False to pass through
        """
        # Track command in deception engine
        self.deception_engine.track_session(session_id, command, ip, username)

        # Start session in metrics if new
        profile = self.deception_engine.get_session_profile(session_id)
        if profile and session_id not in self.metrics.sessions:
            self.metrics.start_session(
                session_id, ip, username,
                profile['skill_level']
            )

        # Parse command to get base command
        base_command = self._extract_base_command(command)

        # Check if we should intercept this command
        should_intercept = self._should_intercept(command, session_id)

        if not should_intercept:
            # Record command but don't intercept
            self.metrics.record_command(session_id, command)
            return None, False

        # Get handler for this command
        handler = self.handlers.get(base_command)
        if not handler:
            # No handler, pass through
            self.metrics.record_command(session_id, command)
            return None, False

        # Get deception strategy for this session
        strategy = self.deception_engine.get_deception_strategy(session_id)

        # Generate response
        response = handler(command, strategy, session_id)

        if response:
            # Add realistic delay
            time.sleep(strategy['response_delay'])

            # Determine deception type and interests
            deception_type, interests = self._classify_command(command)

            # Record deception event
            self.metrics.record_deception_event(
                session_id, command, deception_type,
                f"Generated {base_command} output", interests
            )

            return response, True
        else:
            self.metrics.record_command(session_id, command)
            return None, False

    def end_session(self, session_id: str) -> Optional[Dict]:
        """
        End a session and get summary metrics.

        Args:
            session_id: Session identifier

        Returns:
            Session summary
        """
        return self.metrics.end_session(session_id)

    def get_metrics_report(self) -> Dict:
        """Get comprehensive deception metrics report."""
        return self.metrics.get_effectiveness_report()

    def get_rl_reward(self, session_id: str) -> float:
        """
        Get RL reward bonus for this session's deception effectiveness.

        Args:
            session_id: Session identifier

        Returns:
            Reward value (0-10)
        """
        return self.metrics.get_rl_reward_bonus(session_id)

    # Command Handlers

    def _handle_ls(self, command: str, strategy: Dict, session_id: str) -> Optional[str]:
        """Handle ls/dir commands."""
        # Extract path from command
        path = self._extract_path_from_ls(command)

        # Get interests
        interests = [i.value for i in self.deception_engine.sessions.get(
            session_id, {}
        ).get('interests', [])]

        # Generate directory listing
        return self.content_generator.generate_directory_listing(
            path, interests, strategy['skill_level']
        )

    def _handle_cat(self, command: str, strategy: Dict, session_id: str) -> Optional[str]:
        """Handle cat/type commands."""
        # Extract filename
        filename = self._extract_filename_from_cat(command)

        if not filename:
            return None

        # Get interests
        interests = [i.value for i in self.deception_engine.sessions.get(
            session_id, {}
        ).get('interests', [])]

        # Generate file content
        return self.content_generator.generate_file_content(
            filename, interests, strategy['skill_level']
        )

    def _handle_find(self, command: str, strategy: Dict, session_id: str) -> Optional[str]:
        """Handle find commands."""
        # Extract search term
        search_term = self._extract_find_pattern(command)

        if not search_term:
            return None

        # Get interests
        interests = [i.value for i in self.deception_engine.sessions.get(
            session_id, {}
        ).get('interests', [])]

        # Generate find results
        results = self.content_generator.generate_find_results(
            search_term, interests, strategy['skill_level']
        )

        return '\n'.join(results) if results else None

    def _handle_grep(self, command: str, strategy: Dict, session_id: str) -> Optional[str]:
        """Handle grep commands."""
        # Extract pattern and file
        pattern, file_path = self._extract_grep_params(command)

        if not pattern:
            return None

        # Get interests
        interests = [i.value for i in self.deception_engine.sessions.get(
            session_id, {}
        ).get('interests', [])]

        # Generate grep results
        return self.content_generator.generate_grep_results(
            pattern, file_path or '/var/log/app.log',
            interests, strategy['skill_level']
        )

    def _handle_ps(self, command: str, strategy: Dict, session_id: str) -> Optional[str]:
        """Handle ps commands."""
        return self.content_generator.generate_ps_output(strategy['skill_level'])

    def _handle_netstat(self, command: str, strategy: Dict, session_id: str) -> Optional[str]:
        """Handle netstat/ss commands."""
        return self.content_generator.generate_netstat_output(strategy['skill_level'])

    def _handle_ifconfig(self, command: str, strategy: Dict, session_id: str) -> Optional[str]:
        """Handle ifconfig commands."""
        return """eth0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 10.0.1.42  netmask 255.255.255.0  broadcast 10.0.1.255
        inet6 fe80::a00:27ff:fe4e:66a1  prefixlen 64  scopeid 0x20<link>
        ether 02:00:27:4e:66:a1  txqueuelen 1000  (Ethernet)
        RX packets 458234  bytes 123456789 (117.7 MiB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 312456  bytes 87654321 (83.5 MiB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0

lo: flags=73<UP,LOOPBACK,RUNNING>  mtu 65536
        inet 127.0.0.1  netmask 255.0.0.0
        inet6 ::1  prefixlen 128  scopeid 0x10<host>
        loop  txqueuelen 1000  (Local Loopback)
        RX packets 12345  bytes 6789012 (6.4 MiB)
        RX errors 0  dropped 0  overruns 0  frame 0
        TX packets 12345  bytes 6789012 (6.4 MiB)
        TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0"""

    def _handle_ip(self, command: str, strategy: Dict, session_id: str) -> Optional[str]:
        """Handle ip commands."""
        if 'addr' in command or 'address' in command:
            return """1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
    link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
    inet 127.0.0.1/8 scope host lo
       valid_lft forever preferred_lft forever
    inet6 ::1/128 scope host
       valid_lft forever preferred_lft forever
2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP group default qlen 1000
    link/ether 02:00:27:4e:66:a1 brd ff:ff:ff:ff:ff:ff
    inet 10.0.1.42/24 brd 10.0.1.255 scope global dynamic eth0
       valid_lft 86398sec preferred_lft 86398sec
    inet6 fe80::a00:27ff:fe4e:66a1/64 scope link
       valid_lft forever preferred_lft forever"""
        return None

    # Helper Methods

    def _extract_base_command(self, command: str) -> str:
        """Extract the base command from a full command line."""
        # Remove leading/trailing whitespace
        command = command.strip()

        # Handle commands with pipes, redirects, etc.
        command = command.split('|')[0].split('>')[0].split('<')[0].strip()

        # Extract first word (the command itself)
        parts = command.split()
        if not parts:
            return ''

        # Remove sudo, nice, etc.
        while parts and parts[0] in ['sudo', 'nice', 'time', 'nohup']:
            parts = parts[1:]

        return parts[0] if parts else ''

    def _should_intercept(self, command: str, session_id: str) -> bool:
        """
        Determine if we should intercept this command.

        Args:
            command: Command to evaluate
            session_id: Session identifier

        Returns:
            True if we should generate fake output
        """
        base_cmd = self._extract_base_command(command)

        # Always intercept high-value commands
        high_value_commands = [
            'cat', 'grep', 'find', 'ls', 'dir', 'type'
        ]

        if base_cmd in high_value_commands:
            # Check if command targets interesting files/patterns
            interesting_patterns = [
                'password', 'passwd', '.env', 'credential', 'secret',
                'key', 'token', 'api', 'aws', '.ssh', 'id_rsa',
                'config', 'backup', 'database', 'payroll', 'invoice'
            ]

            cmd_lower = command.lower()
            if any(pattern in cmd_lower for pattern in interesting_patterns):
                return True

            # Intercept based on probability (to mix real and fake)
            # 70% chance of interception for suspicious commands
            import random
            return random.random() < 0.7

        # Sometimes intercept system info commands
        if base_cmd in ['ps', 'netstat', 'ss', 'ifconfig', 'ip']:
            import random
            return random.random() < 0.5

        return False

    def _extract_path_from_ls(self, command: str) -> str:
        """Extract path from ls command."""
        parts = command.split()
        for i, part in enumerate(parts):
            if part in ['ls', 'dir']:
                if i + 1 < len(parts) and not parts[i + 1].startswith('-'):
                    return parts[i + 1]
                break
        return '.'  # Current directory

    def _extract_filename_from_cat(self, command: str) -> Optional[str]:
        """Extract filename from cat command."""
        parts = command.split()
        for i, part in enumerate(parts):
            if part in ['cat', 'type']:
                if i + 1 < len(parts):
                    return parts[i + 1]
                break
        return None

    def _extract_find_pattern(self, command: str) -> Optional[str]:
        """Extract search pattern from find command."""
        # Look for -name argument
        match = re.search(r'-name\s+["\']?([^"\']+)["\']?', command)
        if match:
            return match.group(1)

        # Look for pattern after find
        match = re.search(r'find\s+\S+\s+(.+?)(?:\s|$)', command)
        if match:
            return match.group(1)

        return None

    def _extract_grep_params(self, command: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract pattern and file path from grep command."""
        # Simple extraction - can be enhanced
        parts = command.split()

        pattern = None
        file_path = None

        for i, part in enumerate(parts):
            if part in ['grep']:
                # Skip flags
                j = i + 1
                while j < len(parts) and parts[j].startswith('-'):
                    j += 1

                # Next non-flag is pattern
                if j < len(parts):
                    pattern = parts[j].strip('"\'')
                    j += 1

                # Next is file path
                if j < len(parts):
                    file_path = parts[j]

                break

        return pattern, file_path

    def _classify_command(self, command: str) -> Tuple[str, List[str]]:
        """
        Classify command to determine deception type and interests.

        Args:
            command: Command executed

        Returns:
            Tuple of (deception_type, interests_list)
        """
        cmd_lower = command.lower()
        deception_type = 'command_output'
        interests = []

        # Determine deception type
        if 'cat' in cmd_lower or 'type' in cmd_lower:
            if any(x in cmd_lower for x in ['.env', 'password', 'credential', 'secret']):
                deception_type = 'credentials_file'
                interests.append('credentials')
            elif any(x in cmd_lower for x in ['payroll', 'invoice', 'payment']):
                deception_type = 'financial_data'
                interests.append('financial')
            elif 'config' in cmd_lower or '.conf' in cmd_lower:
                deception_type = 'config_file'
                interests.append('system_info')
            elif 'id_rsa' in cmd_lower or 'ssh' in cmd_lower:
                deception_type = 'ssh_key'
                interests.append('credentials')
            elif '.sql' in cmd_lower or 'database' in cmd_lower:
                deception_type = 'database_dump'
                interests.append('data_exfiltration')

        elif 'ls' in cmd_lower or 'dir' in cmd_lower:
            deception_type = 'directory_listing'
            # Detect interests from path
            if any(x in cmd_lower for x in ['ssh', 'credential', 'password']):
                interests.append('credentials')

        elif 'find' in cmd_lower or 'grep' in cmd_lower:
            # Detect interests from search pattern
            if any(x in cmd_lower for x in ['password', 'passwd', 'credential', 'secret', 'key']):
                interests.append('credentials')
            if any(x in cmd_lower for x in ['payroll', 'invoice', 'payment', 'bank']):
                interests.append('financial')
            if any(x in cmd_lower for x in ['database', '.db', 'sql']):
                interests.append('data_exfiltration')

        elif any(x in cmd_lower for x in ['ps', 'netstat', 'ss', 'ifconfig']):
            deception_type = 'system_info'
            interests.append('system_info')
            if 'netstat' in cmd_lower or 'ss' in cmd_lower:
                interests.append('network')

        return deception_type, interests

    def export_metrics(self, format: str = 'json') -> str:
        """
        Export metrics in specified format.

        Args:
            format: 'json' or 'csv'

        Returns:
            Path to exported file
        """
        if format == 'json':
            return self.metrics.export_json()
        elif format == 'csv':
            return self.metrics.export_csv_summary()
        else:
            raise ValueError(f"Unsupported format: {format}")
