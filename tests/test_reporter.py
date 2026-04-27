"""Unit tests for reporter agent."""

import os
import tempfile
from pathlib import Path
import pytest

from src.agents.reporter import ReportGenerator, ReportConfig
from src.agents.rule_interpreter import EligibilityReport, EligibilityStatus


class TestReportGenerator:
    """Test suite for ReportGenerator."""

    @pytest.fixture
    def sample_report(self):
        """Create a sample EligibilityReport."""
        return EligibilityReport(
            status=EligibilityStatus.ELIGIBLE,
            state="NSW",
            grant_amount=10000,
            grant_name="First Home Buyer Choice",
            passed_rules=["Income Cap", "Property Price Cap", "First Home Buyer"],
            failed_rules=[],
            warnings=[],
            missing_requirements=[],
            next_steps=["Apply online", "Gather documents"],
            sources=["https://revenue.nsw.gov.au"],
        )

    @pytest.fixture
    def sample_user_profile(self):
        """Create sample user profile."""
        return {
            "state": "NSW",
            "income": 80000,
            "property_price": 700000,
            "first_home_buyer": True,
            "citizenship_status": "citizen",
            "will_reside": True,
            "property_is_new": False,
        }

    def test_generate_markdown_report_contains_key_info(self, sample_report, sample_user_profile, tmp_path):
        """Test markdown report contains required information."""
        config = ReportConfig(output_dir=str(tmp_path) + "/", format="markdown")
        generator = ReportGenerator(config, validate_paths=False)
        output_path = generator.generate_report(sample_user_profile, sample_report)

        assert output_path.endswith(".md")
        assert tmp_path.exists()

        content = Path(output_path).read_text()
        assert "Eligibility Report" in content
        assert "$10,000" in content or "10000" in content
        assert "NSW" in content
        assert "Eligible" in content or "ELIGIBLE" in content
        assert "Apply online" in content

    def test_generate_html_report_creates_html_file(self, sample_report, sample_user_profile, tmp_path):
        """Test HTML report generation."""
        config = ReportConfig(output_dir=str(tmp_path) + "/", format="html")
        generator = ReportGenerator(config, validate_paths=False)
        output_path = generator.generate_report(sample_user_profile, sample_report)

        assert output_path.endswith(".html")
        content = Path(output_path).read_text()
        assert "<!DOCTYPE html>" in content
        assert "Eligibility" in content
        assert "$10,000" in content or "10000" in content

    def test_summary_card_eligible_formatting(self, sample_report, sample_user_profile):
        """Test summary card for eligible user."""
        generator = ReportGenerator()
        card = generator.generate_summary_card(sample_user_profile, sample_report)

        assert "eligible" in card.lower()
        assert "green" in card or "#28a745" in card
        assert "$10,000" in card or "10000" in card

    def test_summary_card_not_eligible_formatting(self, sample_report, sample_user_profile):
        """Test summary card for not eligible user."""
        sample_report.status = EligibilityStatus.NOT_ELIGIBLE
        sample_report.missing_requirements = ["Income exceeds cap"]
        sample_report.grant_amount = 0

        generator = ReportGenerator()
        card = generator.generate_summary_card(sample_user_profile, sample_report)

        assert "not eligible" in card.lower()
        assert "red" in card or "#dc3545" in card

    def test_report_includes_next_steps(self, sample_report, sample_user_profile, tmp_path):
        """Test report includes next steps."""
        config = ReportConfig(output_dir=str(tmp_path) + "/")
        generator = ReportGenerator(config, validate_paths=False)
        output_path = generator.generate_report(sample_user_profile, sample_report)

        content = Path(output_path).read_text()
        assert "Apply online" in content
        assert "Gather documents" in content

    def test_report_includes_sources(self, sample_report, sample_user_profile, tmp_path):
        """Test report includes sources."""
        config = ReportConfig(output_dir=str(tmp_path) + "/")
        generator = ReportGenerator(config, validate_paths=False)
        output_path = generator.generate_report(sample_user_profile, sample_report)

        content = Path(output_path).read_text()
        assert "Sources" in content or "sources" in content
        assert "revenue.nsw.gov.au" in content

    def test_output_directory_created_if_not_exists(self, sample_report, sample_user_profile):
        """Test output directory is created automatically."""
        import shutil

        temp_dir = tempfile.mkdtemp()
        output_dir = Path(temp_dir) / "new_reports"

        try:
            config = ReportConfig(output_dir=str(output_dir) + "/")
            generator = ReportGenerator(config, validate_paths=False)
            generator.generate_report(sample_user_profile, sample_report)

            assert output_dir.exists()
        finally:
            shutil.rmtree(temp_dir)

    def test_unsupported_format_raises_error(self, sample_report, sample_user_profile, tmp_path):
        """Test unsupported format returns empty string."""
        config = ReportConfig(output_dir=str(tmp_path) + "/", format="pdf")
        generator = ReportGenerator(config, validate_paths=False)
        output_path = generator.generate_report(sample_user_profile, sample_report, output_format="pdf")

        assert output_path == ""

    def test_report_generates_unique_filenames(self, sample_report, sample_user_profile, tmp_path):
        """Test each report generates a unique filename."""
        config = ReportConfig(output_dir=str(tmp_path) + "/")
        generator = ReportGenerator(config, validate_paths=False)

        files = []
        for i in range(3):
            path = generator.generate_report(sample_user_profile, sample_report)
            files.append(path)

        assert len(set(files)) == 3  # All filenames are unique

    def test_markdown_includes_disclaimer(self, sample_report, sample_user_profile, tmp_path):
        """Test markdown report includes disclaimer."""
        config = ReportConfig(output_dir=str(tmp_path) + "/")
        generator = ReportGenerator(config, validate_paths=False)
        output_path = generator.generate_report(sample_user_profile, sample_report)

        content = Path(output_path).read_text()
        assert "disclaimer" in content.lower()
        assert "informational purposes" in content.lower()

    def test_not_eligible_report_shows_missing_requirements(self, sample_report, sample_user_profile, tmp_path):
        """Test not eligible report shows missing requirements."""
        sample_report.status = EligibilityStatus.NOT_ELIGIBLE
        sample_report.missing_requirements = ["Income exceeds $150,000 cap"]

        config = ReportConfig(output_dir=str(tmp_path) + "/")
        generator = ReportGenerator(config, validate_paths=False)
        output_path = generator.generate_report(sample_user_profile, sample_report)

        content = Path(output_path).read_text()
        assert "Missing requirements" in content or "missing requirements" in content
        assert "Income exceeds" in content
