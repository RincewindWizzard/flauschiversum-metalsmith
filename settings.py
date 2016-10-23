#! /usr/bin/python3
# -*- coding: utf-8 -*-
import logging, configparser, os
from os.path import expanduser

# Configuration
posts_path = 'src/posts/'
static_path = 'static/'
static_images_path = 'static/images/'
overlay = os.path.join(static_images_path, 'Wasserzeichen.png')
index_file = 'index.md'
pretty_xml = 'pretty' # 'pretty', 'minimize', None
pagination_size = 5
posts_per_page = 5
image_dimension = (800, 600)


config = configparser.ConfigParser()
config.read(expanduser('~/.flauschiversum/auth.conf'))
if 'ftp' in config.sections():
  ftp_host     = config['ftp']['host']
  ftp_user     = config['ftp']['user']
  ftp_password = config['ftp']['password']
else:
  logging.error('Keine Zugangsdaten für den FTP Upload gefunden!')

