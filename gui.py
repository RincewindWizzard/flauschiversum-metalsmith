#! /usr/bin/python3
# -*- coding: utf-8 -*-
import os, subprocess, logging, threading, types, re, multiprocessing, queue, copy
from multiprocessing import Queue, Process
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf, GLib
import inotify.adapters
from inotify.constants import IN_DELETE, IN_CREATE, IN_MODIFY, IN_CLOSE_WRITE
from datetime import datetime, date
import settings, database, source_watcher, flauschiversum

class Worker(threading.Thread):
  """
  * This is a helper class for scheduling work outside of the main loop.
  * The callback and progress functions are called in the main loop.
  * The target function is called in a seperate Thread.
  * It gets a Thread safe progress callback and a stopped function, 
  * which tells it to clean up and quit.
  * You can specify how many times the job has to be done.
  """
  def __init__(self, target=None, progress=None, callback=None, times=0, *args, **kwargs):
    self._stopped = False
    self._redo = times # how many times should the work be done, or True if forever
    self._redo_condition = threading.Condition()
    self._on_progress = progress

    def run(*rargs, **rkwargs):
      while not self._stopped:
        logging.debug('Worker {} scheduling his job.'.format(threading.current_thread().name))
        result = target(*rargs, **rkwargs, progress=self.on_progress, stopped=lambda: self._stopped)
        if callback: GLib.idle_add(callback, result)
        with self._redo_condition:
          self._redo_condition.wait_for(lambda: self._redo > 0 or self._redo == True or self._stopped)
          if type(self._redo) == int and self._redo > 0: 
            self._redo -= 1
      logging.debug('Worker {} stopped.'.format(threading.current_thread().name))

    threading.Thread.__init__(self, target = run, *args, **kwargs)

  def on_progress(self, *args, **kwargs):  
    if self._on_progress: GLib.idle_add(self._on_progress, *args, **kwargs)

  def stop(self):
    self._stopped = True
    with self._redo_condition:
      self._redo_condition.notify_all()

  def redo(self):
    """ Tell the Worker to schedule the work for one more time """
    with self._redo_condition:
      if type(self._redo) == int:
        self._redo += 1 
      else: 
        self._redo = 1 
      self._redo_condition.notify_all()

  def forever(self):
    self._redo = True



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

    def dbload(*args, **kwargs):
      database.load_posts()
      return database.get_errors()

    self.database_worker = Worker(dbload, callback=self.on_database_read)
    self.database_worker.start()

    self.source_watcher = Worker(source_watcher.watch_sources, progress=self.on_source_changed)
    self.source_watcher.start()

    self.webserver_process = Process(target = flauschiversum.main)
    logging.debug('start webserver')
    self.webserver_process.start()


    # create worker for icon loading
    def load_icons(*args, **kwargs):
      self.error_icon   = Gtk.IconTheme.get_default().load_icon(Gtk.STOCK_DIALOG_ERROR, 16, 0)
      self.warning_icon = Gtk.IconTheme.get_default().load_icon(Gtk.STOCK_DIALOG_WARNING, 16, 0)

    w = Worker(load_icons)
    w.start()
    w.stop() # destroy after fisrt use

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
    self.assistant.hide()
    self.database_worker.stop()
    self.source_watcher.stop()
    self.webserver_process.terminate()

    Gtk.main_quit()

  def join(self):
    self.database_worker.join()
    self.source_watcher.join()
    self.webserver_process.join()

  def on_cancel(self, *args):
    self.on_exit()

  def on_new_post_btn_clicked(self, btn):
    """ User decided to create a new post """
    logging.debug('new_post')
    self.builder.get_object("create_post_assistant").set_current_page(1)

  def on_edit_posts_btn_clicked(self, btn):
    """ User decided to edit old posts. """
    logging.debug('edit_post')
    self.builder.get_object("create_post_assistant").set_current_page(4)
    open_file(settings.posts_path)
    open_file(settings.localserver)

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
      open_file(settings.localserver)
    except FileExistsError as e:
      self.on_error(e, "Post already exists!")

  def on_source_changed(self, filepath):
    logging.debug('source changed')
    self.reload_build_log()

  def on_database_read(self, errors):
    logging.debug("Databases reloaded!")
    error_list = self.builder.get_object("error_list")
    error_list.clear()

    contains_serious = False
    for level, msg, post in errors:
      if level == logging.ERROR:
        contains_serious = True
        error_list.append([self.error_icon, level, msg, post.path])
      elif level == logging.WARNING:
        error_list.append([self.warning_icon, level, msg, post.path])

    self.assistant.set_page_complete(
      self.builder.get_object("debug_log_area"),
      not contains_serious
    )

  def reload_build_log(self):
    self.database_worker.redo()

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
     # column 3 is for file path of error
    error_file = model.get_value(model.get_iter(treepath), 3)
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
  logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
  assistant = PublishAssistant()
  assistant.show()
  
  """
  def on_progress(n):
    print('Progress', n)

  def run(progress, stopped):
    import time
    for j in range(100000):
      if stopped(): break
      time.sleep(0.1)
      progress(j)
    return "Done"

  def callback(arg):
    print(arg)

  w = Worker(target = run, callback = callback, progress = on_progress)
  #w.daemon = True
  w.forever()
  w.start()"""
  Gtk.main()
  assistant.join()
