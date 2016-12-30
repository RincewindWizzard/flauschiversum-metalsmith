import os, shutil, tempfile, sys, argparse, threading, logging
import inotify.adapters
from PIL import Image

import settings

def resize_image(img_path):
  timg = tempfile.mktemp()
  #shutil.move(img_path, timg)

  img = Image.open(img_path)
  if img.size[0] > settings.image_dimension[0] or img.size[1] > settings.image_dimension[1]:
    img.thumbnail(settings.image_dimension, Image.ANTIALIAS)

    with open(timg, 'wb') as f:
      img.save(f, format= 'JPEG')

    shutil.move(timg, os.path.splitext(img_path)[0] + '.jpg')


def watch_path(path, done=None):
  i = inotify.adapters.Inotify()
  path = bytes(path, 'utf-8')
  i.add_watch(path)

  try:
    files_done = []
    for event in i.event_gen():
      # stop watching if done
      if done and done(): return

      try:
        if event is not None:
          header, type_names, watch_path, filename = event

          if 'IN_CLOSE_WRITE' in type_names or 'IN_CLOSE_NOWRITE' in type_names:
            path = os.path.join(watch_path.decode('utf-8'), filename.decode('utf-8'))
            filename = os.path.basename(path)
            prefix, suffix = os.path.splitext(filename)
            
            if not prefix in files_done and suffix.lower() in ['.jpg', '.png']:
              files_done.append(prefix)
              resize_image(path)
      except Exception as e:
        logging.error(e)
        
  finally:
    i.remove_watch(path)


def convert_all(path, done=None):
  """
  * Converts all images in given folder, that are bigger than settings.image_dimension
  """
  for img in os.listdir(path):
    prefix, suffix = os.path.splitext(img)
    if suffix.lower() in ['.jpg', '.png']:
      resize_image(os.path.join(path, img))

  watch_path(path, done)



def start_watch_thread(path):
  """
  * Creates and returns a new Thread,
  * which watches on the given folder for new image files.
  * Can be stopped with thread.stop()
  """
  def run():
    t = threading.currentThread()
    t.done = False
    convert_all(path, lambda: t.done)

  t = threading.Thread(target = run)
  t.daemon = True

  def stop():
    t.done = True

  t.stop = stop
  t.start()
  return t


def main():
  parser = argparse.ArgumentParser(
    prog = 'asset_resizer',
    description = 'Resize every image in a folder to a given max size. ' + 
                  'Watch for new Images.'
  )
  parser.add_argument('path', help='Path to the folder to be watched.')

  args = parser.parse_args()
  try:
    convert_all(args.path)
  except KeyboardInterrupt:
    ...

if __name__ == '__main__': 
  main()
