import click

from .extractor import AnnotatedPDF
from .excerpt import Excerpt


@click.command()
@click.argument('input_file', type=click.File('rb'))
@click.argument('output_file', type=click.Path(), required=False)
def cli(input_file, output_file):
    loaded_pdf = AnnotatedPDF(input_file)
    excerpt = Excerpt(
        title=loaded_pdf.get_title(),
        paragraphs=loaded_pdf.get_annot_texts())

    if output_file:
        excerpt.save(output_file)
    else:
        click.echo_via_pager(excerpt.get_markdown())

    loaded_pdf.close()
