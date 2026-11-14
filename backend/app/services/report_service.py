"""
CloudPulse Reporting Service
Generates daily/weekly executive performance summaries and exports CSV and PDF documents.
"""
import io
import csv
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.models import Server, Metric, Alert
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


class ReportService:
    @staticmethod
    def get_summary_report(db: Session, org_id: str, days: int = 1) -> Dict[str, Any]:
        """Calculates statistical summary for the specified time window."""
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(days=days)

        servers = db.query(Server).filter(Server.organization_id == org_id).all()
        server_ids = [s.id for s in servers]

        if not server_ids:
            return {
                "period_days": days,
                "server_count": 0,
                "metrics_analyzed": 0,
                "avg_cpu": 0.0,
                "max_cpu": 0.0,
                "avg_ram": 0.0,
                "avg_disk": 0.0,
                "total_alerts": 0,
                "resolved_alerts": 0,
                "server_breakdown": []
            }

        # Query metrics
        metrics = db.query(Metric).filter(
            Metric.server_id.in_(server_ids),
            Metric.timestamp >= start_time
        ).all()

        total_alerts = db.query(Alert).filter(
            Alert.organization_id == org_id,
            Alert.created_at >= start_time
        ).count()

        resolved_alerts = db.query(Alert).filter(
            Alert.organization_id == org_id,
            Alert.created_at >= start_time,
            Alert.status == "resolved"
        ).count()

        if not metrics:
            return {
                "period_days": days,
                "server_count": len(servers),
                "metrics_analyzed": 0,
                "avg_cpu": 0.0,
                "max_cpu": 0.0,
                "avg_ram": 0.0,
                "avg_disk": 0.0,
                "total_alerts": total_alerts,
                "resolved_alerts": resolved_alerts,
                "server_breakdown": [{"id": s.id, "name": s.name, "status": s.status} for s in servers]
            }

        avg_cpu = sum(m.cpu_percent for m in metrics) / len(metrics)
        max_cpu = max(m.cpu_percent for m in metrics)
        avg_ram = sum(m.ram_percent for m in metrics) / len(metrics)
        avg_disk = sum(m.disk_percent for m in metrics) / len(metrics)

        # Server breakdown
        breakdown = []
        for s in servers:
            s_metrics = [m for m in metrics if m.server_id == s.id]
            if s_metrics:
                s_avg_cpu = sum(m.cpu_percent for m in s_metrics) / len(s_metrics)
                s_avg_ram = sum(m.ram_percent for m in s_metrics) / len(s_metrics)
                s_avg_disk = sum(m.disk_percent for m in s_metrics) / len(s_metrics)
            else:
                s_avg_cpu = s_avg_ram = s_avg_disk = 0.0

            breakdown.append({
                "server_id": s.id,
                "name": s.name,
                "status": s.status,
                "avg_cpu": round(s_avg_cpu, 1),
                "avg_ram": round(s_avg_ram, 1),
                "avg_disk": round(s_avg_disk, 1),
                "data_points": len(s_metrics)
            })

        return {
            "period_days": days,
            "server_count": len(servers),
            "metrics_analyzed": len(metrics),
            "avg_cpu": round(avg_cpu, 2),
            "max_cpu": round(max_cpu, 2),
            "avg_ram": round(avg_ram, 2),
            "avg_disk": round(avg_disk, 2),
            "total_alerts": total_alerts,
            "resolved_alerts": resolved_alerts,
            "server_breakdown": breakdown
        }

    @staticmethod
    def generate_csv(db: Session, org_id: str, days: int = 7) -> str:
        """Generates CSV text of historical metric data points."""
        now = datetime.now(timezone.utc)
        start_time = now - timedelta(days=days)

        servers = {s.id: s.name for s in db.query(Server).filter(Server.organization_id == org_id).all()}
        metrics = db.query(Metric).filter(
            Metric.server_id.in_(servers.keys()),
            Metric.timestamp >= start_time
        ).order_by(Metric.timestamp.desc()).limit(1000).all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Timestamp", "Server Name", "CPU Percent", "RAM Percent", "RAM Used (GB)",
            "Disk Percent", "Disk Read Speed (B/s)", "Disk Write Speed (B/s)",
            "Net Upload Speed (B/s)", "Net Download Speed (B/s)"
        ])

        for m in metrics:
            writer.writerow([
                m.timestamp.isoformat(),
                servers.get(m.server_id, "Unknown"),
                f"{m.cpu_percent:.2f}",
                f"{m.ram_percent:.2f}",
                f"{m.ram_used / 1e9:.2f}",
                f"{m.disk_percent:.2f}",
                f"{m.disk_read_speed:.1f}",
                f"{m.disk_write_speed:.1f}",
                f"{m.net_upload_speed:.1f}",
                f"{m.net_download_speed:.1f}"
            ])

        return output.getvalue()

    @staticmethod
    def generate_pdf(db: Session, org_id: str, days: int = 7) -> bytes:
        """Generates a professional PDF performance report using ReportLab."""
        summary = ReportService.get_summary_report(db, org_id, days=days)

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0f172a")
        )
        subtitle_style = ParagraphStyle(
            'SubTitleStyle',
            parent=styles['Normal'],
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#475569")
        )

        elements = []
        elements.append(Paragraph("CloudPulse Executive Infrastructure Report", title_style))
        elements.append(Paragraph(f"Generated on {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} | Window: Last {days} Days", subtitle_style))
        elements.append(Spacer(1, 15))

        # Executive Metrics Table
        data_summary = [
            ["Metric", "Value", "Metric", "Value"],
            ["Total Servers", str(summary["server_count"]), "Metrics Ingested", str(summary["metrics_analyzed"])],
            ["Average CPU Load", f"{summary['avg_cpu']}%", "Peak CPU Load", f"{summary['max_cpu']}%"],
            ["Average RAM Load", f"{summary['avg_ram']}%", "Average Disk Load", f"{summary['avg_disk']}%"],
            ["Total Alerts Triggered", str(summary["total_alerts"]), "Resolved Alerts", str(summary["resolved_alerts"])]
        ]

        t_summary = Table(data_summary, colWidths=[140, 110, 140, 110])
        t_summary.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#f8fafc"), colors.white])
        ]))
        elements.append(t_summary)
        elements.append(Spacer(1, 20))

        # Server Breakdown Table
        elements.append(Paragraph("Individual Server Performance Breakdown", styles['Heading2']))
        elements.append(Spacer(1, 8))

        server_table_data = [["Server Name", "Status", "Avg CPU", "Avg RAM", "Avg Disk", "Samples"]]
        for s in summary["server_breakdown"]:
            server_table_data.append([
                s["name"],
                s["status"].upper(),
                f"{s['avg_cpu']}%",
                f"{s['avg_ram']}%",
                f"{s['avg_disk']}%",
                str(s["data_points"])
            ])

        t_servers = Table(server_table_data, colWidths=[150, 70, 70, 70, 70, 70])
        t_servers.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0284c7")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#f1f5f9")])
        ]))
        elements.append(t_servers)

        doc.build(elements)
        return buffer.getvalue()


report_service = ReportService()
