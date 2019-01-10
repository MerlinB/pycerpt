from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch


page_height = defaultPageSize[1]
page_width = defaultPageSize[0]
title_spacing = 0.3 * inch
paragraph_spacing = 0.2 * inch
font_family = 'Times-Bold'
font_size = 16
stylesheet = getSampleStyleSheet()
title_style = stylesheet['Heading1']
paragraph_style = stylesheet['Normal']


class Story(list):
    def __init__(self, *args, paragraphs=[], **kwargs):
        super().__init__(*args, *kwargs)
        self.add_paragraphs(paragraphs)

    def add_title(self, title):
        self.insert(0, Paragraph(title, title_style))
        self.insert(1, Spacer(1, title_spacing))

    def add_paragraph(self, text):
        self.append(Paragraph(text, paragraph_style))
        self.append(Spacer(1, paragraph_spacing))

    def add_paragraphs(self, paragraphs):
        for paragraph in paragraphs:
            self.add_paragraph(paragraph)

    def save(self, path):
        doc = SimpleDocTemplate(path)
        doc.build(self)
