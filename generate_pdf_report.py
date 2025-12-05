# generate_pdf_report.py
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from io import BytesIO

def generate_pdf_report(df, long_df):
    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer, pagesize=LETTER)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("Measles & Rubella Data Summary Report", styles["Title"]))
    story.append(Spacer(1, 12))

    # Summary metrics
    story.append(Paragraph("<b>Summary Statistics (Wide Data)</b>", styles["Heading2"]))
    summary = df.describe(include="all").reset_index()
    summary_table = Table([summary.columns.tolist()] + summary.values.tolist())
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("FONTSIZE", (0,0), (-1,-1), 8),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 12))

    # Long dataset preview
    story.append(Paragraph("<b>Long Format (First 20 Rows)</b>", styles["Heading2"]))
    preview = long_df.head(20)
    table2 = Table([preview.columns.tolist()] + preview.values.tolist())
    table2.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("FONTSIZE", (0,0), (-1,-1), 7),
    ]))
    story.append(table2)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
