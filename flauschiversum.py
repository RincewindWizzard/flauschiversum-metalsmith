#! /usr/bin/python3
# -*- coding: utf-8 -*-

from routes import app
import database as db

if __name__ == '__main__':
  db.load_posts()
  app.run()
