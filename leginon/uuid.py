import md5
import random
import socket
import time

def uuid(*args):
	# not really a uuid, but close
  t = long(time.time()*1000)
  r = long(random.random()*100000000000000000L)
  try:
    a = socket.gethostbyname(socket.gethostname())
  except:
    a = random.random()*100000000000000000L
  data = str(t)+' '+str(r)+' '+str(a)+' '+str(args)
  data = md5.md5(data).hexdigest()
  return data

