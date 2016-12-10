#! /usr/bin/python3
# -*- coding: utf-8 -*-
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf
from datetime import datetime, date
import os, subprocess

import settings
import database



class PublishAssistant(object):
  def __init__(self):
    self.builder = Gtk.Builder()
    self.builder.add_from_file("Assistant.glade")
    self.builder.connect_signals(self)
    self.assistant = self.builder.get_object("create_post_assistant")
    self.post_image = None

    today = datetime.now()
    date_picker = self.builder.get_object("date_picker")
    date_picker.select_month(today.month-1, today.year)
    date_picker.select_day(today.day)
    #window.connect("delete-event", Gtk.main_quit)

  def show(self):
    self.assistant.show_all()

  @property
  def post_title(self):
    return self.builder.get_object("title_entry").get_text()

  @property
  def post_description(self):
    desc_buf = self.builder.get_object("description_entry").get_buffer()
    return desc_buf.get_text(*desc_buf.get_bounds(), False)

  @property
  def post_date(self):
    selected = self.builder.get_object("date_picker").get_date()
    return date(selected.year, selected.month + 1, selected.day)

  @property
  def post_category(self):
    combo = self.builder.get_object("category_box")
    index = combo.get_active_iter()
    return combo.get_model()[index][1]

  @property
  def post_author(self):
    combo = self.builder.get_object("author_box")
    index = combo.get_active_iter()
    return combo.get_model()[index][0]

  def onDaySelected(self, *foo):
    print(self.post_date)

  def onExit(self, *args):
    Gtk.main_quit()

  def onCancel(self, *args):
    self.onExit()

  def onApply(self, assistant):
    try:
      post = database.create_new_post(
        self.post_title, 
        self.post_category, 
        self.post_author,
        self.post_date,
        self.post_description,
        self.post_image
      )
      subprocess.call([settings.file_opener, post.index_path])
    except FileExistsError as e:
      print("Post already exists!")



  def post_image_choosen(self, file_chooser):
    self.post_image = file_chooser.get_filename()
    img_display = self.builder.get_object("post_image_display")
    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
      self.post_image, 
      width  = img_display.get_allocation().width,
      height = img_display.get_allocation().height,
      preserve_aspect_ratio=True
    )
    img_display.set_from_pixbuf(pixbuf)
    self.assistant.set_page_complete(
      self.builder.get_object("image_page"), 
      True
    )

  def check_complete(self, page):
    """ Sets page as complete if entry is filled """
    if page == self.builder.get_object("main_page"):
      post_path = settings.post_path(self.post_title, self.post_category)
      self.assistant.set_page_complete(
        page, 
        not (self.post_title == "" or os.path.exists(post_path))
      )
    else:
      self.assistant.set_page_complete(
        page, 
        all(not entry.get_text() == "" for entry in page if type(entry) == Gtk.Entry)
      )

if __name__ == '__main__':
  assistant = PublishAssistant()
  assistant.show()
  Gtk.main()
