export interface User {
  id: string;
  email: string;
  full_name: string | null;
  role: string;
  is_active: boolean;
  organization_id?: string;
  created_at: string;
}

export interface Server {
  id: string;
  organization_id: string;
  name: string;
  description?: string;
  hostname?: string;
  os?: string;
  os_version?: string;
  architecture?: string;
  ip_address?: string;
  status: 'online' | 'offline' | 'warning' | 'critical';
  last_heartbeat?: string;
  registration_token?: string;
  is_active: boolean;
  created_at: string;
  latest_cpu?: number | null;
  latest_ram?: number | null;
  latest_disk?: number | null;
}

export interface ServerRegisterToken {
  server_id: string;
  registration_token: string;
  registration_command_windows: string;
  registration_command_linux: string;
}

export interface MetricPoint {
  timestamp: string;
  cpu_percent: number;
  ram_percent: number;
  disk_percent: number;
  net_upload_speed: number;
  net_download_speed: number;
}

export interface ProcessItem {
  pid: number;
  name: string;
  username: string;
  status: string;
  cpu_percent: number;
  memory_percent: number;
  memory_bytes: number;
}

export interface ServerDetailedMetrics {
  server_id: string;
  has_metrics: boolean;
  message?: string;
  latest?: {
    id: string;
    timestamp: string;
    cpu_percent: number;
    cpu_per_core?: number[];
    cpu_frequency_current?: number;
    cpu_cores?: number;
    cpu_temperature?: number | null;
    ram_total: number;
    ram_used: number;
    ram_available: number;
    ram_percent: number;
    swap_percent?: number;
    disk_total: number;
    disk_used: number;
    disk_free: number;
    disk_percent: number;
    disk_read_speed: number;
    disk_write_speed: number;
    disk_io_ops: number;
    net_bytes_sent: number;
    net_bytes_recv: number;
    net_upload_speed: number;
    net_download_speed: number;
    raw_details?: any;
  };
  processes?: ProcessItem[];
}

export interface Alert {
  id: string;
  server_id: string;
  server_name?: string;
  metric_type: string;
  severity: 'warning' | 'critical';
  message: string;
  value?: number;
  threshold?: number;
  status: 'active' | 'acknowledged' | 'resolved';
  acknowledged_at?: string;
  resolved_at?: string;
  acknowledged_by?: string;
  resolved_by?: string;
  created_at: string;
}

export interface AnomalyLog {
  id: string;
  server_id: string;
  server_name?: string;
  timestamp: string;
  anomaly_score: number;
  is_anomaly: boolean;
  cpu_val?: number;
  ram_val?: number;
  disk_val?: number;
  net_val?: number;
  explanation?: string;
  created_at: string;
}

export interface ModelStatus {
  is_trained: boolean;
  model_name: string;
  algorithm: string;
  version: string;
  training_samples: number;
  last_trained?: string;
  status_message: string;
}

export interface Recommendation {
  id: string;
  server_id: string;
  server_name?: string;
  category: string;
  title: string;
  description: string;
  impact: string;
  suggested_action?: string;
  is_applied: boolean;
  created_at: string;
}

export interface OverviewStats {
  total_servers: number;
  online_servers: number;
  offline_servers: number;
  warning_servers: number;
  critical_servers: number;
  avg_cpu_percent: number;
  avg_ram_percent: number;
  avg_disk_percent: number;
  total_network_upload_speed: number;
  total_network_download_speed: number;
  active_alerts_count: number;
}
