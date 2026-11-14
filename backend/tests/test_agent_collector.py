"""
Tests for Real-time System Collector & Process Telemetry
"""
import time
from agent.collector.system_collector import SystemCollector
from agent.collector.process_collector import ProcessCollector


def test_cpu_collection():
    collector = SystemCollector(agent_version="1.0.0")
    cpu_data = collector.collect_cpu_metrics()

    assert "cpu_percent" in cpu_data
    assert isinstance(cpu_data["cpu_percent"], float)
    assert 0.0 <= cpu_data["cpu_percent"] <= 100.0
    assert "cpu_per_core" in cpu_data
    assert isinstance(cpu_data["cpu_per_core"], list)
    assert len(cpu_data["cpu_per_core"]) > 0
    assert "cpu_cores_logical" in cpu_data
    assert cpu_data["cpu_cores_logical"] >= 1


def test_memory_collection():
    collector = SystemCollector(agent_version="1.0.0")
    mem_data = collector.collect_memory_metrics()

    assert "ram_total" in mem_data
    assert "ram_used" in mem_data
    assert "ram_available" in mem_data
    assert "ram_percent" in mem_data
    assert mem_data["ram_total"] > 0
    assert 0.0 <= mem_data["ram_percent"] <= 100.0


def test_disk_collection():
    collector = SystemCollector(agent_version="1.0.0")
    disk_data = collector.collect_disk_metrics()

    assert "disk_total" in disk_data
    assert "disk_used" in disk_data
    assert "disk_free" in disk_data
    assert "disk_percent" in disk_data
    assert disk_data["disk_total"] > 0
    assert 0.0 <= disk_data["disk_percent"] <= 100.0
    assert "disk_read_bytes" in disk_data
    assert "disk_write_bytes" in disk_data


def test_network_calculations():
    collector = SystemCollector(agent_version="1.0.0")
    net1 = collector.collect_network_metrics()
    assert "bytes_sent" in net1
    assert "bytes_recv" in net1

    # Brief delay to test bandwidth throughput delta calculation
    time.sleep(0.5)
    net2 = collector.collect_network_metrics()
    assert "upload_speed_bytes_sec" in net2
    assert "download_speed_bytes_sec" in net2
    assert net2["upload_speed_bytes_sec"] >= 0.0
    assert net2["download_speed_bytes_sec"] >= 0.0


def test_process_collector():
    procs = ProcessCollector.collect_top_processes(limit=5)
    assert "top_cpu" in procs
    assert "top_memory" in procs
    assert len(procs["top_cpu"]) <= 5
    assert len(procs["top_memory"]) <= 5

    if procs["top_cpu"]:
        p = procs["top_cpu"][0]
        assert "pid" in p
        assert "name" in p
        assert "cpu_percent" in p
        assert "memory_percent" in p
