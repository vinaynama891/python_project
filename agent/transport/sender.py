"""
CloudPulse Agent Metric Sender
Handles authenticated HTTPS communication, local queueing, retry with exponential backoff.
"""
import time
import json
import logging
from collections import deque
from typing import Optional, Dict, Any
import requests

try:
    from agent.config.settings import AgentConfig
except ImportError:
    from config.settings import AgentConfig

logger = logging.getLogger("CloudPulseAgent.Sender")


class MetricSender:
    def __init__(self, config: AgentConfig):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": f"CloudPulse-Agent/{config.agent_version}",
            "Content-Type": "application/json",
            "X-Agent-Token": config.agent_token,
            "X-Server-ID": config.server_id
        })
        # Local FIFO buffer with strict maximum capacity
        self.local_queue: deque = deque(maxlen=config.max_queue_size)
        self.is_connected: bool = True

    def update_credentials(self, server_id: str, agent_token: str):
        self.config.server_id = server_id
        self.config.agent_token = agent_token
        self.session.headers.update({
            "X-Agent-Token": agent_token,
            "X-Server-ID": server_id
        })

    def send_heartbeat(self, health_status: str = "healthy") -> bool:
        """Sends lightweight heartbeat signal to the backend."""
        if not self.config.server_id or not self.config.agent_token:
            return False

        endpoint = f"{self.config.server_url.rstrip('/')}/api/agent/heartbeat"
        payload = {
            "server_id": self.config.server_id,
            "agent_version": self.config.agent_version,
            "health_status": health_status
        }
        try:
            resp = self.session.post(endpoint, json=payload, timeout=self.config.timeout_seconds)
            if resp.status_code == 200:
                return True
            else:
                logger.warning(f"Heartbeat rejected: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            logger.debug(f"Heartbeat network error: {e}")
            return False

    def send_metrics(self, payload: Dict[str, Any]) -> bool:
        """
        Sends metrics payload. If offline or backend unreachable, buffers to local_queue
        and retries with exponential backoff upon restoration.
        """
        payload["server_id"] = self.config.server_id

        # If previous transmissions failed, queue this metric and attempt to flush
        if not self.is_connected:
            self.local_queue.append(payload)
            return self._attempt_flush()

        # Try sending directly
        success = self._post_payload_with_backoff(payload)
        if success:
            self.is_connected = True
            # Check if there are backlogged metrics to flush
            if len(self.local_queue) > 0:
                self._flush_queue()
            return True
        else:
            self.is_connected = False
            self.local_queue.append(payload)
            logger.warning(f"Backend unreachable. Buffered to queue (queue size: {len(self.local_queue)})")
            return False

    def _post_payload_with_backoff(self, payload: Dict[str, Any]) -> bool:
        """Tries to send a payload with exponential backoff retries."""
        endpoint = f"{self.config.server_url.rstrip('/')}/api/agent/metrics"
        delay = 0.5

        for attempt in range(1, self.config.max_retries + 1):
            try:
                resp = self.session.post(endpoint, json=payload, timeout=self.config.timeout_seconds)
                if resp.status_code in (200, 201):
                    return True
                elif resp.status_code == 401:
                    logger.error("Authentication failed: Agent token is invalid or revoked!")
                    return False
                else:
                    logger.warning(f"Server responded with {resp.status_code}: {resp.text}")
            except (requests.ConnectionError, requests.Timeout) as e:
                logger.debug(f"Attempt {attempt}/{self.config.max_retries} failed: {e}")
            except Exception as e:
                logger.error(f"Unexpected send error: {e}")
                return False

            if attempt < self.config.max_retries:
                time.sleep(delay)
                delay *= 2  # Exponential backoff

        return False

    def _attempt_flush(self) -> bool:
        """Attempts to flush the oldest buffered metric to see if connectivity returned."""
        if not self.local_queue:
            self.is_connected = True
            return True

        oldest = self.local_queue[0]
        if self._post_payload_with_backoff(oldest):
            self.local_queue.popleft()
            self.is_connected = True
            logger.info("Connection restored! Flushing queued metrics...")
            self._flush_queue()
            return True
        return False

    def _flush_queue(self):
        """Drains remaining queue while connection holds."""
        while self.local_queue:
            item = self.local_queue[0]
            try:
                endpoint = f"{self.config.server_url.rstrip('/')}/api/agent/metrics"
                resp = self.session.post(endpoint, json=item, timeout=self.config.timeout_seconds)
                if resp.status_code in (200, 201):
                    self.local_queue.popleft()
                else:
                    self.is_connected = False
                    break
            except Exception:
                self.is_connected = False
                break
