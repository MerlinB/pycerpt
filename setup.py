from setuptools import setup, find_packages

setup(
    name='pycerpt',
    version='0.2.0',
    author='Merlin Buczek',
    author_email='merlin.buczek@gmail.com',
    description='A cli utility for generating excerpts from highlighted PDFs',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url='https://github.com/MerlinB/pycerpt',
    packages=find_packages(),
    install_requires=[
        'Click',
        'pdfminer.six',
        'chardet'  # https://github.com/pdfminer/pdfminer.six/issues/213
    ],
    extras_require={
        'pdf': ['reportlab'],
        'testing': ['tox']
    },
    entry_points={
        'console_scripts': [
            'excerpt = pycerpt.cli:cli',
        ]
    },
    classifiers=[
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        "License :: CC0 1.0 Universal (CC0 1.0) Public Domain Dedication",
        "Operating System :: OS Independent",
    ],
)
