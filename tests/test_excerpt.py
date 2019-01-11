import os
import pytest

from pycerpt.excerpt import Excerpt


@pytest.fixture()
def excerpt():
    return Excerpt(
        title='testtitle',
        paragraphs=['testparagraph1', 'testparagraph2'])


class TestExcerpt:
    def test_unknown_format(self, excerpt, tmpdir):
        with pytest.raises(NotImplementedError):
            excerpt.save(f'{tmpdir}/test.unknown')

    def test_md_generation(self, excerpt, tmpdir):
        file_path = f'{tmpdir}/test.md'
        excerpt.save(file_path)
        assert os.path.isfile(file_path)

    def test_text_output(self, excerpt):
        assert excerpt.get_markdown().startswith("# testtitle\n\ntestparagraph1")


class TestPDFGen:
    pytestmark = pytest.mark.pdfgen

    def test_pdf_generation(self, excerpt, tmpdir):
        file_path = f'{tmpdir}/test.pdf'
        excerpt.save(file_path)
        assert os.path.isfile(file_path)