import click

from .extractor import AnnotatedPDF


@click.command()
@click.argument('pdf_input_path')
@click.argument('pdf_output_path')
def cli(pdf_input_path, pdf_output_path):
    loaded_pdf = AnnotatedPDF(pdf_input_path)
    loaded_pdf.gen_excerpt_file(pdf_output_path)
    loaded_pdf.close()
