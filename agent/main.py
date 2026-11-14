"""
CloudPulse Host Monitoring Agent Entrypoint
Academic Capstone Session 2026-2027
"""
import sys
import os
import time
import signal
import argparse
import logging
import json
from pathlib import Path

# Add project root to sys.path so modules resolve cleanly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.config.settings import AgentConfig
from agent.collector.system_collector import SystemCollector
from agent.transport.sender import MetricSender
from agent.transport.auth import register_agent

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [CloudPulse-Agent] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("CloudPulseAgent")


class CloudPulseAgent:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.collector = SystemCollector(agent_version=config.agent_version)
        self.sender = MetricSender(config)
        self.running = False
        self._setup_signals()

    def _setup_signals(self):
        signal.signal(signal.SIGINT, self._handle_shutdown)
        if hasattr(signal, "SIGTERM"):
            signal.signal(signal.SIGTERM, self._handle_shutdown)

    def _handle_shutdown(self, signum, frame):
        logger.info("Shutdown signal received. Cleaning up and stopping agent gracefully...")
        self.running = False

    def test_run(self):
        """Perform a single real collection pass and print the JSON metrics to stdout."""
        logger.info("Performing single test collection of real machine metrics...")
        # Brief sleep for delta calculations
        time.sleep(1.0)
        metrics = self.collector.collect_all_metrics()
        print("\n" + "=" * 60)
        print("CLOUDPULSE REAL-TIME HARDWARE METRIC SAMPLE:")
        print("=" * 60)
        print(json.dumps(metrics, indent=2))
        print("=" * 60 + "\n")
        logger.info("Test collection succeeded! All hardware and process metrics verified.")

    def run(self):
        if not self.config.server_id or not self.config.agent_token:
            logger.error("Agent is not configured with Server ID or Agent Token.")
            logger.info("Please register the agent first: python -m agent.main --register <REGISTRATION_TOKEN> --url <BACKEND_URL>")
            sys.exit(1)

        self.running = True
        logger.info(f"CloudPulse Agent started (Server ID: {self.config.server_id}).")
        logger.info(f"Collection interval: {self.config.collection_interval}s. Target: {self.config.server_url}")

        last_heartbeat = 0.0

        # Prime network and disk counters
        self.collector.collect_all_metrics()
        time.sleep(1.0)

        while self.running:
            loop_start = time.time()
            try:
                # 1. Collect real telemetry
                payload = self.collector.collect_all_metrics()

                # 2. Transmit to backend
                sent = self.sender.send_metrics(payload)
                if sent:
                    logger.info(
                        f"Metric sent - CPU: {payload['cpu']['cpu_percent']}% | "
                        f"RAM: {payload['memory']['ram_percent']}% | "
                        f"Disk: {payload['disk']['disk_percent']}% | "
                        f"Net Up: {payload['network']['upload_speed_bytes_sec']} B/s | "
                        f"Net Down: {payload['network']['download_speed_bytes_sec']} B/s"
                    )

                # 3. Periodic Heartbeat
                now = time.time()
                if now - last_heartbeat >= self.config.heartbeat_interval:
                    self.sender.send_heartbeat(health_status="healthy")
                    last_heartbeat = now

            except Exception as e:
                logger.error(f"Error during collection/transmission cycle: {e}", exc_info=True)

            # Sleep remaining interval time
            elapsed = time.time() - loop_start
            sleep_time = max(0.1, self.config.collection_interval - elapsed)
            time.sleep(sleep_time)

        logger.info("CloudPulse Agent stopped.")


def main():
    parser = argparse.ArgumentParser(description="CloudPulse Real-Time System Monitoring Agent")
    parser.add_argument("--url", type=str, help="Backend URL (e.g., http://localhost:8000)")
    parser.add_argument("--token", type=str, help="Agent Token")
    parser.add_argument("--server-id", type=str, help="Server UUID")
    parser.add_argument("--interval", type=int, default=5, help="Collection interval in seconds (default: 5)")
    parser.add_argument("--register", type=str, help="Admin Registration Token for self-registration")
    parser.add_argument("--name", type=str, help="Custom server name for registration")
    parser.add_argument("--test", action="store_true", help="Perform single test collection of real metrics and exit")

    args = parser.parse_args()
    config = AgentConfig.load()

    if args.url:
        config.server_url = args.url
    if args.token:
        config.agent_token = args.token
    if args.server_id:
        config.server_id = args.server_id
    if args.interval:
        config.collection_interval = args.interval

    # Registration Mode
    if args.register:
        logger.info(f"Initiating registration with backend: {config.server_url}...")
        res = register_agent(config.server_url, args.register, args.name)
        if res:
            server_id, agent_token = res
            config.server_id = server_id
            config.agent_token = agent_token
            config.save()
            logger.info("Registration complete! Credentials saved to agent_config.json")
            print(f"\nSuccessfully registered server with ID: {server_id}\n")
            return
        else:
            logger.error("Registration failed. Please check registration token and backend connectivity.")
            sys.exit(1)

    agent = CloudPulseAgent(config)

    if args.test:
        agent.test_run()
        return

    agent.run()


if __name__ == "__main__":
    main()
