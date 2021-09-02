import time
from pyscope import tietz2

name = raw_input('Filename ? (ex: 123_1) ')
exp_time_ms = float(raw_input('exposure time (ms) ? '))
movie_length = float(raw_input('Movie length (s) ? '))

t=tietz2.EmMenuF416()
t.setDimension({'x':2048,'y':2048})
t.setBinning({'x':2,'y':2})
t0 = time.time()
t.startMovie(name, exp_time_ms)
print('start took %.2f s' % (time.time()-t0))
time.sleep(movie_length)
t0 = time.time()
t.stopMovie(name, exp_time_ms)
print('stop took %.2f s' % (time.time()-t0))
