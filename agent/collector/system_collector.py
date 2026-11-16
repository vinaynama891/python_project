"""
CloudPulse Real-time System Collector
Collects authentic host machine telemetry using psutil, platform, and socket.
"""
import time
import socket
import platform
from datetime import datetime, timezone
from typing import Dict, Any, Optional

import psutil
try:
    from agent.collector.process_collector import ProcessCollector
except ImportError:
    from collector.process_collector import ProcessCollector


class SystemCollector:
    def __init__(self, agent_version: str = "1.0.0"):
        self.agent_version = agent_version
        self._last_net_time: Optional[float] = None
        self._last_bytes_sent: Optional[int] = None
        self._last_bytes_recv: Optional[int] = None

        self._last_disk_time: Optional[float] = None
        self._last_disk_read_bytes: Optional[int] = None
        self._last_disk_write_bytes: Optional[int] = None

        # Prime initial cpu_percent reading for accurate subsequent values
        try:
            psutil.cpu_percent(interval=None)
            psutil.cpu_percent(percpu=True, interval=None)
        except Exception:
            pass

    def collect_static_info(self) -> Dict[str, Any]:
        """Collect static machine identification and hardware profile."""
        hostname = socket.gethostname()
        try:
            ip_address = socket.gethostbyname(hostname)
        except Exception:
            ip_address = "127.0.0.1"

        boot_time = psutil.boot_time()
        uptime_seconds = round(time.time() - boot_time, 2)

        return {
            "hostname": hostname,
            "ip_address": ip_address,
            "os": platform.system(),
            "os_version": f"{platform.release()} ({platform.version()})",
            "architecture": platform.machine(),
            "cpu_cores_physical": psutil.cpu_count(logical=False) or 1,
            "cpu_cores_logical": psutil.cpu_count(logical=True) or 1,
            "boot_time": datetime.fromtimestamp(boot_time, tz=timezone.utc).isoformat(),
            "uptime_seconds": uptime_seconds,
            "agent_version": self.agent_version,
            "agent_health": "healthy"
        }

    def collect_cpu_metrics(self) -> Dict[str, Any]:
        """Collect detailed CPU utilization, frequencies, and temperature."""
        cpu_total = psutil.cpu_percent(interval=None)
        per_core = psutil.cpu_percent(percpu=True, interval=None)

        freq_info = {
            "current": 0.0,
            "min": 0.0,
            "max": 0.0
        }
        try:
            f = psutil.cpu_freq()
            if f:
                freq_info = {
                    "current": round(float(f.current), 2) if f.current else 0.0,
                    "min": round(float(f.min), 2) if f.min else 0.0,
                    "max": round(float(f.max), 2) if f.max else 0.0
                }
        except Exception:
            pass

        temperature = None
        try:
            if hasattr(psutil, "sensors_temperatures"):
                temps = psutil.sensors_temperatures()
                if temps:
                    # Pick the first available CPU temperature sensor
                    for name, entries in temps.items():
                        if entries and len(entries) > 0:
                            temperature = round(entries[0].current, 1)
                            break
        except Exception:
            temperature = None

        return {
            "cpu_percent": round(float(cpu_total), 2),
            "cpu_per_core": [round(float(c), 2) for c in per_core],
            "cpu_frequency": freq_info,
            "cpu_cores_logical": psutil.cpu_count(logical=True) or 1,
            "cpu_cores_physical": psutil.cpu_count(logical=False) or 1,
            "cpu_temperature": temperature
        }

    def collect_memory_metrics(self) -> Dict[str, Any]:
        """Collect real virtual memory and swap statistics."""
        vm = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return {
            "ram_total": vm.total,
            "ram_used": vm.used,
            "ram_available": vm.available,
            "ram_percent": round(float(vm.percent), 2),
            "swap_total": swap.total,
            "swap_used": swap.used,
            "swap_free": swap.free,
            "swap_percent": round(float(swap.percent), 2)
        }

    def collect_disk_metrics(self) -> Dict[str, Any]:
        """Collect primary partition disk usage and disk I/O rates."""
        # Detect root partition path for Windows or Unix
        root_path = "C:\\" if platform.system() == "Windows" else "/"
        try:
            usage = psutil.disk_usage(root_path)
        except Exception:
            usage = psutil.disk_usage(".")

        io = None
        try:
            io = psutil.disk_io_counters()
        except Exception:
            pass

        now = time.time()
        read_bytes = io.read_bytes if io else 0
        write_bytes = io.write_bytes if io else 0
        read_count = io.read_count if io else 0
        write_count = io.write_count if io else 0

        disk_read_speed = 0.0
        disk_write_speed = 0.0

        if self._last_disk_time is not None and now > self._last_disk_time:
            dt = now - self._last_disk_time
            if dt > 0 and self._last_disk_read_bytes is not None and self._last_disk_write_bytes is not None:
                disk_read_speed = max(0.0, (read_bytes - self._last_disk_read_bytes) / dt)
                disk_write_speed = max(0.0, (write_bytes - self._last_disk_write_bytes) / dt)

        self._last_disk_time = now
        self._last_disk_read_bytes = read_bytes
        self._last_disk_write_bytes = write_bytes

        return {
            "disk_total": usage.total,
            "disk_used": usage.used,
            "disk_free": usage.free,
            "disk_percent": round(float(usage.percent), 2),
            "disk_read_bytes": read_bytes,
            "disk_write_bytes": write_bytes,
            "disk_io_operations": read_count + write_count,
            "disk_read_speed_bytes_sec": round(disk_read_speed, 2),
            "disk_write_speed_bytes_sec": round(disk_write_speed, 2)
        }

    def collect_network_metrics(self) -> Dict[str, Any]:
        """Collect network I/O counters, compute bandwidth throughput, and list interfaces."""
        net_io = psutil.net_io_counters()
        now = time.time()

        bytes_sent = net_io.bytes_sent
        bytes_recv = net_io.bytes_recv
        packets_sent = net_io.packets_sent
        packets_recv = net_io.packets_recv

        upload_speed = 0.0
        download_speed = 0.0

        if self._last_net_time is not None and now > self._last_net_time:
            dt = now - self._last_net_time
            if dt > 0 and self._last_bytes_sent is not None and self._last_bytes_recv is not None:
                upload_speed = max(0.0, (bytes_sent - self._last_bytes_sent) / dt)
                download_speed = max(0.0, (bytes_recv - self._last_bytes_recv) / dt)

        self._last_net_time = now
        self._last_bytes_sent = bytes_sent
        self._last_bytes_recv = bytes_recv

        # Interface information
        interfaces = []
        try:
            addrs = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            for if_name, if_addresses in addrs.items():
                is_up = stats[if_name].isup if if_name in stats else False
                ip = None
                for addr in if_addresses:
                    if addr.family == socket.AF_INET:
                        ip = addr.address
                        break
                interfaces.append({
                    "name": if_name,
                    "ip": ip or "N/A",
                    "is_up": is_up
                })
        except Exception:
            pass

        return {
            "bytes_sent": bytes_sent,
            "bytes_recv": bytes_recv,
            "upload_speed_bytes_sec": round(upload_speed, 2),
            "download_speed_bytes_sec": round(download_speed, 2),
            "packets_sent": packets_sent,
            "packets_recv": packets_recv,
            "interfaces": interfaces
        }

    def collect_all_metrics(self) -> Dict[str, Any]:
        """Gathers the comprehensive snapshot of real hardware and process metrics."""
        timestamp = datetime.now(timezone.utc).isoformat()
        static_info = self.collect_static_info()
        cpu_metrics = self.collect_cpu_metrics()
        mem_metrics = self.collect_memory_metrics()
        disk_metrics = self.collect_disk_metrics()
        net_metrics = self.collect_network_metrics()
        processes = ProcessCollector.collect_top_processes(limit=10)

        return {
            "timestamp": timestamp,
            "system": static_info,
            "cpu": cpu_metrics,
            "memory": mem_metrics,
            "disk": disk_metrics,
            "network": net_metrics,
            "processes": processes
        }
