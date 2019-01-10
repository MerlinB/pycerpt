from .pdfgen import Story


FILE_EXTENSIONS = {
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
    def __init__(self, title, paragraphs):
        self.title = title
        self.paragraphs = list(paragraphs)

    def get_markdown(self):
        text = f'# {self.title}\n\n'
        for paragraph in self.paragraphs:
            text += f'{paragraph}\n\n'
        return text

    def save(self, path):
        extension = path.split('.')[-1].lower()
        if extension in FILE_EXTENSIONS['markdown']:
            self.save_text(path)
        elif extension == 'pdf':
            self.save_pdf(path)
        else:
            raise NotImplementedError()

    def save_text(self, path):
        with open(path, 'w') as file:
            file.write(self.get_markdown())

    def save_pdf(self, path):
        story = Story(paragraphs=self.paragraphs)
        story.add_title(self.title)
        story.save(path)
