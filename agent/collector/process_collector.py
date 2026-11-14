"""
CloudPulse Process Metrics Collector
Safely queries process information with robust permission handling.
"""
from typing import List, Dict, Any
import psutil


class ProcessCollector:
    """Collects top CPU and memory consuming processes without crashing on permission errors."""

    @staticmethod
    def collect_top_processes(limit: int = 10) -> Dict[str, List[Dict[str, Any]]]:
        processes = []

        # Iterate over processes safely
        for proc in psutil.process_iter(attrs=['pid', 'name', 'username', 'status', 'cpu_percent', 'memory_percent', 'memory_info']):
            try:
                info = proc.info
                # Some OSes return None or 0.0 initially for cpu_percent unless sampled twice
                cpu_p = info.get('cpu_percent') or 0.0
                mem_p = info.get('memory_percent') or 0.0
                mem_info = info.get('memory_info')
                rss_bytes = mem_info.rss if mem_info else 0

                processes.append({
                    "pid": info.get('pid'),
                    "name": info.get('name') or "Unknown",
                    "username": info.get('username') or "N/A",
                    "status": str(info.get('status') or "unknown"),
                    "cpu_percent": round(float(cpu_p), 2),
                    "memory_percent": round(float(mem_p), 2),
                    "memory_bytes": rss_bytes
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
            except Exception:
                continue

        # Sort top CPU
        top_cpu = sorted(processes, key=lambda p: p["cpu_percent"], reverse=True)[:limit]
        # Sort top RAM
        top_memory = sorted(processes, key=lambda p: p["memory_percent"], reverse=True)[:limit]

        return {
            "top_cpu": top_cpu,
            "top_memory": top_memory
        }
