"""Report Generator Agent for FHBG Eligibility Bot.

Generates user-friendly eligibility reports in multiple formats
(Markdown, PDF, HTML) using Jinja2 templates.
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass

from jinja2 import Environment, FileSystemLoader, select_autoescape

from src.agents.rule_interpreter import EligibilityReport, EligibilityStatus, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class ReportConfig:
    """Configuration for report generation."""
    output_dir: str = "reports/"
    template_dir: str = "src/chatbot/templates/"
    format: str = "markdown"  # markdown, html, pdf
    include_timestamp: bool = True
    include_qr_code: bool = False


class ReportGenerator:
    """Agent that generates eligibility reports in various formats."""

    def __init__(
        self,
        config: Optional[ReportConfig] = None,
        validate_paths: bool = True,
    ):
        """Initialize ReportGenerator.

        Args:
            config: Report generation configuration.
            validate_paths: If True, enforce output_dir within project/reports.
                           Set to False for tests using temporary directories.

        Security:
            Path traversal protection is applied when validate_paths=True.
        """
        self.config = config or ReportConfig()

        # Security: Validate output directory path to prevent directory traversal
        if validate_paths:
            project_root = Path(__file__).parent.parent.parent.resolve()
            output_path = Path(self.config.output_dir).resolve()
            allowed_root = (project_root / "reports").resolve()

            # Ensure output stays within allowed reports directory
            if not output_path.is_relative_to(allowed_root):
                raise ValueError(
                    f"output_dir must be within {allowed_root}. Got: {self.config.output_dir}"
                )

        self._ensure_output_dir()

        # Setup Jinja2 environment
        template_path = Path(self.config.template_dir)
        if template_path.exists():
            self.env = Environment(
                loader=FileSystemLoader(template_path),
                autoescape=select_autoescape(["html", "xml"]),
            )
        else:
            # Fallback to basic string templates
            self.env = None
            logger.warning(
                f"Template directory not found: {template_path}. "
                "Using basic templates."
            )

    def _ensure_output_dir(self) -> None:
        """Ensure output directory exists."""
        Path(self.config.output_dir).mkdir(parents=True, exist_ok=True)

    def generate_report(
        self,
        user_profile: Dict[str, Any],
        eligibility_report: Any,
        output_format: Optional[str] = None,
    ) -> str:
        """Generate an eligibility report.

        Args:
            user_profile: User's information dictionary.
            eligibility_report: EligibilityReport object from RuleInterpreter.
            output_format: Output format (markdown, html, pdf).

        Returns:
            Path to generated report file.
        """
        fmt = output_format or self.config.format
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

        # Prepare context
        context = {
            "user": user_profile,
            "report": eligibility_report,
            "timestamp": datetime.now(),
            "format": fmt,
        }

        # Generate based on format
        if fmt == "markdown":
            content = self._generate_markdown(context)
            extension = ".md"
        elif fmt == "html":
            content = self._generate_html(context)
            extension = ".html"
        else:
            logger.error(f"Unsupported format: {fmt}")
            return ""

        # Save to file
        filename = f"eligibility_report_{timestamp}{extension}"
        filepath = Path(self.config.output_dir) / filename

        try:
            with open(filepath, "w") as f:
                f.write(content)
            logger.info(f"Report saved to {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to save report: {e}")
            return ""

    def _generate_markdown(self, context: Dict[str, Any]) -> str:
        """Generate Markdown report."""
        user = context["user"]
        report = context["report"]

        # Build report content
        lines = [
            "# 🏡 First Home Buyer Grant Eligibility Report",
            "",
            f"**Generated:** {context['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
            "## 👤 Your Details",
            "",
        ]

        # User details
        details = [
            ("State", user.get("state", "N/A")),
            ("Annual Income", f"${user.get('income', 0):,.0f}"),
            ("Property Price", f"${user.get('property_price', 0):,.0f}"),
            ("First Home Buyer", "Yes" if user.get("first_home_buyer") else "No"),
            ("Citizenship Status", user.get("citizenship_status", "N/A")),
            ("Will Reside", "Yes" if user.get("will_reside") else "No"),
            ("Property Type", "New" if user.get("property_is_new") else "Existing"),
        ]

        for label, value in details:
            lines.append(f"| **{label}** | {value} |")
            lines.append("| --- | --- |")

        lines.extend(["", "---", "", "## 📊 Eligibility Result", ""])

        # Eligibility result
        if report.status.value == "eligible":
            lines.append(f"### ✅ Eligible")
            lines.append("")
            lines.append(f"**Grant:** {report.grant_name}")
            lines.append(f"**Amount:** ${report.grant_amount:,.0f}")
            lines.append("")
            lines.append("**Congratulations!** You meet all eligibility criteria.")
        else:
            lines.append(f"### ❌ Not Eligible")
            lines.append("")
            lines.append(f"**Grant:** {report.grant_name}")
            lines.append("")
            if report.missing_requirements:
                lines.append("**Missing requirements:**")
                for req in report.missing_requirements:
                    lines.append(f"- {req}")

        lines.extend(["", "---", "", "## 📋 Next Steps", ""])

        for step in report.next_steps:
            lines.append(f"- {step}")

        lines.extend(["", "---", "", "## 📚 Sources", ""])
        for source in report.sources:
            lines.append(f"- {source}")

        lines.extend(["", "---", ""])
        lines.append(
            "> **Disclaimer:** This report is for informational purposes only. "
            "Please verify all details with the official government website."
        )

        return "\n".join(lines)

    def _generate_html(self, context: Dict[str, Any]) -> str:
        """Generate HTML report."""
        if self.env and Path(self.config.template_dir + "/report.html.j2").exists():
            template = self.env.get_template("report.html.j2")
            return template.render(**context)
        else:
            return self._generate_basic_html(context)

    def _generate_basic_html(self, context: Dict[str, Any]) -> str:
        """Generate basic HTML report without templates."""
        user = context["user"]
        report = context["report"]

        status_color = "#28a745" if report.status.value == "eligible" else "#dc3545"
        status_text = "ELIGIBLE" if report.status.value == "eligible" else "NOT ELIGIBLE"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FHBG Eligibility Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{ color: #333; }}
        .header {{
            background: {status_color};
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .section {{
            margin: 20px 0;
            padding: 15px;
            border-left: 4px solid #007bff;
            background: #f8f9fa;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 10px 0;
        }}
        td {{
            padding: 8px;
            border-bottom: 1px solid #ddd;
        }}
        .eligible {{ color: {status_color}; font-weight: bold; }}
        .grant-amount {{
            font-size: 24px;
            color: {status_color};
            font-weight: bold;
        }}
        .next-steps {{
            background: #d1ecf1;
            padding: 15px;
            border-radius: 5px;
        }}
        .footer {{
            margin-top: 30px;
            font-size: 12px;
            color: #666;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>🏡 First Home Buyer Grant Eligibility Report</h1>
        <p><em>Generated: {context['timestamp'].strftime('%Y-%m-%d %H:%M:%S')}</em></p>

        <div class="header">
            <h2>Status: <span class="eligible">{status_text}</span></h2>
            <p>Grant: {report.grant_name}</p>
            <p class="grant-amount">${report.grant_amount:,.0f}</p>
        </div>

        <div class="section">
            <h3>👤 Your Details</h3>
            <table>
                <tr><td><strong>State</strong></td><td>{user.get('state', 'N/A')}</td></tr>
                <tr><td><strong>Annual Income</strong></td><td>${user.get('income', 0):,.0f}</td></tr>
                <tr><td><strong>Property Price</strong></td><td>${user.get('property_price', 0):,.0f}</td></tr>
                <tr><td><strong>First Home Buyer</strong></td><td>{"Yes" if user.get("first_home_buyer") else "No"}</td></tr>
                <tr><td><strong>Citizenship Status</strong></td><td>{user.get('citizenship_status', 'N/A')}</td></tr>
                <tr><td><strong>Will Reside</strong></td><td>{"Yes" if user.get("will_reside") else "No"}</td></tr>
            </table>
        </div>

        <div class="section">
            <h3>📋 Next Steps</h3>
            <div class="next-steps">
                <ul>
        """

        for step in report.next_steps:
            html += f"<li>{step}</li>\n"

        html += """
                </ul>
            </div>
        </div>

        <div class="section">
            <h3>📚 Sources</h3>
            <ul>
        """

        for source in report.sources:
            html += f"<li><a href='{source}'>{source}</a></li>\n"

        html += """
            </ul>
        </div>

        <div class="footer">
            <p>This report is for informational purposes only. Please verify all details with official sources.</p>
        </div>
    </div>
</body>
</html>
"""

        return html

    def generate_summary_card(
        self,
        user_profile: Dict[str, Any],
        eligibility_report: Any,
    ) -> str:
        """Generate a compact summary card (for chat display).

        Args:
            user_profile: User's information dictionary.
            eligibility_report: EligibilityReport object.

        Returns:
            Markdown string of summary card.
        """
        if eligibility_report.status.value == "eligible":
            emoji = "✅"
            status = "ELIGIBLE"
            color = "green"
        else:
            emoji = "❌"
            status = "NOT ELIGIBLE"
            color = "red"

        card = f"""
<div style="border: 2px solid {color}; border-radius: 10px; padding: 15px; margin: 10px 0;">
  <h3 style="margin-top: 0;">{emoji} {eligibility_report.grant_name}</h3>
  <p><strong>Status:</strong> {status}</p>
  <p><strong>Grant Amount:</strong> ${eligibility_report.grant_amount:,.0f}</p>
  <p><strong>State:</strong> {user_profile.get('state', 'N/A')}</p>
</div>

"""

        # Add brief next steps
        if eligibility_report.next_steps:
            card += "\n**Next Steps:**\n"
            for step in eligibility_report.next_steps[:3]:
                card += f"- {step}\n"

        return card


def main():
    """CLI interface for report generator."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Generate eligibility report")
    parser.add_argument("--input", required=True, help="JSON file with user data and report")
    parser.add_argument("--output-dir", default="reports/", help="Output directory")
    parser.add_argument("--format", default="markdown", choices=["markdown", "html"], help="Output format")

    args = parser.parse_args()

    # Load input data
    try:
        with open(args.input, "r") as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load input file: {e}")
        return 1

    user_profile = data.get("user_profile", {})
    report_data = data.get("eligibility_report", {})

    # Convert report_data back to EligibilityReport object (simplified)
    from src.agents.rule_interpreter import EligibilityReport, EligibilityStatus

    report = EligibilityReport(
        status=EligibilityStatus(report_data.get("status", "not_eligible")),
        state=report_data.get("state", ""),
        grant_amount=report_data.get("grant_amount", 0),
        grant_name=report_data.get("grant_name", ""),
        passed_rules=report_data.get("passed_rules", []),
        failed_rules=[
            ValidationResult(
                rule_name=v.get("rule_name", ""),
                passed=False,
                user_value=v.get("user_value"),
                required_value=v.get("required_value"),
                message=v.get("message", "")
            )
            for v in report_data.get("failed_rules", [])
        ],
        warnings=report_data.get("warnings", []),
        missing_requirements=report_data.get("missing_requirements", []),
        next_steps=report_data.get("next_steps", []),
        sources=report_data.get("sources", []),
    )
            for v in report_data.get("failed_rules", [])
        ],
        warnings=report_data.get("warnings", []),
        missing_requirements=report_data.get("missing_requirements", []),
        next_steps=report_data.get("next_steps", []),
        sources=report_data.get("sources", []),
    )

    # Generate report
    config = ReportConfig(output_dir=args.output_dir, format=args.format)
    generator = ReportGenerator(config)
    output_path = generator.generate_report(user_profile, report)

    if output_path:
        print(f"✅ Report generated: {output_path}")
        return 0
    else:
        print("❌ Failed to generate report")
        return 1


if __name__ == "__main__":
    exit(main())
