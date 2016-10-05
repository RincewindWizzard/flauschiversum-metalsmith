import sys, os, io, logging
from datetime import datetime
from threading import RLock, Thread
from PIL import Image
import frontmatter
from markdown_slideshow import compile as markdown
from slugify import slugify

from flask import Flask, request, send_file
app = Flask(__name__)

# --------------------
# Configuration
posts_path = 'src/posts/'
static_path = 'src/static/'
static_images_path = 'src/static/images/'
index_file = 'index.md'

# --------------------

def tryget(doc, key, msg=None):
  """ Try getting a value from a dic and log if error """
  if key in doc.keys():
    return doc[key]
  else:
    if msg: logging.warning(msg)
    return None

class Post(object):
  def __new__(cls, path):
    if path in database['posts']:
      return database['posts'][path]
    else:
      return super(Post, cls).__new__(cls)

  def __init__(self, path):
    database['posts'][path] = self
    self._path = path
    self.date = None
    self.slug = None
    self.reload()

  @property
  def path(self):
    return self._path

  def check_images(self):
    """ Test if all referenced images exist """
    for alt, src in self.images:
      try:
        src = os.path.join(self.path, src)
        if not os.path.isfile(src):
          logging.error('Das Bild "{}" existiert nicht in {}'.format(alt, src))
      except TypeError as e:
        logging.exception('Ein Fehler trat auf: os.path.join({}, {})'.format(os.path.dirname(self.path), src))


  @property
  def url(self):
    if self.date and self.slug:
      return '/{}/{:02d}/{}/'.format(self.date.year, self.date.month, self.slug)
    else:
      return None

  def reload(self):
    # the url might change
    if self.url in database['post_by_url']:
      del database['post_by_url'][self.url]

    index_path = os.path.join(self.path, index_file)
    doc = frontmatter.load(index_path)

    self.title = tryget(doc, 'title', '"{}" hat keinen Titel!'.format(index_path))
    self.slug = tryget(doc, 'slug')
    if not self.slug:
      self.slug = slugify(self.title)
    self.date = tryget(doc, 'date', '"{}" hat kein Veröffentlichungsdatum!'.format(self.title))
    database['post_by_url'][self.url] = self

    if not self.title: self.title = self.path
    self.author = tryget(doc, 'author', '"{}" hat keinen Autor!'.format(self.title))
    self.image = tryget(doc, 'image', '"{}" hat kein Thumbnail!'.format(self.title))
    self.excerpt = tryget(doc, 'excerpt', '"{}" hat keine Kurzfassung!'.format(self.title))

    self.category = tryget(doc, 'category')
    if not self.category:
      self.category = os.path.split(os.path.dirname(self.path))[1]

    self.content = doc.content
    self.html, self.images = markdown(self.content)
    # ensure Thumbnail is included in list
    if self.image:
      self.images.append((self.title, self.image))

    self.check_images()

# In Memory database
dbLock = RLock()
database = {
  'posts': {},
  'post_by_url': {}
}

def load_posts():
  with dbLock:
    # flushing
    del database['posts']
    database['posts'] = {}

    for category_path in os.listdir(posts_path):
      for post_path in os.listdir(os.path.join(posts_path, category_path)):
        Post(os.path.join(posts_path, category_path, post_path))

def posts_by_date(category=None):
  if category:
    posts = [post for post in database['posts'].values() if post.category == category]
  else:
    posts = database['posts'].values()
  return sorted(posts, key=lambda x: x.date)

def categories():
  cats = set()
  for post in database['posts'].values():
    cats.add(post.category)
  return cats


#---------------------------


@app.route('/')
def hello_world():
  with dbLock:
    html = ['<ul>']
    for category in categories():
      html.append('<li>')
      html.append(category)
      html.append('<ul>')
      for post in posts_by_date(category):
        html.append('<li>')
        html.append('<a href="{}">{}</a>'.format(post.url, post.title))
        html.append('</li>')
      html.append('</ul>')
      html.append('</li>')

    #titles.append(post.title)
    html.append('</ul>')
    return ''.join(html)


@app.route('/<int:year>/<int:month>/<title>/')
def render_post(year, month, title):
  with dbLock:
    return database['post_by_url'][request.path].html

@app.route('/<int:year>/<int:month>/<title>/<int:width>x<int:height>/<image>')
@app.route('/<int:year>/<int:month>/<title>/<int:width>x/<image>', defaults={'height': 1000})
@app.route('/<int:year>/<int:month>/<title>/x<int:height>/<image>', defaults={'width': 1000})
def convert_thumbnail(year, month, title, width, height, image):
  post = database['post_by_url']['/{}/{:02d}/{}/'.format(year, month, title)]
  img = Image.open(os.path.join(post.path, image))
  overlay = Image.open(os.path.join(static_images_path, 'Flauschiversum_overlay.png'))
  overlay.thumbnail(img.size, Image.ANTIALIAS)

  img.paste(overlay, (img.size[0] - overlay.size[0], img.size[1] - overlay.size[1]), overlay)

  img.thumbnail((width, height), Image.ANTIALIAS)
  f = io.BytesIO()
  img.save(f, format= 'JPEG')
  return send_file(io.BytesIO(f.getvalue()),
                   attachment_filename=image,
                   mimetype='image/png')



if __name__ == '__main__':
  load_posts()
  app.run()
