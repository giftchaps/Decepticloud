"""
Cowrie Integration Module

Integrates the adaptive deception system with Cowrie honeypot by monitoring
Cowrie logs and providing a command processing interface.
"""

import json
import time
from datetime import datetime
from typing import Dict, Optional, Any
from pathlib import Path
import logging
from .command_interceptor import CommandInterceptor


class CowrieIntegration:
    """
    Integration layer for Cowrie honeypot.

    Monitors Cowrie JSON logs in real-time and processes commands through
    the deception system.
    """

    def __init__(self, log_file: str = "/cowrie/var/log/cowrie/cowrie.json",
                 data_dir: str = "./data/deception"):
        """
        Initialize Cowrie integration.

        Args:
            log_file: Path to Cowrie JSON log file
            data_dir: Directory for deception data
        """
        self.log_file = Path(log_file)
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize deception system
        self.interceptor = CommandInterceptor(str(self.data_dir))

        # Session tracking
        self.active_sessions: Dict[str, Dict] = {}

        # Log position tracking (for tailing)
        self.log_position = 0

        # Configure logging
        self.logger = logging.getLogger('cowrie_integration')
        self.logger.setLevel(logging.INFO)

        handler = logging.FileHandler(self.data_dir / 'cowrie_integration.log')
        handler.setFormatter(
            logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        )
        self.logger.addHandler(handler)

    def process_log_entry(self, entry: Dict[str, Any]) -> Optional[Dict]:
        """
        Process a single Cowrie log entry.

        Args:
            entry: Parsed JSON log entry from Cowrie

        Returns:
            Deception response if applicable
        """
        event_id = entry.get('eventid')
        session_id = entry.get('session')

        if not session_id:
            return None

        # Handle session start
        if event_id == 'cowrie.session.connect':
            self._handle_session_start(entry)

        # Handle login attempts
        elif event_id == 'cowrie.login.success':
            self._handle_login(entry)

        # Handle commands
        elif event_id == 'cowrie.command.input':
            return self._handle_command(entry)

        # Handle session end
        elif event_id == 'cowrie.session.closed':
            return self._handle_session_end(entry)

        return None

    def tail_log_file(self, callback=None, continuous=True):
        """
        Tail Cowrie log file and process entries in real-time.

        Args:
            callback: Optional callback function for each deception event
            continuous: If True, keep tailing; if False, process existing entries
        """
        self.logger.info(f"Starting to tail log file: {self.log_file}")

        if not self.log_file.exists():
            self.logger.warning(f"Log file does not exist: {self.log_file}")
            return

        with open(self.log_file, 'r') as f:
            # Seek to last known position
            f.seek(self.log_position)

            while True:
                line = f.readline()

                if line:
                    try:
                        entry = json.loads(line)
                        response = self.process_log_entry(entry)

                        if response and callback:
                            callback(response)

                        # Update position
                        self.log_position = f.tell()

                    except json.JSONDecodeError as e:
                        self.logger.error(f"Failed to parse log entry: {e}")
                        continue

                else:
                    if not continuous:
                        break

                    # No new data, wait a bit
                    time.sleep(0.1)

    def get_command_response(self, session_id: str, command: str,
                            ip: str, username: str) -> Tuple[Optional[str], bool]:
        """
        Get deceptive response for a command.

        This can be called directly from custom Cowrie commands.

        Args:
            session_id: Session identifier
            command: Command to process
            ip: Source IP
            username: Username

        Returns:
            Tuple of (response, should_intercept)
        """
        return self.interceptor.process_command(
            session_id, command, ip, username
        )

    def get_session_metrics(self, session_id: str) -> Optional[Dict]:
        """Get metrics for a specific session."""
        return self.interceptor.metrics.get_session_profile(session_id)

    def get_effectiveness_report(self) -> Dict:
        """Get overall deception effectiveness report."""
        return self.interceptor.get_metrics_report()

    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics to file."""
        return self.interceptor.export_metrics(format)

    # Private methods

    def _handle_session_start(self, entry: Dict) -> None:
        """Handle new session connection."""
        session_id = entry['session']
        src_ip = entry.get('src_ip', 'unknown')

        self.active_sessions[session_id] = {
            'session_id': session_id,
            'src_ip': src_ip,
            'start_time': entry.get('timestamp'),
            'username': None,
        }

        self.logger.info(f"New session: {session_id} from {src_ip}")

    def _handle_login(self, entry: Dict) -> None:
        """Handle successful login."""
        session_id = entry['session']
        username = entry.get('username', 'unknown')

        if session_id in self.active_sessions:
            self.active_sessions[session_id]['username'] = username

        self.logger.info(f"Login: {session_id} as {username}")

    def _handle_command(self, entry: Dict) -> Optional[Dict]:
        """Handle command execution."""
        session_id = entry['session']
        command = entry.get('input', '')

        if not command or session_id not in self.active_sessions:
            return None

        session = self.active_sessions[session_id]
        ip = session['src_ip']
        username = session.get('username', 'unknown')

        # Process through deception system
        response, intercepted = self.interceptor.process_command(
            session_id, command, ip, username
        )

        self.logger.info(
            f"Command from {session_id}: {command} "
            f"(intercepted: {intercepted})"
        )

        if intercepted and response:
            return {
                'session_id': session_id,
                'command': command,
                'response': response,
                'timestamp': datetime.now().isoformat(),
                'intercepted': True,
            }

        return None

    def _handle_session_end(self, entry: Dict) -> Optional[Dict]:
        """Handle session closure."""
        session_id = entry['session']

        if session_id not in self.active_sessions:
            return None

        # Get session summary from deception system
        summary = self.interceptor.end_session(session_id)

        # Clean up
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]

        self.logger.info(f"Session ended: {session_id}")

        return summary


class CowrieResponseInjector:
    """
    Provides fake file system for Cowrie using the deception system.

    This can be used to create custom files that Cowrie will serve
    when attackers try to access them.
    """

    def __init__(self, deception_dir: str = "./data/deception/cowrie_fs"):
        self.deception_dir = Path(deception_dir)
        self.deception_dir.mkdir(parents=True, exist_ok=True)

        self.interceptor = CommandInterceptor()

    def create_deceptive_files(self, session_id: str, interests: list,
                               skill_level: str) -> Dict[str, str]:
        """
        Create fake files based on attacker profile.

        Args:
            session_id: Session identifier
            interests: List of attacker interests
            skill_level: Attacker skill level

        Returns:
            Dictionary mapping file paths to content
        """
        files = {}

        # Create credential files
        if 'credentials' in interests:
            # .env file
            env_content = self.interceptor.content_generator.generate_file_content(
                '.env', interests, skill_level
            )
            files['/home/ubuntu/.env'] = env_content

            # SSH key
            ssh_key = self.interceptor.content_generator.generate_file_content(
                'id_rsa', interests, skill_level
            )
            files['/home/ubuntu/.ssh/id_rsa'] = ssh_key

            # Password file
            passwd = self.interceptor.content_generator.generate_file_content(
                'passwords.txt', interests, skill_level
            )
            files['/home/ubuntu/credentials/passwords.txt'] = passwd

        # Create financial files
        if 'financial' in interests:
            payroll = self.interceptor.content_generator.generate_file_content(
                'payroll_november.txt', interests, skill_level
            )
            files['/var/data/payroll/november_2024.txt'] = payroll

        # Create configuration files
        config = self.interceptor.content_generator.generate_file_content(
            'database.conf', interests, skill_level
        )
        files['/opt/app/config/database.conf'] = config

        # Write files to disk for Cowrie to serve
        for path, content in files.items():
            file_path = self.deception_dir / path.lstrip('/')
            file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, 'w') as f:
                f.write(content)

        return files


def start_deception_monitor(log_file: str, data_dir: str = "./data/deception"):
    """
    Start monitoring Cowrie logs and processing commands.

    This can be run as a standalone service.

    Args:
        log_file: Path to Cowrie log file
        data_dir: Directory for deception data
    """
    integration = CowrieIntegration(log_file, data_dir)

    def on_deception_event(event):
        """Callback for deception events."""
        print(f"[DECEPTION] {event['command']} -> {len(event.get('response', ''))} bytes")

    print(f"Starting Cowrie deception monitor...")
    print(f"Log file: {log_file}")
    print(f"Data directory: {data_dir}")
    print("Press Ctrl+C to stop\n")

    try:
        integration.tail_log_file(callback=on_deception_event, continuous=True)
    except KeyboardInterrupt:
        print("\nStopping deception monitor...")

        # Export final metrics
        json_file = integration.export_metrics('json')
        csv_file = integration.export_metrics('csv')

        print(f"\nMetrics exported:")
        print(f"  JSON: {json_file}")
        print(f"  CSV: {csv_file}")

        # Print summary
        report = integration.get_effectiveness_report()
        print(f"\nDeception Summary:")
        print(f"  Total events: {report['engagement_metrics']['total_deception_events']}")
        print(f"  Dwell time improvement: {report['dwell_time_analysis']['improvement_percentage']:.1f}%")


if __name__ == '__main__':
    import sys

    log_file = sys.argv[1] if len(sys.argv) > 1 else '/cowrie/var/log/cowrie/cowrie.json'
    data_dir = sys.argv[2] if len(sys.argv) > 2 else './data/deception'

    start_deception_monitor(log_file, data_dir)
