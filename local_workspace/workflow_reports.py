"""Local PDF export of reviewed workflow text; no network or tool execution."""
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape


def pdf_report(text: str, scope: str) -> bytes:
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    font = 'Helvetica'
    font_path = Path('/System/Library/Fonts/Supplemental/Arial.ttf')
    if font_path.is_file():
        if 'DAKSHArial' not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont('DAKSHArial', str(font_path)))
        font = 'DAKSHArial'
    styles = getSampleStyleSheet()
    for style in styles.byName.values():
        style.fontName = font
    styles['BodyText'].leading = 15
    out = BytesIO()
    document = SimpleDocTemplate(out, title='DAKSH local workflow report', author='DAKSH', rightMargin=42, leftMargin=42)
    story = [Paragraph('DAKSH — Local workflow report', styles['Title']), Paragraph(escape(scope), styles['BodyText']), Spacer(1, 14)]
    for line in text.splitlines():
        if not line.strip():
            story.append(Spacer(1, 6))
            continue
        heading = line.startswith('#')
        content = line.lstrip('# ').strip() if heading else line
        story.append(Paragraph(escape(content), styles['Heading2'] if heading else styles['BodyText']))
    document.build(story)
    return out.getvalue()
