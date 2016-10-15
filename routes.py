#! /usr/bin/python3
# -*- coding: utf-8 -*-
import subprocess, os, io
from datetime import datetime
from PIL import Image
from flask import Flask, Response, request, send_file, render_template, send_from_directory
app = Flask(__name__)

import htmlmin
from bs4 import BeautifulSoup as parse_html_string

import settings
from database import dbLock, database
import database as db


def postprocess(html):
  if settings.pretty_xml == 'pretty':
    return parse_html_string(html, 'lxml').prettify()
  elif settings.pretty_xml == 'minimize':
    return htmlmin.minify(html)
  else:
    return html

@app.route('/', defaults={'category': None})
@app.route('/basteln/',   defaults={'category': 'basteln'})
@app.route('/brandings/', defaults={'category': 'brandings'})
@app.route('/filzen/',    defaults={'category': 'filzen'})
@app.route('/malen/',     defaults={'category': 'malen'})
@app.route('/nähen/',     defaults={'category': 'nahen'})
@app.route('/naehen/',    defaults={'category': 'nahen'})
@app.route('/nahen/',     defaults={'category': 'nahen'})
@app.route('/wolle/',     defaults={'category': 'wolle'})
def index(category):
  with dbLock:
    html = render_template(
      'index.html', 
      posts=list(reversed(db.posts_by_date(category))),
      category=category,
      currentyear=datetime.now().year, 
      currentPage=0
    )
    return postprocess(html)

@app.route('/<int:year>/<int:month>/<title>/')
def render_post(year, month, title):
  with dbLock:
    post = database['post_by_url'][request.path]
    return postprocess(
      render_template('post.html', post=post, title=post.title)
    )
    

@app.route('/<int:year>/<int:month>/<title>/<int:width>x<int:height>/<image>')
@app.route('/<int:year>/<int:month>/<title>/<int:width>x/<image>', defaults={'height': 1000})
@app.route('/<int:year>/<int:month>/<title>/x<int:height>/<image>', defaults={'width': 1000})
def convert_thumbnail(year, month, title, width, height, image):
  post = database['post_by_url']['/{}/{:02d}/{}/'.format(year, month, title)]
  img = Image.open(os.path.join(post.path, image))
  overlay = Image.open(os.path.join(settings.static_images_path, 'Flauschiversum_overlay.png'))
  overlay.thumbnail(img.size, Image.ANTIALIAS)

  img.paste(overlay, (img.size[0] - overlay.size[0], img.size[1] - overlay.size[1]), overlay)

  img.thumbnail((width, height), Image.ANTIALIAS)
  f = io.BytesIO()
  img.save(f, format= 'JPEG')
  return send_file(io.BytesIO(f.getvalue()),
                   attachment_filename=image,
                   mimetype='image/png')

@app.route('/<path>/<basename>')
@app.route('/<basename>', defaults={'path': ''})
def static_files(path, basename):
  return send_from_directory(os.path.join('static', path), basename)

@app.route('/style.css')
def style():
  return Response(
    subprocess.run(['lessc', 'static/style/main.less'], 
      stdout=subprocess.PIPE).stdout,
    mimetype='text/css'
  )



