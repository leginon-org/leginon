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
		'''
		Groups of tilts for prediction in radians.
		If there are two, the first is tilting toward positive from start.
		the second is tilting toward negative from start.
		'''
		return [list(tilts) for tilts in self.tilts]

	def getTiltSequence(self):
		'''
		Collection sequence of tilts in radians. A single list based on IndexSequence.
		'''
		return self.tilt_sequence

	def getIndexSequence(self):
		'''
		Collection sequence map indices in getTilts
		'''
		return self.index_sequence

	def getTargetAdjustIndices(self):
		'''
		Target adjustment index in TiltSequence
		'''
		return self.target_adjust_indices

	def addOnTilts(self,tilts):
		'''
		add custom tilts, in radians. Will only add ones in the range
		of the input tilts
		'''
		tilt_num = len(tilts)
		if tilt_num < 2:
			# can not judge whether the add_on is in range
			return tilts
		for add_on_tilt in self.add_on:
			if add_on_tilt not in tilts and add_on_tilt < max(tilts) and add_on_tilt > min(tilts):
				tilts.append(add_on_tilt)
				reverse_sort = add_on_tilt < tilts[0]
		# sort if at least one tilt is added
		if tilt_num < len(tilts):
			tilts.sort()
			if reverse_sort:
				tilts.reverse()
		return tilts

	def update(self, **kwargs):
		attrs = ['min', 'max', 'start', 'step', 'n', 'equally_sloped', 'add_on', 'tilt_order']
		for attr in attrs:
			if attr not in kwargs:
				continue
			setattr(self, attr, kwargs[attr])

		for attr in attrs:
			if not hasattr(self, attr) or getattr(self, attr) is None:
				# first initialization has no kwargs, just initialize'
				self.tilts = []
				return
		self.updateTilts()
		self.updateTiltSequence()

	def updateTilts(self):
		self.tilts = []

		if self.equally_sloped:
			if self.start < self.min or self.start > self.max:
				raise ValueError('start angle out of range')
	
			tilts = cosineSloped(max(abs(self.max),abs(self.min)),self.n)
			# this sorts from negative tilts to positive tilts
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

			# group 0	
			tilt_half = tilts[index:]
			if len(tilt_half) > 2:
				tilt_half = self.addOnTilts(tilt_half)
			else:
				tilt_half = []
				# First group is positive tilts
			self.tilts.append(tilt_half)

			# group 1
			if index < len(tilts) - 1:
				if len(tilt_half) == 0:
					index -= 1 # subtract one so that it does not repeat
				index += 1
			else:
				index += 1
			tilt_half = tilts[:index]
			tilt_half.reverse()
			if len(tilt_half) > 2:
				tilt_half = self.addOnTilts(tilt_half)
			else:
				tilt_half = []
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
			# equal angled
			# The first always move toward positive
			parameters = [
				(self.min, self.max, self.start, abs(self.step)),
				(self.min, self.max, self.start, -abs(self.step)),
			]

			for args in parameters:
				tilts = equallyAngled(*args)
				if len(tilts) < 2:
					# This means only the start angle is in this tilt group
					tilts = []
				tilts = self.addOnTilts(tilts)
				self.tilts.append(tilts)

			if not self.tilts:
				raise ValueError('no angles from parameters specified')

	def updateTiltSequence(self):
		self.tilt_sequence = []
		self.index_sequence = []
		self.target_adjust_indices = []

		# Handle one tilt group: always 'sequential'
		if len(self.tilts) < 2:
			self.tilt_order = 'sequential'
			group_order = (0,)
		else:
			if self.step > 0:
				group_order = (0,1)
			else:
				group_order = (1,0)
		if self.tilt_order == 'sequential':
			self.makeSequentialTiltOrder(group_order)
		elif self.tilt_order == 'alternate':
			# 0,1,-1,-2,2,3,-3,-4 alternate increment. Wim Hagen scheme
			self.makeAlternateTiltOrder(group_order, False)
		elif self.tilt_order == 'swing':
			# 0,1,-1,2,-2,3,-3 always switch direction
			self.makeAlternateTiltOrder(group_order, True)


	def makeSequentialTiltOrder(self, group_order):
		for i in group_order:
			for j in range(len(self.tilts[i])):
				self.index_sequence.append((i,j))
				self.tilt_sequence.append(self.tilts[i][j])
		if len(group_order) > 1:
				# may need target_adjustment
				g_index = group_order[1]
				g = self.tilts[g_index]
				if len(self.tilts[group_order[0]]) > 2 and len(g) > 0:
					self.target_adjust_indices.append(self.index_sequence.index((g_index,0)))

	def makeAlternateTiltOrder(self, group_order, always_switch_direction=False):
			# assuming group[0][0] = group[1][0]
			added_next_one = False
			i = 0
			group = group_order[0]
			while i < len(self.tilts[group]):
				self.index_sequence.append((group,i))
				self.tilt_sequence.append(self.tilts[group][i])
				if i+1 < len(self.tilts[group]):
					if not always_switch_direction:
						self.index_sequence.append((group,i+1))
						self.tilt_sequence.append(self.tilts[group][i+1])
						added_next_one = True
					else:
						# add tilt in the other group at the same index
						other_group = int(not bool(group))
						if i < len(self.tilts[other_group]) and i > 0:
							# no need to acquire another image at start angle.
							self.index_sequence.append((other_group,i))
							self.tilt_sequence.append(self.tilts[other_group][i])
				else:
					added_next_one = False
				if not always_switch_direction:
					group = int(not bool(group))
				i += 1
			if added_next_one:
				i += 1
			for g in group_order:
				# all the left over tilts
				if i < len(self.tilts[g]):
					for j in range(i,len(self.tilts[g])):
						self.index_sequence.append((g,j))
						self.tilt_sequence.append(self.tilts[g][j])

if __name__ == '__main__':
	kwargs = {
		'equally_sloped': False,
		'min': math.radians(-60),
		'max': math.radians(40),
		'start': math.radians(0),
		'step': math.radians(5),
		'n': 10,
		'add_on': [],
		'tilt_order': 'alternate',
	}
	tilts = Tilts(**kwargs)
	for ts in tilts.getTilts():
		print 'getTilts', map((lambda x: math.degrees(x)), ts)

	print tilts.index_sequence
	print ' '
	for t in tilts.getTiltSequence():
		print '%.1f' % math.degrees(t)
	print tilts.getTargetAdjustIndices()

