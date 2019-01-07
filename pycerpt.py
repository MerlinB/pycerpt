import click
import io

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams, LTContainer, LTAnno, LTText, LTTextBox
from pdfminer.converter import TextConverter
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument
import pdfminer.settings


pdfminer.settings.STRICT = False


@click.command()
@click.argument('pdf_input_path')
@click.argument('pdf_output_path')
def pycerpt(pdf_input_path, pdf_output_path):
    loaded_pdf = AnnotatedPDF(pdf_input_path)
    loaded_pdf.gen_excerpt_file(pdf_output_path)
    loaded_pdf.close()


class AnnotatedPDF:
    def __init__(self, file_path):
        self.file = open(file_path, 'rb')
        rsrcmgr = PDFResourceManager()
        self.device = RectExtractor(rsrcmgr, laparams=LAParams())
        self.interpreter = PDFPageInterpreter(rsrcmgr, self.device)
        self.parser = PDFParser(self.file)
        self.doc = PDFDocument(self.parser)

    def get_title(self):
        return self.doc.info[0].get('Title')

    def get_pages(self):
        return PDFPage.create_pages(self.doc)

    def gen_excerpt_file(self, output_path):
        title = self.get_title()
        excerpt = Excerpt(title)
        excerpt.add_paragraphs(self.get_annotation_texts())
        excerpt.save_pdf(output_path)

    def get_annotation_texts(self):
        return [annot.get_substituted_text() for annot in self.get_annotations()]

    def get_annotations(self):
        annots = []
        for (pageno, page_dict) in enumerate(self.get_pages()):
            page = Page(pageno, page_dict, self)
            page.extract_annots()
            annots += page.annots
        return annots

    def close(self):
        self.device.close()
        self.file.close()


class Page:
    def __init__(self, number, obj_dict, annotated_pdf):
        self.obj_dict = obj_dict
        self.number = number
        self.annots = []
        self.document = annotated_pdf

    @property
    def has_annots(self):
        return bool(self.obj_dict.annots)

    def extract_annots(self):
        if self.has_annots:
            self.create_annots()
            self.process_annots()

    def get_resolved_annots(self):
        resolved_annots = []
        for annot in self.obj_dict.annots.resolve():
            resolved_annots.append(annot.resolve())
        return resolved_annots

    def create_annots(self):
        for resolved_annot in self.get_resolved_annots():
            annot = AnnotationWrapper(resolved_annot)
            self.annots.append(annot)

    def process_annots(self):
        self.document.device.set_annots(self.annots)
        self.document.interpreter.process_page(self.obj_dict)


class Box:
    def __init__(self, x0, y0, x1, y1):
        assert x0 <= x1 and y0 <= y1
        self.x0 = x0
        self.y0 = y0
        self.x1 = x1
        self.y1 = y1

    @classmethod
    def from_coords(cls, coords):
        assert len(coords) % 8 == 0
        boxes = []
        while coords != []:
            (x0, y0, x1, y1, x2, y2, x3, y3) = coords[:8]
            xvals = [x0, x1, x2, x3]
            yvals = [y0, y1, y2, y3]
            box = cls(min(xvals), min(yvals), max(xvals), max(yvals))
            boxes.append(box)
            coords = coords[8:]
        return boxes

    def does_include(self, item):
        assert item.x0 <= item.x1 and item.y0 <= item.y1

        x_overlap = max(0, min(item.x1, self.x1) - max(item.x0, self.x0))
        y_overlap = max(0, min(item.y1, self.y1) - max(item.y0, self.y0))
        overlap_area = x_overlap * y_overlap

        item_area = (item.x1 - item.x0) * (item.y1 - item.y0)
        assert overlap_area <= item_area >= 0

        return overlap_area >= 0.5 * item_area


class AnnotationWrapper:
    substitutions = {
        u'ﬀ': 'ff',
        u'ﬁ': 'fi',
        u'ﬂ': 'fl',
        u'’': "'",
    }

    def __init__(self, obj_dict):
        self.obj_dict = obj_dict
        self.boxes = self.get_boxes()
        self.text = ''

    @property
    def subtype(self):
        subtype = self.obj_dict.get('Subtype')
        return subtype.name if subtype else None

    @property
    def coords(self):
        return self.obj_dict.get('QuadPoints')

    def get_boxes(self):
        return Box.from_coords(self.coords)

    def get_content(self):
        contents = self.obj_dict.get('Contents')
        if contents is not None:
            contents = str(contents, 'iso8859-15')
            contents = contents.replace('\r\n', '\n').replace('\r', '\n')
        return contents

    def overlaps(self, item):
        return any([box.does_include(item) for box in self.boxes])

    def add_text(self, text):
        if text == '\n':
            # kludge for latex: elide hyphens, join lines
            if self.text.endswith('-'):
                self.text = self.text[:-1]
            else:
                self.text += ' '
        else:
            self.text += text

    def get_substituted_text(self):
        text = self.text
        if text:
            for search, substitution in self.substitutions.items():
                text = text.replace(search, substitution)
        return text


class RectExtractor(TextConverter):
    def __init__(self, rsrcmgr, codec='utf-8', pageno=1, laparams=None):
        io_dummy = io.StringIO()
        TextConverter.__init__(
            self, rsrcmgr, outfp=io_dummy, codec=codec, pageno=pageno,
            laparams=laparams)
        self.annots = []
        self._matches = []

    def reset_matches(self):
        self._matches = []

    def set_annots(self, annots):
        self.annots = [annot for annot in annots if annot.boxes]
        self._matches = []

    def get_overlapping_annots(self, item):
        matches = []
        for annot in self.annots:
            if annot.overlaps(item):
                matches.append(annot)
        return matches

    def match_new(self, item):
        self._matches = self.get_overlapping_annots(item)

    def add_text(self, text):
        for annot in self._matches:
            annot.add_text(text)

    def receive_layout(self, ltpage):
        def render(item):
            if isinstance(item, LTContainer):
                for child in item:
                    render(child)
            elif isinstance(item, LTAnno):
                self.add_text(item.get_text())
            elif isinstance(item, LTText):
                self.match_new(item)
                self.add_text(item.get_text())
            if isinstance(item, LTTextBox):
                self.match_new(item)
                self.add_text('\n')

        render(ltpage)


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


if __name__ == '__main__':
    pycerpt()
