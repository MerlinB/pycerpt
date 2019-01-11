import io
import re

import chardet  # type: ignore

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter  # type: ignore
from pdfminer.pdfpage import PDFPage  # type: ignore
from pdfminer.layout import LAParams, LTContainer, LTAnno, LTText, LTTextBox  # type: ignore
from pdfminer.converter import TextConverter  # type: ignore
from pdfminer.pdfparser import PDFParser  # type: ignore
from pdfminer.pdfdocument import PDFDocument  # type: ignore
from pdfminer.pdftypes import PDFObjRef  # type: ignore
import pdfminer.settings  # type: ignore


pdfminer.settings.STRICT = False


class AnnotatedPDF:
    def __init__(self, file):
        self.file = file
        rsrcmgr = PDFResourceManager()
        self.device = RectExtractor(rsrcmgr, laparams=LAParams())
        self.interpreter = PDFPageInterpreter(rsrcmgr, self.device)
        self.parser = PDFParser(self.file)
        self.doc = PDFDocument(self.parser)

    def get_title(self):
        title = self.doc.info[0].get('Title')
        if isinstance(title, str):
            return title
        elif isinstance(title, bytes):
            encoding = chardet.detect(title)
            return title.decode(encoding['encoding'])
        else:
            raise TypeError("Unknown type of title.")

    def get_pages(self):
        return PDFPage.create_pages(self.doc)

    def get_annot_texts(self):
        return (annot.get_paragraph() for annot in self.get_annots()
                if not annot.is_empty)

    def get_annots(self):
        for (pageno, page_dict) in enumerate(self.get_pages(), 1):
            page = Page(pageno, page_dict, self)
            page.extract_annots()
            for annot in page.annots:
                yield annot

    def close(self):
        self.device.close()


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
        for annot in self.obj_dict.annots.resolve():
            yield annot.resolve()

    def create_annots(self):
        for resolved_annot in self.get_resolved_annots():
            annot = AnnotationWrapper(resolved_annot, self.number)
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
        while coords:
            (x0, y0, x1, y1, x2, y2, x3, y3) = coords[:8]
            xvals = [x0, x1, x2, x3]
            yvals = [y0, y1, y2, y3]
            box = cls(min(xvals), min(yvals), max(xvals), max(yvals))
            yield box
            coords = coords[8:]

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

    def __init__(self, obj_dict, pageno):
        self.obj_dict = obj_dict
        self.boxes = self.get_boxes()
        self.text = ''
        self.pageno = pageno

    @property
    def is_empty(self):
        return not bool(self.text)

    @property
    def endswith_wordbreak(self):
        re_pattern = re.compile(r'\w-$')
        return bool(re_pattern.search(self.text))

    @property
    def subtype(self):
        subtype = self.obj_dict.get('Subtype')
        return subtype.name if subtype else None

    @property
    def coords(self):
        coords = self.obj_dict.get('QuadPoints', [])
        if isinstance(coords, list):
            return coords
        elif isinstance(coords, PDFObjRef):
            return coords.resolve()
        else:
            raise TypeError("Unknown type of annotation coordinates.")

    def get_boxes(self):
        return list(Box.from_coords(self.coords))

    def get_content(self):
        contents = self.obj_dict.get('Contents')
        if contents is not None:
            contents = str(contents, 'iso8859-15')
            contents = contents.replace('\r\n', '\n').replace('\r', '\n')
        return contents

    def overlaps(self, item):
        return any([box.does_include(item) for box in self.boxes])

    def add_char(self, char):
        if char == '\n':
            self.handle_line_break()
        else:
            self.text += char

    def handle_line_break(self):
        if self.endswith_wordbreak:
            self.text = self.text[:-1]
        elif not self.text.endswith(' '):
            self.text += ' '

    def get_substituted_text(self):
        text = self.text
        if text:
            for search, substitution in self.substitutions.items():
                text = text.replace(search, substitution)
        return text

    def get_paragraph(self):
        text = self.get_substituted_text()
        text += f' ({self.pageno})'
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

    def get_overlapping_annots(self, char):
        for annot in self.annots:
            if annot.overlaps(char):
                yield annot

    def match_new_character(self, char):
        self._matches = list(self.get_overlapping_annots(char))

    def add_char(self, char):
        for annot in self._matches:
            annot.add_char(char)

    def handle_new_box(self):
        for annot in self._matches:
            annot.handle_line_break()

    def receive_layout(self, ltpage):
        def render(item):
            if isinstance(item, LTContainer):
                for child in item:
                    render(child)
            elif isinstance(item, LTAnno):
                self.add_char(item.get_text())
            elif isinstance(item, LTText):
                self.match_new_character(item)
                self.add_char(item.get_text())
            elif isinstance(item, LTTextBox):
                self.match_new_character(item)
                self.handle_new_box()

        render(ltpage)
