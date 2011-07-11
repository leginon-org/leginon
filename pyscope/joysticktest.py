try:
	scope = 'Tecnai'
	import pyscope.registry
	import time
	log_file = 'speedtest%s.log' % (int(time.time()))
	t = pyscope.registry.getClass(scope)()

	def write_log(fields):
		line = '\t'.join(map(str, fields)) + '\n'
		f = open(log_file, 'a')
		f.write(line)
		f.close()

	for i in range(500):
		print 'iteration', i
		pos = t.getStagePosition()
		t0 = time.time()
		time.sleep(0.25)
		write_log([t0, pos['x'], pos['y']])
except Exception, e:
	print e
raw_input('enter to quit')
