import os
from markdown import Markdown
from markdown.extensions import Extension
from markdown.treeprocessors import Treeprocessor

class Slideshow(Treeprocessor, Extension):
  def extendMarkdown(self, md, md_globals):
    self.md = md
    md.treeprocessors.add('slideshow', self, '>inline')

  def run(self, doc):
    self.md.images = []
    for image in doc.findall('.//img'):
      self.md.images.append((image.get('alt'), image.get('src')))
      dirname = os.path.dirname(image.get('src'))
      basename = os.path.basename(image.get('src'))
      image.set('src', os.path.join(dirname, 'x500', basename))


md = Markdown(extensions=[Slideshow()])

def compile(text):
  return md.convert(text), md.images

