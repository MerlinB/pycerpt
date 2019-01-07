from setuptools import setup, find_packages

setup(
    name='pycerpt',
    version='0.1.1',
    author='Merlin Buczek',
    author_email='merlin.buczek@gmail.com',
    description='A cli utility for generating excerpts from highlighted PDFs',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url='https://github.com/MerlinB/pycerpt',
    packages=find_packages(),
    install_requires=[
        'Click',
        'reportlab',
        'pdfminer.six',
        'chardet'  # https://github.com/pdfminer/pdfminer.six/issues/213
    ],
    entry_points='''
        [console_scripts]
        pycerpt=pycerpt.cli:cli
    ''',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication",
        "Operating System :: OS Independent",
    ],
)
