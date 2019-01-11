from typing import List

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer  # type: ignore
from reportlab.lib.styles import getSampleStyleSheet  # type: ignore
from reportlab.lib.units import inch  # type: ignore


TITLE_SPACING: int = 0.3 * inch
PARAGRAPH_SPACING: int = 0.2 * inch
STYLESHEET = getSampleStyleSheet()
TITLE_STYLE = STYLESHEET['Heading1']
PARAGRAPH_STYLE = STYLESHEET['Normal']


class Story(list):
    def __init__(self, paragraphs: List[str] = None) -> None:
        if paragraphs:
            self.add_paragraphs(paragraphs)

    def add_title(self, title: str) -> None:
        self.insert(0, Paragraph(title, TITLE_STYLE))
        self.insert(1, Spacer(1, TITLE_SPACING))

    def add_paragraph(self, text: str) -> None:
        self.append(Paragraph(text, PARAGRAPH_STYLE))
        self.append(Spacer(1, PARAGRAPH_SPACING))

    def add_paragraphs(self, paragraphs: List[str]) -> None:
        for paragraph in paragraphs:
            self.add_paragraph(paragraph)

    def save(self, path: str) -> None:
        doc = SimpleDocTemplate(path)
        doc.build(self)
