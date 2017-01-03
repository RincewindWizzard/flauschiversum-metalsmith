import subprocess

def main():
  p = subprocess.Popen(
    ['git', 'add', 'src'],
    stderr = subprocess.PIPE,
    stdout = subprocess.PIPE
  )
  stdout, stderr = p.communicate()
  p.wait()
  print(stdout.decode('utf-8'))


  p = subprocess.Popen(
    ['git', 'commit', '-m', 'Beiträge bearbeitet'],
    stderr = subprocess.PIPE,
    stdout = subprocess.PIPE
  )
  stdout, stderr = p.communicate()
  p.wait()
  print(stdout.decode('utf-8'))

if __name__ == '__main__':
  main()
