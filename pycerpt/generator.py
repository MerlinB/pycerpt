from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch


class Excerpt:
    page_height = defaultPageSize[1]
    page_width = defaultPageSize[0]
    title_spacing = 0.3 * inch
    paragraph_spacing = 0.2 * inch
    font_family = 'Times-Bold'
    font_size = 16

    def __init__(self, title):
        self.style = getSampleStyleSheet()
        self.title = title
        self.story = []
        self.add_space(self.title_spacing)

    def add_space(self, size):
        self.story.append(Spacer(1, size))

    def add_paragraph(self, text):
        new_paragraph = Paragraph(text, self.style['Normal'])
        self.story.append(new_paragraph)
        self.add_space(self.paragraph_spacing)

    def add_paragraphs(self, paragraph_list):
        for paragraph in paragraph_list:
            self.add_paragraph(paragraph)

    def save_pdf(self, output_path):
        doc = SimpleDocTemplate(output_path)
        self.story.insert(0, Paragraph(self.title, self.style['Heading1']))
        doc.build(self.story)
