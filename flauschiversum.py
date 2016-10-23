#! /usr/bin/python3
# -*- coding: utf-8 -*-

import logging
from routes import app
import database as db

if __name__ == '__main__':
  db.load_posts()
  try:
    app.run(host="0.0.0.0")
  except OSError as e:
    if e.errno == 98:
      logging.error("Address already in use!")
    else:
      raise e
