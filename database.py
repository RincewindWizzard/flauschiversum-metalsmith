#! /usr/bin/python3
# -*- coding: utf-8 -*-

#stdlib
import logging, os
from datetime import datetime
from threading import RLock, Thread

# external libraries
import frontmatter
from slugify import slugify
from markdown_slideshow import compile as markdown

# own libraries
import settings
from PIL import Image
from markdown_slideshow import resized_image

def tryget(doc, key, msg=None):
  """ Try getting a value from a dic and log if error """
  if key in doc.keys():
    return doc[key]
  else:
    if msg: logging.warning(msg)
    return None



class Post(object):
  """
  * This is the Post class, which represents a post with all its assets.
  * A post is identified by its path and two posts with the same path point to the same object.
  """
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
  def datestring(self):
    months = ['Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli', 'August', 'September', 'Oktober', 'November', 'Dezember']
    return '{}. {} {}'.format(self.date.day, months[self.date.month - 1], self.date.year)

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

    self.index_path = os.path.join(self.path, settings.index_file)
    doc = frontmatter.load(self.index_path)

    self.title = tryget(doc, 'title', '"{}" hat keinen Titel!'.format(self.index_path))
    self.slug = tryget(doc, 'slug')
    if not self.slug:
      self.slug = slugify(self.title)
    self.date = tryget(doc, 'date', '"{}" hat kein Veröffentlichungsdatum!'.format(self.title))
    database['post_by_url'][self.url] = self

    if not self.title: self.title = self.path
    self.author = tryget(doc, 'author', '"{}" hat keinen Autor!'.format(self.title))
    self.image = tryget(doc, 'image', '"{}" hat kein Thumbnail!'.format(self.title))
    self.thumb = os.path.join(self.url, resized_image(self.image, 200)) if self.image else None
    self.excerpt = tryget(doc, 'excerpt', '"{}" hat keine Kurzfassung!'.format(self.title))

    self.category = tryget(doc, 'category')
    if not self.category:
      self.category = os.path.split(os.path.dirname(self.path))[1]
    else:
      self.category = slugify(self.category)

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

    for category_path in os.listdir(settings.posts_path):
      for post_path in os.listdir(os.path.join(settings.posts_path, category_path)):
        Post(os.path.join(settings.posts_path, category_path, post_path))

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



def create_new_post(title, category, author, publish_date, description, thumb_src):
  """ 
  * Creates a new Post in the src directory
  * Raises FileExistsError if post already exists
  """
  post_path = os.path.join(settings.posts_path, category, slugify(title))
  os.mkdir(post_path)
  thumb_dst = os.path.join(os.getcwd(), post_path, slugify(title) + '_thumb.jpg')
  thumb = Image.open(thumb_src)
  thumb.thumbnail(settings.image_dimension, Image.ANTIALIAS)
  thumb.save(thumb_dst, format= 'JPEG')


  with open(os.path.join(post_path, settings.index_file), 'w') as f:
    f.write("""---
title: "{}"
category: {}
author: {}
date: {}
image: "{}"
excerpt: "{}"
---

""".format(title, category, author, datetime.strftime(publish_date, settings.date_fmt), os.path.basename(thumb_dst), description))
  return Post(post_path)
