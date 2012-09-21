# this is the standard pipeline currently used by default
pipes = (
	('sim', 'Simulate'),
	('read', 'Read'),
	('scale1', 'Scale'),
	('pad', 'Pad'),
	('shape1', 'Shape'),
	('power', 'Power'),
	('mask', 'Mask'),
	('shape2', 'Shape'),
	('sqrt', 'Sqrt'),
	('lpf', 'LPF'),
	('scale2', 'Scale'),
	('histogram', 'Histogram'),
	('format', 'Format'),
)
