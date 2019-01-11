import logging
from typing import Dict, Iterable, List


logger = logging.getLogger(__name__)


pdf_export_available: bool
try:
    from .pdfgen import Story
except ImportError:
    logger.debug("PDF functionality dependencies not met.")
    pdf_export_available = False
else:
    pdf_export_available = True


FILE_EXTENSIONS: Dict[str, List[str]] = {
    'markdown': [
        'markdown',
        'mdown',
        'mkdn',
        'md',
        'mkd',
        'mdwn',
        'mdtxt',
        'mdtext',
        'text',
        'Rmd',
        'txt'
    ]
}


class Excerpt:
    def __init__(self, title: str, paragraphs: Iterable[str]) -> None:
        self.title: str = title
        self.paragraphs: List[str] = list(paragraphs)

    def get_markdown(self) -> str:
        text: str = f'# {self.title}\n\n'
        for paragraph in self.paragraphs:
            text += f'{paragraph}\n\n'
        return text

    def save(self, path: str) -> None:
        extension: str = path.split('.')[-1].lower()
        if extension in FILE_EXTENSIONS['markdown']:
            self.save_text(path)
        elif extension == 'pdf':
            self.save_pdf(path)
        else:
            raise NotImplementedError(f'Export to {extension} not supported.')

    def save_text(self, path: str) -> None:
        with open(path, 'w') as file:
            file.write(self.get_markdown())

    def save_pdf(self, path: str) -> None:
        if not pdf_export_available:
            raise ImportError(
                "Missing dependencies. "
                "Install [pdf] extras for PDF generation functionality.")
        story = Story(paragraphs=self.paragraphs)
        story.add_title(self.title)
        story.save(path)
