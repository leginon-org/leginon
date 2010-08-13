import math

def equallyAngled(min, max, start, step):
	if step == 0:
		raise ValueError('step size is zero')
	if min > max:
		min, max = max, min
	tilt = start
	tilts = []
	while tilt >= min and tilt <= max:
		tilts.append(tilt)
		tilt += step
	return tilts

def equallySloped(n):
	if n < 2:
		raise ValueError
	m = (2**n)/4
	angles = []
	angles += [math.atan2(-m, i) for i in range(0, m)]
	angles += [math.atan2(i, m) for i in range(-m, 0)]
	angles += [math.atan2(i, m) for i in range(0, m)]
	angles += [math.atan2(m, i) for i in range(m, 0, -1)]
	return angles

def cosineSloped(max,n):
	if n < 2 or max < math.radians(0.02):
		raise ValueError
	bestscale = 1
	for step in (0.1,0.01,0.001,0.0001,0.00001):
		scales = map((lambda x: bestscale - 10*step + x*step), range(0,10))
		for scale in scales:
			tilts=[0.0]
			for i in range(1,n):
				tilt = tilts[i-1]+scale*math.cos(tilts[i-1])
				tilts.append(tilt)
			if tilts[-1] > max:
				break
		bestscale = scale
	negatives = map((lambda x: -x),tilts)
	negatives.pop(0)
	tilts.extend(negatives)
	degrees = map((lambda x: math.degrees(x)),tilts)
	return tilts

def angles2lines(thetas, n):
	p = len(thetas)
	lines = []

	for theta in thetas:
		if theta >= 3*math.pi/4:
			theta -= math.pi

		if round(theta, 6) >= -math.pi/4 and round(theta, 6) <= math.pi/4:
			line = n*0.5*(1 + math.tan(theta)) + 1
		else:
			line = n*(1.5 + 0.5*math.tan(math.pi/2 - theta)) + 1

		line = round(line)

		if line > 2*n:
			line = line - 2*n
		lines.append(line)

	return lines

def symmetric(thetas, n):
	n = 2**n
	lines = angles2lines(thetas, n) 
	symmetric_angles = []
	for line in lines:
		if line <= n + 1:
			symmetric_angle = math.atan((n + 2 - 2*line)/n)
		else:
			symmetric_angle = math.pi/2 - math.atan((3*n + 2 - 2*line)/n)
		if symmetric_angle > math.pi/2:
			symmetric_angle -= math.pi
		symmetric_angles.append(symmetric_angle)
	return symmetric_angles

class Tilts(object):
	def __init__(self, **kwargs):
		self.update(**kwargs)

	def getTilts(self):
		return [list(tilts) for tilts in self.tilts]

	def update(self, **kwargs):
		attrs = ['min', 'max', 'start', 'step', 'n', 'equally_sloped']
		for attr in attrs:
			if attr not in kwargs:
				continue
			setattr(self, attr, kwargs[attr])

		for attr in attrs:
			if not hasattr(self, attr) or getattr(self, attr) is None:
				self.tilts = []
				return

		self.updateTilts()

	def updateTilts(self):
		self.tilts = []

		if self.equally_sloped:
			if self.start < self.min or self.start > self.max:
				raise ValueError('start angle out of range')
	
			tilts = cosineSloped(max(abs(self.max),abs(self.min)),self.n)
			tilts.sort()

			tolerance = math.radians(0.01)
			while tilts[0] < self.min-tolerance:
				if not tilts:
					raise ValueError('no angles from parameters specified')
				tilts.pop(0)
	
			while tilts[-1] > self.max+tolerance:
				if not tilts:
					raise ValueError('no angles from parameters specified')
				tilts.pop(-1)

			d = [abs(tilt - self.start) for tilt in tilts]
			index = d.index(min(d))
	
			tilt_half = tilts[index:]
			if len(tilt_half) > 1:
				self.tilts.append(tilt_half)

			if index < len(tilts) - 1:
				index += 1
			tilt_half = tilts[:index]
			tilt_half.reverse()
			if len(tilt_half) > 1:
				self.tilts.append(tilt_half)
			'''
		# This is for symmetrical data collection not equally sloped
		if self.equally_sloped:
			parameters = [
				(self.min, self.max, self.start, self.step),
				(self.min, self.max, self.start, -self.step),
			]

			for args in parameters:
				tilts = equallyAngled(*args)
				tilts = symmetric(tilts, self.n)
				if len(tilts) < 2:
					continue
				self.tilts.append(tilts)
			'''
		else:
			parameters = [
				(self.min, self.max, self.start, self.step),
				(self.min, self.max, self.start, -self.step),
			]

			for args in parameters:
				tilts = equallyAngled(*args)
				if len(tilts) < 2:
					continue
				self.tilts.append(tilts)

			if not self.tilts:
				raise ValueError('no angles from parameters specified')

if __name__ == '__main__':
	kwargs = {
		'equally_sloped': True,
		'min': math.radians(-60),
		'max': math.radians(50),
		'start': math.radians(0),
		'step': math.radians(1),
		'n': 10,
	}
	tilts = Tilts(**kwargs)
	print sum([len(t) for t in tilts.getTilts()])
	for ts in tilts.getTilts():
		print ' '
		for t in ts:
			print '%.1f' % math.degrees(t)
	#tilts.update(equally_sloped=True)
	#print sum([len(t) for t in tilts.getTilts()])
	#print tilts.getTilts()

