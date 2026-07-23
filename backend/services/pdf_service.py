"""
PDF generation service using WeasyPrint.
Converts Markdown → HTML → PDF with a professional consulting style.
"""
from __future__ import annotations

import logging
import os
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# Output directory for generated PDFs
PDF_OUTPUT_DIR = Path("generated_pdfs")
PDF_OUTPUT_DIR.mkdir(exist_ok=True)


# ─── Professional CSS ─────────────────────────────────────────────────────────

REPORT_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@700&display=swap');

* { margin: 0; padding: 0; box-sizing: border-box; }

@page {
    size: A4;
    margin: 2cm 2.5cm 2.5cm 2.5cm;
    @top-right {
        content: "Lead Intelligence Report";
        font-family: Inter, sans-serif;
        font-size: 8pt;
        color: #94a3b8;
    }
    @bottom-center {
        content: "Page " counter(page) " of " counter(pages);
        font-family: Inter, sans-serif;
        font-size: 8pt;
        color: #94a3b8;
    }
}

body {
    font-family: Inter, -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 10.5pt;
    line-height: 1.7;
    color: #1e293b;
    background: #ffffff;
}

/* Cover page */
.cover-page {
    page-break-after: always;
    min-height: 25cm;
    display: flex;
    flex-direction: column;
    justify-content: center;
    background: linear-gradient(135deg, #0f172a 0%, #1e3a5f 100%);
    padding: 3cm;
    border-radius: 0;
}

.cover-logo {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 14pt;
    color: #38bdf8;
    letter-spacing: 4px;
    text-transform: uppercase;
    margin-bottom: 3cm;
}

.cover-title {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 36pt;
    color: #f8fafc;
    line-height: 1.2;
    margin-bottom: 0.5cm;
}

.cover-subtitle {
    font-size: 14pt;
    color: #94a3b8;
    margin-bottom: 2cm;
}

.cover-meta {
    font-size: 10pt;
    color: #64748b;
    border-top: 1px solid #334155;
    padding-top: 0.5cm;
}

.cover-meta span {
    display: block;
    margin-bottom: 4px;
}

/* Headings */
h1 {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 22pt;
    color: #0f172a;
    margin: 1cm 0 0.4cm 0;
    padding-bottom: 0.3cm;
    border-bottom: 3px solid #0ea5e9;
    page-break-after: avoid;
}

h2 {
    font-size: 14pt;
    font-weight: 600;
    color: #1e40af;
    margin: 0.8cm 0 0.3cm 0;
    page-break-after: avoid;
}

h3 {
    font-size: 11pt;
    font-weight: 600;
    color: #334155;
    margin: 0.5cm 0 0.2cm 0;
    page-break-after: avoid;
}

/* Paragraphs */
p {
    margin-bottom: 0.4cm;
}

/* Lists */
ul, ol {
    margin: 0.3cm 0 0.3cm 0.6cm;
}

li {
    margin-bottom: 0.15cm;
}

/* Callout boxes */
.callout {
    border-left: 4px solid #0ea5e9;
    background: #f0f9ff;
    padding: 0.4cm 0.6cm;
    margin: 0.5cm 0;
    border-radius: 0 4px 4px 0;
}

.callout.warning {
    border-left-color: #f59e0b;
    background: #fffbeb;
}

.callout.success {
    border-left-color: #10b981;
    background: #f0fdf4;
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 0.5cm 0;
    font-size: 9.5pt;
}

th {
    background: #1e3a5f;
    color: #f8fafc;
    padding: 0.25cm 0.4cm;
    text-align: left;
    font-weight: 600;
}

td {
    padding: 0.2cm 0.4cm;
    border-bottom: 1px solid #e2e8f0;
}

tr:nth-child(even) td {
    background: #f8fafc;
}

/* Score badge */
.score-badge {
    display: inline-block;
    background: #0ea5e9;
    color: white;
    padding: 2px 12px;
    border-radius: 20px;
    font-size: 9pt;
    font-weight: 600;
}

/* Section break */
.section-break {
    page-break-before: always;
}

/* Footer note */
.footer-note {
    font-size: 8pt;
    color: #94a3b8;
    text-align: center;
    margin-top: 1cm;
    border-top: 1px solid #e2e8f0;
    padding-top: 0.3cm;
}

code {
    font-family: 'Courier New', monospace;
    font-size: 9pt;
    background: #f1f5f9;
    padding: 1px 5px;
    border-radius: 3px;
}

blockquote {
    border-left: 3px solid #0ea5e9;
    padding-left: 0.5cm;
    color: #475569;
    font-style: italic;
    margin: 0.4cm 0;
}

strong { font-weight: 600; color: #0f172a; }
em { font-style: italic; }

hr {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 0.6cm 0;
}
"""


def _markdown_to_html(markdown_text: str, company_name: str, lead_name: str) -> str:
    """Convert markdown report to complete HTML document."""
    import markdown as md  # type: ignore

    body_html = md.markdown(
        markdown_text,
        extensions=["extra", "tables", "toc", "fenced_code"],
    )

    cover_html = f"""
    <div class="cover-page">
        <div class="cover-logo">Lead Intelligence</div>
        <div class="cover-title">Business Audit Report</div>
        <div class="cover-subtitle">{company_name}</div>
        <div class="cover-meta">
            <span>Prepared for: {lead_name}</span>
            <span>Generated: {datetime.now().strftime('%B %d, %Y')}</span>
            <span>Confidential — For Recipient Use Only</span>
        </div>
    </div>
    """

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Business Audit Report — {company_name}</title>
    <style>{REPORT_CSS}</style>
</head>
<body>
    {cover_html}
    <div class="report-body">
        {body_html}
    </div>
    <div class="footer-note">
        This report was generated by Lead Intelligence AI. All information is based on publicly available data
        and AI analysis. © {datetime.now().year} Lead Intelligence.
    </div>
</body>
</html>"""


async def generate_pdf(
    markdown_content: str,
    company_name: str,
    lead_name: str,
    workflow_id: str,
) -> str:
    """Convert markdown report to a professional PDF."""
    import asyncio
    import functools

    html_content = _markdown_to_html(markdown_content, company_name, lead_name)

    safe_company = "".join(c if c.isalnum() or c in "-_" else "_" for c in company_name)
    filename = f"report_{safe_company}_{workflow_id[:8]}.pdf"
    output_path = str(PDF_OUTPUT_DIR / filename)
    PDF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        from weasyprint import HTML  # type: ignore

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            functools.partial(
                HTML(string=html_content, base_url=".").write_pdf,
                output_path,
            ),
        )
    except Exception as exc:
        logger.warning("WeasyPrint failed, using reportlab fallback: %s", exc)
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
        from reportlab.lib.units import inch
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
        from reportlab.lib import colors

        doc = SimpleDocTemplate(output_path, pagesize=A4, rightMargin=0.75 * inch, leftMargin=0.75 * inch, topMargin=0.75 * inch, bottomMargin=0.75 * inch)
        styles = getSampleStyleSheet()
        body = []
        body.append(Paragraph(f"Business Audit Report — {company_name}", styles["Title"]))
        body.append(Paragraph(f"Prepared for {lead_name}", styles["Heading2"]))
        body.append(Spacer(1, 0.25 * inch))
        for line in markdown_content.splitlines():
            if line.startswith("# "):
                body.append(Paragraph(line[2:], styles["Heading1"]))
            elif line.startswith("## "):
                body.append(Paragraph(line[3:], styles["Heading2"]))
            elif line.startswith("- "):
                body.append(Paragraph(line[2:], styles["BodyText"]))
            else:
                body.append(Paragraph(line or " ", styles["BodyText"]))
            body.append(Spacer(1, 0.1 * inch))
        doc.build(body)

    logger.info("PDF generated at %s", output_path)
    return output_path
