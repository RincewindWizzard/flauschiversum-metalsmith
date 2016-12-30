#! /usr/bin/python3
# -*- coding: utf-8 -*-
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf
from datetime import datetime, date
import os, subprocess

import settings, database, asset_resizer

def open_file(path):
  """
  * Opens a file with the standard tool.
  """
  subprocess.call([settings.file_opener, path])

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

  def on_exit(self, *args):
    Gtk.main_quit()

  def on_cancel(self, *args):
    self.on_exit()


  def on_apply(self, assistant):
    """
    * Create the new Post and open a text editor
    """
    try:
      post = database.create_new_post(
        self.post_title, 
        self.post_category, 
        self.post_author,
        self.post_date,
        self.post_description,
        self.post_image
      )
      open_file(post.index_path)
      open_file(post.path)
      asset_resizer.start_watch_thread(post.path)
    except FileExistsError as e:
      self.on_error(e, "Post already exists!")

  def buildlog(self, level, message, path=None):
    """
    * Log an error in the debug log area.
    * level (string) indicates the severity of the error
    * path points to the file where the error occured
    """
    error_list = self.builder.get_object("error_list")
    error_list.append([level, message, path])

  def on_error(self, error, msg):
    """
    * Display an Error dialog if something nasty happens.
    """
    dialog = Gtk.MessageDialog(
      self.builder.get_object('create_post_assistant'), 
      0, 
      Gtk.MessageType.ERROR,
      Gtk.ButtonsType.CANCEL,
      error.args[0]
    )
    dialog.format_secondary_text(msg)
    dialog.run()
    dialog.destroy()

  def on_error_clicked(self, error_list_view, treepath, column):
    """
    * Opens the file, where a compile error occured.
    """
    model = error_list_view.get_model()
     # column 2 is for file path of error
    error_file = model.get_value(model.get_iter(treepath), 2)
    open_file(error_file)

  def post_image_chosen(self, file_chooser):
    """
    * If a post image has been chosen, it has to be resized and displayed
    * If everything works well the current slide is completed
    """
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
