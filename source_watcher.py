import os, shutil, tempfile, sys, argparse, threading, logging, multiprocessing, queue
from multiprocessing import Queue, Process
import inotify.adapters
from PIL import Image

import settings

def resize_image(img_path):
  timg = tempfile.mktemp()
  shutil.move(img_path, timg)
  logging.debug('Resizing {}'.format(img_path))
  prefix, suffix = os.path.splitext(img_path)
  dst_suffix = '.JPG' if suffix == '.JPG' else '.jpg'
  dst = prefix + dst_suffix

  img = Image.open(img_path)
  if img.size[0] > settings.image_dimension[0] or img.size[1] > settings.image_dimension[1]:
    img.thumbnail(settings.image_dimension, Image.ANTIALIAS)

    with open(dst, 'wb') as f:
      img.save(f, format= 'JPEG')

    logging.info('Resizing ' + img_path)
    os.remove(timg)

def convert_all(paths, done=None):
  """
  * Converts all images in given folder, that are bigger than settings.image_dimension
  """
  for path in paths:
    for img in os.listdir(path):
      prefix, suffix = os.path.splitext(img)
      if suffix.lower() in ['.jpg', '.png']:
        resize_image(os.path.join(path, img))



def watcher_main(queue, stop):
  """
  * Extra Process that watches for source change because of GIL, you know
  """
  logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
  # convert all images to max size first
  convert_all([ path for path, _, _ in os.walk(settings.posts_path) ])


  watch = inotify.adapters.InotifyTree(
    bytes(settings.posts_path, 'utf-8'),
    mask=IN_CLOSE_WRITE
  )

  # regex for multiple data types
  image_files   = [ re.compile(s) for s in [r'.*\.png$', r'.*\.jpg$', r'.*\.JPG$'] ]
  watched_files = [ re.compile(s) for s in [r'.*\.png$', r'.*\.jpg$', r'.*\.JPG$', r'index\.md$'] ]

  last_file = None
  for event in watch.event_gen():
    if stop.is_set(): break
    if event:
      header, type_names, watch_path, filename = event
      watch_path = watch_path.decode('utf-8')
      filename = filename.decode('utf-8')
      filepath = os.path.join(watch_path, filename)

      if not filepath == last_file:
        if any([ r.match(filename) for r in watched_files ]):
          queue.put(filepath)
        if any([ r.match(filename) for r in image_files ]):
          resize_image(filepath)

      last_file = filepath

def watch_sources(progress=None, stopped=None):
  """
  * Watch for changes in the post path.
  * progress is called everytime something changed and code has to be recompiled.
  * Automatically resizes image assets.
  """
  multiprocessing.set_start_method('spawn')
  q = Queue()
  timeout = 1
  stop_event = multiprocessing.Event()
  p = Process(target=watcher_main, args=(q, stop_event))
  p.start()

  while not stopped():
    try:
      filepath = q.get(True, timeout)
      progress(filepath)
    except queue.Empty as e:
      ...

  stop_event.set()




"""

def main():
  parser = argparse.ArgumentParser(
    prog = 'asset_resizer',
    description = 'Resize every image in a folder to a given max size. ' + 
                  'Watch for new Images.'
  )
  parser.add_argument('paths', nargs='+', help='Path to the folder to be watched.')
  args = parser.parse_args()

  paths = []
  for path in args.paths:
    paths.extend([ path for path, _, _ in os.walk(path) ])

  try:
    convert_all(paths)
  except KeyboardInterrupt:
    ...

if __name__ == '__main__':
  logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.DEBUG)
  main()"""
