from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch


class Excerpt:
    page_height = defaultPageSize[1]
    page_width = defaultPageSize[0]
    title_spacing = 2
    paragraph_spacing = 0.2
    font_family = 'Times-Bold'
    font_size = 16

    def __init__(self, title):
        self.style = self.get_styles()
        self.title = title
        self.story = []
        self.add_space(self.title_spacing)

    def get_styles(self):
        styles = getSampleStyleSheet()
        return styles["Normal"]

    def add_space(self, size):
        self.story.append(Spacer(1, size * inch))

    def add_paragraph(self, text):
        new_paragraph = Paragraph(text, self.style)
        self.story.append(new_paragraph)
        self.add_space(self.paragraph_spacing)

    def add_paragraphs(self, paragraph_list):
        for paragraph in paragraph_list:
            self.add_paragraph(paragraph)

    def add_title(self, canvas, doc):
        canvas.saveState()
        canvas.setFont(self.font_family, self.font_size)
        x_position = self.page_width / 2
        y_position = self.page_height - 108
        canvas.drawCentredString(x_position, y_position, self.title)
        canvas.restoreState()

    def save_pdf(self, output_path):
        doc = SimpleDocTemplate(output_path)
        doc.build(self.story, onFirstPage=self.add_title)
