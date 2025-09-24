import csv  # Added csv
import json
import os
import re
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

# Conditional import for tomllib
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib  # Use tomli and alias it as tomllib
    except ImportError:
        tomllib = None  # type: ignore

import yaml
from reportlab.lib import colors
from reportlab.lib.pagesizes import portrait, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Flowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
    ListFlowable, 
    ListItem, 
    PageBreak,
)
from reportlab.lib.units import inch
from rich.console import Console

from aws_finops_dashboard.types import ProfileData
from aws_finops_dashboard.pdf_utils import (
    paragraphStyling,
    sectionHeading,
    miniHeader,
    keyValueTable,
    bulletList,
    formatServicesForList,
)

console = Console()


styles = getSampleStyleSheet()

# Custom style for the footer
pdf_footer_style = ParagraphStyle(
    name="PDF_Footer",
    parent=styles["Normal"],
    fontSize=8,
    textColor=colors.grey,
    alignment=1,
    leading=10,
)


def export_audit_report_to_pdf(
    audit_data_list: List[Dict[str, str]],
    file_name: str = "audit_report",
    path: Optional[str] = None,
) -> Optional[str]:
    """
    Export the audit report to a PDF file.

    :param audit_data_list: List of dictionaries, each representing a profile/account's audit data.
    :param file_name: The base name of the output PDF file.
    :param path: Optional directory where the PDF file will be saved.
    :return: Full path of the generated PDF file or None on error.
    """
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        base_filename = f"{file_name}_{timestamp}.pdf"

        if path:
            os.makedirs(path, exist_ok=True)
            output_filename = os.path.join(path, base_filename)
        else:
            output_filename = base_filename

        doc = SimpleDocTemplate(output_filename, pagesize=landscape(letter))
        styles = getSampleStyleSheet()
        elements: List[Flowable] = []

        headers = [
            "Profile",
            "Account ID",
            "Untagged Resources",
            "Stopped EC2 Instances",
            "Unused Volumes",
            "Unused EIPs",
            "Budget Alerts",
        ]
        table_data = [headers]

        for row in audit_data_list:
            table_data.append(
                [
                    row.get("profile", ""),
                    row.get("account_id", ""),
                    row.get("untagged_resources", ""),
                    row.get("stopped_instances", ""),
                    row.get("unused_volumes", ""),
                    row.get("unused_eips", ""),
                    row.get("budget_alerts", ""),
                ]
            )

        table = Table(table_data, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.black),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
                    ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("GRID", (0, 0), (-1, -1), 0.25, colors.black),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                ]
            )
        )

        elements.append(
            Paragraph("AWS FinOps Dashboard (Audit Report)", styles["Title"])
        )
        elements.append(Spacer(1, 12))
        elements.append(table)
        elements.append(Spacer(1, 4))
        elements.append(
            Paragraph(
                "Note: This table lists untagged EC2, RDS, Lambda, ELBv2 only.",
                pdf_footer_style,
            )
        )
        elements.append(Spacer(1, 2))
        current_time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        footer_text = f"This audit report is generated using AWS FinOps Dashboard (CLI) \u00a9 2025 on {current_time_str}"
        elements.append(Paragraph(footer_text, pdf_footer_style))

        doc.build(elements)
        return output_filename
    except Exception as e:
        console.print(f"[bold red]Error exporting audit report to PDF: {str(e)}[/]")
        return None


def clean_rich_tags(text: str) -> str:
    """
    Clean the rich text before writing the data to a pdf.

    :param text: The rich text to clean.
    :return: Cleaned text.
    """
    return re.sub(r"\[/?[a-zA-Z0-9#_]*\]", "", text)


def export_audit_report_to_csv(
    audit_data_list: List[Dict[str, str]],
    file_name: str = "audit_report",
    path: Optional[str] = None,
) -> Optional[str]:
    """Export the audit report to a CSV file."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        base_filename = f"{file_name}_{timestamp}.csv"
        output_filename = base_filename
        if path:
            os.makedirs(path, exist_ok=True)
            output_filename = os.path.join(path, base_filename)

        headers = [
            "Profile",
            "Account ID",
            "Untagged Resources",
            "Stopped EC2 Instances",
            "Unused Volumes",
            "Unused EIPs",
            "Budget Alerts",
        ]
        # Corresponding keys in the audit_data_list dictionaries
        data_keys = [
            "profile",
            "account_id",
            "untagged_resources",
            "stopped_instances",
            "unused_volumes",
            "unused_eips",
            "budget_alerts",
        ]

        with open(output_filename, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            for item in audit_data_list:
                writer.writerow([item.get(key, "") for key in data_keys])
        return output_filename
    except Exception as e:
        console.print(f"[bold red]Error exporting audit report to CSV: {str(e)}[/]")
        return None

def export_audit_report_to_json(
        raw_audit_data: List[Dict[str, Any]],
        file_name: str = "audit_report",
        path: Optional[str] = None) -> Optional[str]:
    """Export the audit report to a JSON file."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        base_filename = f"{file_name}_{timestamp}.json"
        output_filename = base_filename
        if path:
            os.makedirs(path, exist_ok=True)
            output_filename = os.path.join(path, base_filename)

        with open(output_filename, "w", encoding="utf-8") as jsonfile:
            json.dump(raw_audit_data, jsonfile, indent=4) # Use the structured list
        return output_filename
    except Exception as e:
        console.print(f"[bold red]Error exporting audit report to JSON: {str(e)}[/]")
        return None
    
def export_trend_data_to_json(
    trend_data: List[Dict[str, Any]],
    file_name: str = "trend_data",
    path: Optional[str] = None) -> Optional[str]:
    """Export trend data to a JSON file."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        base_filename = f"{file_name}_{timestamp}.json"
        output_filename = base_filename
        if path:
            os.makedirs(path, exist_ok=True)
            output_filename = os.path.join(path, base_filename)

        with open(output_filename, "w", encoding="utf-8") as jsonfile:
            json.dump(trend_data, jsonfile, indent=4)
        return output_filename
    except Exception as e:
        console.print(f"[bold red]Error exporting trend data to JSON: {str(e)}[/]")
        return None
    
def export_cost_dashboard_to_pdf(
    data: List[ProfileData],
    filename: str,
    output_dir: Optional[str] = None,
    previous_period_dates: str = "N/A",
    current_period_dates: str = "N/A",
) -> Optional[str]:
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        base_filename = f"{filename}_{timestamp}.pdf"

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            output_filename = os.path.join(output_dir, base_filename)
        else:
            output_filename = base_filename
        
        doc = SimpleDocTemplate(
            output_filename,
            pagesize=portrait(letter),
            leftMargin=0.5*inch,
            rightMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch,
            allowSplitting=True,
        )

        elements: List[Flowable] = []
        elements.append(Paragraph("AWS FinOps Dashboard (Cost Report)", styles["Title"]))
        elements.append(Spacer(1, 10))

        elements.append(paragraphStyling(f"<b>Previous Period:</b> {previous_period_dates}<br/><b>Current Period:</b> {current_period_dates}"))
        elements.append(Spacer(1, 6))

        for idx, row in enumerate(data):
            header_tbl = Table(
                [[paragraphStyling(f"<b>Profile:</b> {row['profile']}  &nbsp;&nbsp;&nbsp; "
                     f"<b>Account:</b> {row['account_id']}")]],
                colWidths=[doc.width],
                hAlign="LEFT",
            )
            header_tbl.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
                ("BOX", (0, 0), (-1, -1), 0.25, colors.grey),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            elements.append(header_tbl)
            elements.append(Spacer(1, 6))

            kv_rows = [
                ("Previous Period Cost", f"<b>${row['last_month']:.2f}</b>"),
                ("Current Period Cost", f"<b>${row['current_month']:.2f}</b>"),
            ]
            elements.append(keyValueTable(kv_rows))
            elements.append(Spacer(1, 6))

            elements.append(miniHeader("Cost By Service"))
            svc_items = formatServicesForList(row["service_costs"])
            elements.append(bulletList(svc_items))
            elements.append(Spacer(1, 6))

            elements.append(miniHeader("Budget Status"))
            budgets = row["budget_info"] if row["budget_info"] else ["No budgets"]
            elements.append(bulletList(budgets))
            elements.append(Spacer(1, 6))

            elements.append(miniHeader("EC2 Instances"))
            ec2_items = [f"{state}: {count}" for state, count in row["ec2_summary"].items() if count > 0] or ["No instances"]
            elements.append(bulletList(ec2_items))

            if idx < len(data) - 1:
                elements.append(Spacer(1, 14))

        elements.append(Spacer(1, 8))
        footer_text = f"This report is generated using AWS FinOps Dashboard (CLI) \u00a9 2025 on {datetime.now():%Y-%m-%d %H:%M:%S}"
        elements.append(Paragraph(footer_text, pdf_footer_style))

        doc.build(elements)
        return os.path.abspath(output_filename)
    except Exception as e:
        console.print(f"[bold red]Error exporting to PDF: {str(e)}[/]")
        return None


def load_config_file(file_path: str) -> Optional[Dict[str, Any]]:
    """Load configuration from TOML, YAML, or JSON file."""
    _, file_extension = os.path.splitext(file_path)
    file_extension = file_extension.lower()

    try:
        with open(file_path, "rb" if file_extension == ".toml" else "r") as f:
            if file_extension == ".toml":
                if tomllib is None:
                    console.print(
                        f"[bold red]Error: TOML library (tomli) not installed for Python < 3.11. Please install it.[/]"
                    )
                    return None
                loaded_data = tomllib.load(f)
                if isinstance(loaded_data, dict):
                    return loaded_data
                console.print(
                    f"[bold red]Error: TOML file {file_path} did not load as a dictionary.[/]"
                )
                return None
            elif file_extension in [".yaml", ".yml"]:
                loaded_data = yaml.safe_load(f)
                if isinstance(loaded_data, dict):
                    return loaded_data
                console.print(
                    f"[bold red]Error: YAML file {file_path} did not load as a dictionary.[/]"
                )
                return None
            elif file_extension == ".json":
                loaded_data = json.load(f)
                if isinstance(loaded_data, dict):
                    return loaded_data
                console.print(
                    f"[bold red]Error: JSON file {file_path} did not load as a dictionary.[/]"
                )
                return None
            else:
                console.print(
                    f"[bold red]Error: Unsupported configuration file format: {file_extension}[/]"
                )
                return None
    except FileNotFoundError:
        console.print(f"[bold red]Error: Configuration file not found: {file_path}[/]")
        return None
    except tomllib.TOMLDecodeError as e:
        console.print(f"[bold red]Error decoding TOML file {file_path}: {e}[/]")
        return None
    except yaml.YAMLError as e:
        console.print(f"[bold red]Error decoding YAML file {file_path}: {e}[/]")
        return None
    except json.JSONDecodeError as e:
        console.print(f"[bold red]Error decoding JSON file {file_path}: {e}[/]")
        return None
    except Exception as e:
        console.print(f"[bold red]Error loading configuration file {file_path}: {e}[/]")
        return None
