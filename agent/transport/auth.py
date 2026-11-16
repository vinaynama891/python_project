"""
CloudPulse Agent Authentication & Registration
Enables one-click token-based registration of monitoring agents.
"""
import socket
import platform
import logging
from typing import Optional, Tuple
import requests

try:
    from agent.config.settings import AgentConfig
except ImportError:
    from config.settings import AgentConfig

logger = logging.getLogger("CloudPulseAgent.Auth")


def register_agent(server_url: str, registration_token: str, server_name: Optional[str] = None) -> Optional[Tuple[str, str]]:
    """
    Registers this host machine with the CloudPulse backend using an admin registration token.
    Returns (server_id, agent_token) upon success.
    """
    endpoint = f"{server_url.rstrip('/')}/api/agent/register"
    hostname = socket.gethostname()
    try:
        ip_address = socket.gethostbyname(hostname)
    except Exception:
        ip_address = "127.0.0.1"

    payload = {
        "registration_token": registration_token,
        "hostname": hostname,
        "server_name": server_name or hostname,
        "os": platform.system(),
        "os_version": f"{platform.release()} ({platform.version()})",
        "architecture": platform.machine(),
        "ip_address": ip_address
    }

    try:
        resp = requests.post(endpoint, json=payload, timeout=10)
        if resp.status_code in (200, 201):
            data = resp.json()
            server_id = data.get("server_id")
            agent_token = data.get("agent_token")
            logger.info(f"Agent successfully registered! Server ID: {server_id}")
            return server_id, agent_token
        else:
            logger.error(f"Registration failed: HTTP {resp.status_code} - {resp.text}")
            return None
    except Exception as e:
        logger.error(f"Failed to connect to backend for registration: {e}")
        return None
