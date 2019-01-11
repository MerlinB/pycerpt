from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch


TITLE_SPACING = 0.3 * inch
PARAGRAPH_SPACING = 0.2 * inch
STYLESHEET = getSampleStyleSheet()
TITLE_STYLE = STYLESHEET['Heading1']
PARAGRAPH_STYLE = STYLESHEET['Normal']


class Story(list):
    def __init__(self, *args, paragraphs=[], **kwargs):
        super().__init__(*args, *kwargs)
        self.add_paragraphs(paragraphs)

    def add_title(self, title):
        self.insert(0, Paragraph(title, TITLE_STYLE))
        self.insert(1, Spacer(1, TITLE_SPACING))

    def add_paragraph(self, text):
        self.append(Paragraph(text, PARAGRAPH_STYLE))
        self.append(Spacer(1, PARAGRAPH_SPACING))

    def add_paragraphs(self, paragraphs):
        for paragraph in paragraphs:
            self.add_paragraph(paragraph)

    def save(self, path):
        doc = SimpleDocTemplate(path)
        doc.build(self)
