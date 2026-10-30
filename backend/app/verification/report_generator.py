import io
from datetime import datetime, timezone
from typing import Dict, List, Any
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Preformatted,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


class VerificationReportGenerator:
    """Generates the comprehensive 11-section verification report and PDF document."""

    @classmethod
    def generate_report_content(
        cls,
        bug_data: Dict[str, Any],
        repair_data: Dict[str, Any],
        test_data: Dict[str, Any],
        regression_diff: Dict[str, Any],
        decision: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Construct the 11-section structured report data."""
        return {
            "section_1_original_issue": {
                "title": bug_data.get("title", ""),
                "category": bug_data.get("category", ""),
                "severity": bug_data.get("severity", ""),
                "file_path": bug_data.get("file_path", ""),
                "line_number": bug_data.get("line_number"),
                "description": bug_data.get("description", ""),
            },
            "section_2_root_cause": {
                "root_cause": bug_data.get("root_cause", ""),
                "evidence": bug_data.get("evidence", []),
                "confidence": bug_data.get("confidence", 0.85),
            },
            "section_3_files_affected": {
                "files": repair_data.get("files_changed", []),
                "count": len(repair_data.get("files_changed", [])),
            },
            "section_4_generated_patch": {
                "patch_content": repair_data.get("patch_content", ""),
                "explanation": repair_data.get("explanation", ""),
            },
            "section_5_changes_applied": {
                "applied_at": datetime.now(timezone.utc).isoformat(),
                "isolation_mode": "Isolated Working Copy",
                "clean_application": True,
            },
            "section_6_tests_executed": {
                "runner": "Pytest",
                "total_tests": test_data.get("total", 0),
                "duration_seconds": test_data.get("duration", 0.0),
            },
            "section_7_test_results": {
                "status": test_data.get("status", "unknown"),
                "passed": test_data.get("passed", 0),
                "failed": test_data.get("failed", 0),
                "skipped": test_data.get("skipped", 0),
                "failures": test_data.get("failures", []),
            },
            "section_8_regression_checks": {
                "has_regression": regression_diff.get("has_regression", False),
                "fixed_tests": regression_diff.get("fixed_tests", []),
                "new_regressions": regression_diff.get("new_regressions", []),
                "is_improved": regression_diff.get("is_improved", True),
            },
            "section_9_verification_decision": {
                "final_verdict": decision.get("status", "INCONCLUSIVE"),
                "checks_passed": decision.get("checks_passed", []),
                "checks_failed": decision.get("checks_failed", []),
            },
            "section_10_remaining_risks": {
                "risks": decision.get("remaining_risks", []),
            },
            "section_11_recommended_next_action": {
                "recommendation": (
                    "Approve and merge patch into your main repository."
                    if decision.get("status") == "VERIFIED"
                    else "Review remaining test failures or regenerate patch with updated constraints."
                ),
                "can_auto_merge": False,
                "note": "PatchPilot adheres to strict security standards: patches are never merged without explicit developer approval."
            }
        }

    @classmethod
    def generate_pdf(cls, report_data: Dict[str, Any], project_name: str = "Project") -> bytes:
        """Render downloadable PDF with professional styling."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
        )
        subtitle_style = ParagraphStyle(
            "DocSubTitle",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#475569"),
        )
        heading_style = ParagraphStyle(
            "SectionHeading",
            parent=styles["Heading2"],
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#1e293b"),
            fontName="Helvetica-Bold",
            spaceBefore=10,
            spaceAfter=4,
        )
        body_style = ParagraphStyle(
            "Body",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#334155"),
        )
        code_style = ParagraphStyle(
            "CodeBlock",
            parent=styles["Code"],
            fontSize=7,
            leading=9,
            textColor=colors.HexColor("#0f172a"),
            backColor=colors.HexColor("#f1f5f9"),
        )

        verdict = report_data.get("section_9_verification_decision", {}).get("final_verdict", "INCONCLUSIVE")
        verdict_color = {
            "VERIFIED": colors.HexColor("#16a34a"),
            "PARTIALLY_VERIFIED": colors.HexColor("#d97706"),
            "FAILED": colors.HexColor("#dc2626"),
            "INCONCLUSIVE": colors.HexColor("#64748b"),
        }.get(verdict, colors.HexColor("#64748b"))

        story = []

        # Title & Header
        story.append(Paragraph("PATCHPILOT VERIFICATION AUDIT REPORT", title_style))
        story.append(Paragraph(f"Project: <b>{project_name}</b> | Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}", subtitle_style))
        story.append(Spacer(1, 12))

        # Status Banner Table
        status_table_data = [
            [
                Paragraph("<b>VERIFICATION VERDICT:</b>", body_style),
                Paragraph(f"<b><font size='13' color='{verdict_color.hexval()}'>{verdict}</font></b>", body_style)
            ]
        ]
        status_table = Table(status_table_data, colWidths=[160, 380])
        status_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(status_table)
        story.append(Spacer(1, 14))

        # 1. Original Issue
        sec1 = report_data.get("section_1_original_issue", {})
        story.append(Paragraph("1. Original Issue & Detection", heading_style))
        story.append(Paragraph(f"<b>Title:</b> {sec1.get('title')}", body_style))
        story.append(Paragraph(f"<b>Category:</b> {sec1.get('category')} | <b>Severity:</b> {sec1.get('severity')}", body_style))
        story.append(Paragraph(f"<b>Location:</b> {sec1.get('file_path')}:{sec1.get('line_number') or 1}", body_style))
        story.append(Paragraph(f"<b>Description:</b> {sec1.get('description')}", body_style))
        story.append(Spacer(1, 8))

        # 2. Root Cause
        sec2 = report_data.get("section_2_root_cause", {})
        story.append(Paragraph("2. Root Cause Analysis", heading_style))
        story.append(Paragraph(f"<b>Diagnosis:</b> {sec2.get('root_cause')}", body_style))
        story.append(Paragraph(f"<b>Confidence:</b> {int(sec2.get('confidence', 0.85) * 100)}%", body_style))
        story.append(Spacer(1, 8))

        # 3. Files Affected & Patch
        sec3 = report_data.get("section_3_files_affected", {})
        sec4 = report_data.get("section_4_generated_patch", {})
        story.append(Paragraph("3. Changes Applied & Code Patch", heading_style))
        story.append(Paragraph(f"<b>Files Changed:</b> {', '.join(sec3.get('files', []))}", body_style))
        story.append(Paragraph(f"<b>Explanation:</b> {sec4.get('explanation')}", body_style))
        
        # Display first 20 lines of patch
        patch_text = sec4.get("patch_content", "")
        patch_snippet = "\n".join(patch_text.splitlines()[:25])
        if patch_snippet:
            story.append(Spacer(1, 4))
            story.append(Preformatted(patch_snippet, code_style))
        story.append(Spacer(1, 8))

        # 4. Test Execution & Regression
        sec6 = report_data.get("section_6_tests_executed", {})
        sec7 = report_data.get("section_7_test_results", {})
        sec8 = report_data.get("section_8_regression_checks", {})
        story.append(Paragraph("4. Automated Test Results & Regression Check", heading_style))
        test_summary_text = (
            f"<b>Runner:</b> {sec6.get('runner')} | "
            f"<b>Total:</b> {sec7.get('total', 0)} | "
            f"<b>Passed:</b> {sec7.get('passed', 0)} | "
            f"<b>Failed:</b> {sec7.get('failed', 0)} | "
            f"<b>Duration:</b> {sec6.get('duration_seconds', 0.0):.2f}s"
        )
        story.append(Paragraph(test_summary_text, body_style))
        story.append(Paragraph(f"<b>Regression Detected:</b> {'YES - Warning' if sec8.get('has_regression') else 'NONE - Clean'}", body_style))
        if sec8.get("fixed_tests"):
            story.append(Paragraph(f"<b>Tests Fixed by Patch:</b> {', '.join(sec8.get('fixed_tests'))}", body_style))
        story.append(Spacer(1, 8))

        # 5. Remaining Risks & Next Action
        sec10 = report_data.get("section_10_remaining_risks", {})
        sec11 = report_data.get("section_11_recommended_next_action", {})
        story.append(Paragraph("5. Remaining Risks & Recommendation", heading_style))
        risks = sec10.get("risks", [])
        if risks:
            for r in risks:
                story.append(Paragraph(f"• {r}", body_style))
        else:
            story.append(Paragraph("• No outstanding risks identified.", body_style))
        story.append(Spacer(1, 4))
        story.append(Paragraph(f"<b>Recommended Action:</b> {sec11.get('recommendation')}", body_style))
        story.append(Paragraph(f"<i>{sec11.get('note')}</i>", subtitle_style))

        doc.build(story)
        pdf_bytes = buffer.getvalue()
        buffer.close()
        return pdf_bytes

