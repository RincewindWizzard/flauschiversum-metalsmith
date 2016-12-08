#! /usr/bin/python3
# -*- coding: utf-8 -*-
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf
from datetime import datetime, date
import os



class PublishAssistant(object):
  def __init__(self):
    self.builder = Gtk.Builder()
    self.builder.add_from_file("Assistant.glade")
    self.builder.connect_signals(self)
    self.assistant = self.builder.get_object("create_post_assistant")

    today = datetime.now()
    date_picker = self.builder.get_object("date_picker")
    date_picker.select_month(today.month, today.year)
    date_picker.select_day(today.day)
    #window.connect("delete-event", Gtk.main_quit)

  def show(self):
    self.assistant.show_all()

  @property
  def post_title(self):
    return self.builder.get_object("title_entry").get_text()

  @property
  def post_date(self):
    selected = self.builder.get_object("date_picker").get_date()
    return date(selected.year, selected.month + 1, selected.day)

  @property
  def post_category(self):
    combo = self.builder.get_object("category_box")
    index = combo.get_active_iter()
    return combo.get_model()[index][1]

  def onDaySelected(self, *foo):
    print(self.post_date)

  def onExit(self, *args):
    Gtk.main_quit()

  def onCancel(self, *args):
    self.onExit()

  def onApply(self, assistant):
    print(os.path.join(os.getcwd(), 'src/posts/', self.post_category, self.post_title))

  def post_image_choosen(self, file_chooser):
    post_image = file_chooser.get_filename()
    img_display = self.builder.get_object("post_image_display")
    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
      post_image, 
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
      self.assistant.set_page_complete(
        page, 
        not self.builder.get_object("title_entry").get_text() == ""
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
