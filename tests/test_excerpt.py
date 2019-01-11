import pytest

from pycerpt.excerpt import Excerpt


class TestExceptions:
    @pytest.fixture
    def excerpt(self):
        return Excerpt(
            title='testtitle',
            paragraphs=['testparagraph1', 'testparagraph2'])

    def test_pdf_exception(self, excerpt, tmpdir):
        with pytest.raises(ImportError):
            excerpt.save(f'{tmpdir}/test.pdf')

    def test_unknown_format(self, excerpt, tmpdir):
        with pytest.raises(NotImplementedError):
            excerpt.save(f'{tmpdir}/test.unknown')
