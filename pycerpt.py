import click
import sys
import io
import textwrap

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.rl_config import defaultPageSize
from reportlab.lib.units import inch

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.layout import LAParams, LTContainer, LTAnno, LTText, LTTextBox
from pdfminer.converter import TextConverter
from pdfminer.pdfparser import PDFParser
from pdfminer.pdfdocument import PDFDocument, PDFNoOutlines
from pdfminer.psparser import PSLiteralTable, PSLiteral
import pdfminer.pdftypes as pdftypes
import pdfminer.settings


pdfminer.settings.STRICT = False


@click.command()
@click.argument('pdf_input_path')
@click.argument('pdf_output_path')
def pycerpt(pdf_input_path, pdf_output_path):
    AnnotatedPDF(pdf_input_path).gen_excerpt_file(pdf_output_path)


class AnnotatedPDF:
    def __init__(self, file_path):
        self.file = open(file_path, 'rb')
        rsrcmgr = PDFResourceManager()
        self.device = RectExtractor(rsrcmgr, laparams=LAParams())
        self.interpreter = PDFPageInterpreter(rsrcmgr, self.device)
        self.parser = PDFParser(self.file)
        self.doc = PDFDocument(self.parser)

    def get_title(self):
        return 'hello world'

    def gen_excerpt_file(self, output_path):
        title = self.get_title()
        excerpt = Excerpt(title)

        for annot in self.get_annotations():
            excerpt.add_paragraph(annot.gettext())

        excerpt.save_pdf(output_path)

    def get_annotations(self):
        for (pageno, page_dict) in enumerate(PDFPage.create_pages(self.doc)):
            page = Page(pageno, pdf_object=page_dict)
            return page.get_annots()

    def close(self):
        self.device.close()
        self.file.close()


class Page:
    def __init__(self, number, pdf_object):
        self.pdf_object = pdf_object
        self.number = number
        self.annots = []

    @property
    def has_annots(self):
        return bool(self.pdf_object.annots)

    def get_annots(self):
        if self.has_annots:
            self.create_annotations()
            self.set_coords()
            self.process()
            return self.annots

    def get_resolved_annots(self):
        resolved_annots = []
        for annot in self.pdf_object.annots:
            resolved_annots.append(annot.resolve)
        return resolved_annots

    def set_coords(self):
        self.pdf_object.document.device.setcoords(self.extracted_annots)

    def process(self):
        self.pdf_object.document.interpreter.process_page(self.pdf_object)

    def create_annots(self):
        annots = []
        for resolved_annot in self.get_resolved_annots():
            annot = AnnotationWrapper.from_resolved_annot(resolved_annot)

            contents = annot.get('Contents')
            if contents is not None:
                contents = str(contents, 'iso8859-15')
                contents = contents.replace('\r\n', '\n').replace('\r', '\n')
            annots.append(annot)

        return annots


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

    def __init__(self, pdf_object):
        self.pdf_object = pdf_object
        self.boxes = self.get_boxes()

    @property
    def subtype(self):
        subtype = self.pdf_object.get('Subtype')
        return subtype.name if subtype else None

    @property
    def coords(self):
        return self.pdf_object.get('QuadPoints')

    def get_boxes(self):
        return Box.from_coords(self.coords)

    def get_content(self):
        contents = self.pdf_object.get('Contents')
        if contents is not None:
            contents = str(contents, 'iso8859-15')
            contents = contents.replace('\r\n', '\n').replace('\r', '\n')
        return contents

    def capture(self, text):
        if text == '\n':
            # kludge for latex: elide hyphens, join lines
            if self.text.endswith('-'):
                self.text = self.text[:-1]
            else:
                self.text += ' '
        else:
            self.text += text

    def get_text(self):
        if self.text:
            # replace tex ligatures (and other common odd characters)
            return ''.join([self.substitutions.get(c, c) for c in self.text.strip()])


class RectExtractor(TextConverter):
    def __init__(self, rsrcmgr, codec='utf-8', pageno=1, laparams=None):
        io_dummy = io.StringIO()
        TextConverter.__init__(self, rsrcmgr, outfp=io_dummy, codec=codec, pageno=pageno, laparams=laparams)
        self.annots = []
        self._lasthit = []

    def set_annots(self, annots):
        self.annots = [a for a in annots if a.boxes]
        self._lasthit = []

    def testboxes(self, item):
        self._lasthit = []
        for annot in self.annots:
            if any([box.does_include(item) for box in annot.boxes]):
                self._lasthit.append(annot)
        return self._lasthit

    def receive_layout(self, ltpage):
        def render(item):
            if isinstance(item, LTContainer):
                for child in item:
                    render(child)
            elif isinstance(item, LTAnno):
                # this catches whitespace
                for a in self._lasthit:
                    a.capture(item.get_text())
            elif isinstance(item, LTText):
                for a in self.testboxes(item):
                    a.capture(item.get_text())
            if isinstance(item, LTTextBox):
                for a in self.testboxes(item):
                    a.capture('\n')

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
