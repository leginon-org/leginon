import threading
import wx

import leginon.gui.wx.Acquisition
import leginon.gui.wx.Camera
import leginon.gui.wx.Settings
import leginon.gui.wx.ToolBar
from leginon.gui.wx.Entry import Entry, FloatEntry, IntEntry
from leginon.gui.wx.Presets import EditPresetOrder
import leginon.gui.wx.tomography.TomographyViewer as TomoViewer

class ImagePanel(object):
	def __init__(self, viewer):
		self.viewer = viewer

	def setImage(self, image):
		pass

	def setTargets(self, type_name, targets):
		#if type_name == 'Peak':
		#	self.viewer.setXCShift(targets[0], center=False)
		pass

	def setImageType(self, type_name, image):
		#if type_name == 'Image':
		#	self.viewer.addImage(image)
		#elif type_name == 'Correlation':
		#	self.viewer.setXC(image)
		pass

class SettingsDialog(leginon.gui.wx.Acquisition.SettingsDialog):
	def initialize(self):
		scrolling = not self.show_basic
		return ScrolledSettings(self,self.scrsize,scrolling,self.show_basic)

class ScrolledSettings(leginon.gui.wx.Acquisition.ScrolledSettings):
	def initialize(self):
		szs = leginon.gui.wx.Acquisition.ScrolledSettings.initialize(self)
		if self.show_basic:
			sz = self.addTomoBasicSettings()
		else:
			sz = self.addTomoSettings()
		return szs + [sz]

	def addTomoBasicSettings(self):
		tiltsb = wx.StaticBox(self, -1, 'Tilt')
		tiltsbsz = wx.StaticBoxSizer(tiltsb, wx.VERTICAL)
		expsb = wx.StaticBox(self, -1, 'Exposure')
		expsbsz = wx.StaticBoxSizer(expsb, wx.VERTICAL)
		miscsb = wx.StaticBox(self, -1, 'Misc.')
		miscsbsz = wx.StaticBoxSizer(miscsb, wx.VERTICAL)
		# tiltsbsz
		self.widgets['tilt min'] = FloatEntry(self, -1,
											   allownone=False,
											   chars=7,
											   value='0.0')
		self.widgets['tilt max'] = FloatEntry(self, -1,
											   allownone=False,
											   chars=7,
											   value='0.0')
		self.widgets['tilt start'] = FloatEntry(self, -1,
												 allownone=False,
												 chars=7,
												 value='0.0')
		self.widgets['tilt step'] = FloatEntry(self, -1,
												allownone=False,
												chars=7,
												value='0.0')

		tiltsz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Min.')
		tiltsz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 10)
		tiltsz.Add(self.widgets['tilt min'], (0, 1), (1, 1),
					wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'Max.')
		tiltsz.Add(label, (0, 2), (1, 1), wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 10)
		tiltsz.Add(self.widgets['tilt max'], (0, 3), (1, 1),
					wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'Start')
		tiltsz.Add(label, (0, 4), (1, 1), wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 10)
		tiltsz.Add(self.widgets['tilt start'], (0, 5), (1, 1),
					wx.ALIGN_LEFT|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'Step')
		tiltsz.Add(label, (0, 6), (1, 1), wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 10)
		tiltsz.Add(self.widgets['tilt step'], (0, 7), (1, 1),
					wx.ALIGN_LEFT|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'degree(s)')
		tiltsz.Add(label, (0, 8), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		tiltsbsz.Add(tiltsz, 0, wx.EXPAND|wx.ALL, 5)
		#expsz
		self.widgets['dose'] = FloatEntry(self, -1, min=0.0,
													allownone=False,
													chars=7,
													value='200.0')
		expsz = wx.GridBagSizer(5, 10)
		label = wx.StaticText(self, -1, 'Total dose')
		expsz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		expsz.Add(self.widgets['dose'], (0, 1), (1, 1),
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'e-/A^2')
		expsz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)

		expsz.AddGrowableCol(0)
		expsz.AddGrowableRow(0)
		expsz.AddGrowableRow(1)
		expsbsz.Add(expsz, 1, wx.EXPAND|wx.ALL, 5)
		#misc
		self.widgets['integer'] = wx.CheckBox(self, -1, 'Scale by')
		self.widgets['intscale'] = FloatEntry(self, -1, min=0.0,
															allownone=False,
															chars=5,
															value='10.0')
		self.widgets['mean threshold'] = FloatEntry(self, -1, min=0.0,
															allownone=False,
															chars=5,
															value='100.0')
		intsz = wx.GridBagSizer(5, 5)
		intsz.Add(self.widgets['integer'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		intsz.Add(self.widgets['intscale'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'to convert to integer')
		intsz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		mtsz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Consider images with less than')
		mtsz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		mtsz.Add(self.widgets['mean threshold'],
				   (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'counts as obstructed')
		mtsz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		miscsz = wx.GridBagSizer(5, 10)
		miscsz.Add(intsz, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		miscsz.Add(mtsz, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		miscsbsz.Add(miscsz, 1, wx.ALL|wx.ALIGN_CENTER, 5)

		# overall
		sz = wx.GridBagSizer(5, 5)
		sz.Add(tiltsbsz, (0, 0), (1, 2), wx.EXPAND)
		sz.Add(expsbsz, (1, 0), (1, 1), wx.EXPAND)
		sz.Add(miscsbsz, (1, 1), (1, 1), wx.EXPAND)
		sz.AddGrowableRow(0)
		sz.AddGrowableRow(1)
		sz.AddGrowableCol(0)
		sz.AddGrowableCol(1)
		return sz

	def addTomoSettings(self):
		tiltsb = wx.StaticBox(self, -1, 'Tilt')
		tiltsbsz = wx.StaticBoxSizer(tiltsb, wx.VERTICAL)
		equalslopesb = wx.StaticBox(self, -1, 'Cosine Rule Tilting')
		equalslopesbsz = wx.StaticBoxSizer(equalslopesb, wx.VERTICAL)
		expsb = wx.StaticBox(self, -1, 'Exposure')
		expsbsz = wx.StaticBoxSizer(expsb, wx.VERTICAL)
		bcsb = wx.StaticBox(self, -1, 'Before Collection')
		bcsbsz = wx.StaticBoxSizer(bcsb, wx.VERTICAL)
		miscsb = wx.StaticBox(self, -1, 'Misc.')
		miscsbsz = wx.StaticBoxSizer(miscsb, wx.VERTICAL)
		modelb = wx.StaticBox(self, -1, 'Model')
		modelbsz = wx.StaticBoxSizer(modelb, wx.VERTICAL)
		optb = wx.StaticBox(self, -1, 'Custom Tilt Axis Model in +/- Directions(d)')
		optbsz = wx.StaticBoxSizer(optb, wx.VERTICAL)

		self.widgets['tilt min'] = FloatEntry(self, -1,
											   allownone=False,
											   chars=7,
											   value='0.0')
		self.widgets['tilt max'] = FloatEntry(self, -1,
											   allownone=False,
											   chars=7,
											   value='0.0')
		self.widgets['tilt start'] = FloatEntry(self, -1,
												 allownone=False,
												 chars=7,
												 value='0.0')
		self.widgets['tilt step'] = FloatEntry(self, -1,
												allownone=False,
												chars=7,
												value='0.0')
		self.widgets['equally sloped'] = wx.CheckBox(self, -1, 'Use cosine rule')
		self.widgets['equally sloped n'] = IntEntry(self, -1, min=1, allownone=False, chars=5, value='30')

		tiltsz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Min.')
		tiltsz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 10)
		tiltsz.Add(self.widgets['tilt min'], (0, 1), (1, 1),
					wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'Max.')
		tiltsz.Add(label, (0, 2), (1, 1), wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 10)
		tiltsz.Add(self.widgets['tilt max'], (0, 3), (1, 1),
					wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'Start')
		tiltsz.Add(label, (0, 4), (1, 1), wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 10)
		tiltsz.Add(self.widgets['tilt start'], (0, 5), (1, 1),
					wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'Step')
		tiltsz.Add(label, (0, 6), (1, 1), wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL|wx.LEFT, 10)
		tiltsz.Add(self.widgets['tilt step'], (0, 7), (1, 1),
					wx.ALIGN_LEFT|wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'degree(s)')
		tiltsz.Add(label, (0, 8), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		equalslopesz = wx.GridBagSizer(5, 5)
		equalslopesz.Add(self.widgets['equally sloped'], (0, 0), (1, 2),
					wx.ALIGN_LEFT|wx.FIXED_MINSIZE)
		equalslopesz.Add(self.widgets['equally sloped n'], (1, 0), (1, 1),
					wx.ALIGN_LEFT|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'Number of tilts in the maximal tilting direction')
		equalslopesz.Add(label, (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		equalslopesbsz.Add(equalslopesz, 0, wx.EXPAND|wx.ALL, 5)
		tiltsz.Add(equalslopesbsz, (0, 9), (1, 2), wx.EXPAND|wx.ALL, 5)
		tiltsbsz.Add(tiltsz, 0, wx.EXPAND|wx.ALL, 5)

		self.widgets['dose'] = FloatEntry(self, -1, min=0.0,
													allownone=False,
													chars=7,
													value='200.0')
		self.widgets['min exposure'] = FloatEntry(self, -1, min=0.0,
															allownone=False,
															chars=5,
															value='0.25')
		self.widgets['max exposure'] = FloatEntry(self, -1, min=0.0,
															allownone=False,
															chars=5,
															value='2.0')

		expsz = wx.GridBagSizer(5, 10)
		label = wx.StaticText(self, -1, 'Total dose')
		expsz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		expsz.Add(self.widgets['dose'], (0, 1), (1, 1),
					wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'e-/A^2')
		expsz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'Exposure time')
		expsz.Add(label, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		exptsz = wx.GridBagSizer(0,0)
		label = wx.StaticText(self, -1, 'Min.')
		exptsz.Add(label, (0, 0), (1, 1), wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		exptsz.Add(self.widgets['min exposure'], (0, 1), (1, 1),
					wx.ALIGN_LEFT|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'Max.')
		exptsz.Add(label, (0, 2), (1, 1), wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL)
		exptsz.Add(self.widgets['max exposure'], (0, 3), (1, 1),
					wx.ALIGN_LEFT|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'seconds')
		exptsz.Add(label, (0, 4), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		expsz.Add(exptsz, (1, 1), (1, 2), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)

		expsz.AddGrowableCol(0)
		expsz.AddGrowableRow(0)
		expsz.AddGrowableRow(1)

		expsbsz.Add(expsz, 1, wx.EXPAND|wx.ALL, 5)

		self.widgets['run buffer cycle'] = wx.CheckBox(self, -1, 'Run buffer cycle')
		self.widgets['align zero loss peak'] = wx.CheckBox(self, -1, 'Align zero loss peak')
		self.widgets['measure dose'] = wx.CheckBox(self, -1, 'Measure dose')

		bcsz = wx.GridBagSizer(5, 10)
		bcsz.Add(self.widgets['run buffer cycle'],
				   (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		bcsz.Add(self.widgets['align zero loss peak'],
				   (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		bcsz.Add(self.widgets['measure dose'],
				   (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		bcsbsz.Add(bcsz, 1, wx.ALL|wx.ALIGN_CENTER, 5)

		self.widgets['integer'] = wx.CheckBox(self, -1, 'Scale by')
		self.widgets['intscale'] = FloatEntry(self, -1, min=0.0,
															allownone=False,
															chars=5,
															value='10.0')
		self.widgets['mean threshold'] = FloatEntry(self, -1, min=0.0,
															allownone=False,
															chars=5,
															value='100.0')
		self.widgets['collection threshold'] = FloatEntry(self, -1, min=0.0,
															allownone=False,
															chars=5,
															value='90.0')
		self.widgets['tilt pause time'] = FloatEntry(self, -1, min=0.0,
															allownone=False,
															chars=5,
															value='1.0')
#		self.widgets['measure defocus'] = wx.CheckBox(self, -1, 'Measure defocus')
		self.widgets['use lpf'] = wx.CheckBox(self, -1, 'Use lpf in peak finding of tilt image correlation')
		self.widgets['use tilt'] = wx.CheckBox(self, -1, 'Stretch images according to the tilt before correlation')

#		tapersz = wx.GridBagSizer(5,5)
#		lab = wx.StaticText(self, -1, 'edge tapered upto')
#		tapersz.Add(lab, (0,0), (1,1))
#		tapersz.Add(self.widgets['taper size'], (0,1), (1,1))
#		lab = wx.StaticText(self, -1, '% image length')
#		tapersz.Add(lab, (0,2), (1,1))

		intsz = wx.GridBagSizer(5, 5)
		intsz.Add(self.widgets['integer'], (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		intsz.Add(self.widgets['intscale'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, 'to convert to integer')
		intsz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		mtsz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Consider images with less than')
		mtsz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		mtsz.Add(self.widgets['mean threshold'],
				   (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'counts as obstructed')
		mtsz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		ctsz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Abort if first half collected less than')
		ctsz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		ctsz.Add(self.widgets['collection threshold'],
				   (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, '% of images')
		ctsz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		tptsz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Pause')
		tptsz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		tptsz.Add(self.widgets['tilt pause time'],
				   (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'seconds before each tilt image.')
		tptsz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		miscsz = wx.GridBagSizer(5, 10)
		miscsz.Add(intsz, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		miscsz.Add(mtsz, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		miscsz.Add(ctsz, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		miscsz.Add(tptsz, (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		miscsz.Add(self.widgets['use lpf'], (4, 0), (1, 1), wx.ALIGN_CENTER)
		miscsz.Add(self.widgets['use tilt'], (5, 0), (1, 1), wx.ALIGN_CENTER)
		#miscsz.Add(tapersz, (7, 0), (1, 1), wx.ALIGN_CENTER)
		#miscsz.Add(self.widgets['measure defocus'], (5, 0), (1, 1), wx.ALIGN_CENTER)
		miscsbsz.Add(miscsz, 1, wx.ALL|wx.ALIGN_CENTER, 5)

		modelmags = self.getMagChoices()
		self.widgets['model mag'] = wx.Choice(self, -1, choices=modelmags)
		self.widgets['phi'] = FloatEntry(self, -1, allownone=False,
			chars=4, value='0.0')
		self.widgets['phi2'] = FloatEntry(self, -1, allownone=False,
			chars=4, value='0.0')
		self.widgets['offset'] = FloatEntry(self, -1, allownone=False,
			chars=6, value='0.0')
		self.widgets['offset2'] = FloatEntry(self, -1, allownone=False,
			chars=6, value='0.0')
		self.widgets['z0'] = FloatEntry(self, -1, allownone=False,
			chars=6, value='0.0')
		self.widgets['z0 error'] = FloatEntry(self, -1, min=0.0,
			allownone=False, chars=6, value='2e-6')
		self.widgets['fixed model'] = wx.CheckBox(self, -1, 'Keep the tilt axis parameters fixed')
		self.widgets['use z0'] = wx.CheckBox(self, -1, 'Initialize z0 with current model')
		self.widgets['fit data points'] = IntEntry(self, -1, min=4, allownone=False, chars=5, value='4')

		magsz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Initialize with the model of')
		magsz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		magsz.Add(self.widgets['model mag'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		phisz = wx.GridBagSizer(2, 2)
		phisz.AddGrowableCol(0)
		label = wx.StaticText(self, -1, 'Tilt Axis from Y')
		phisz.Add(label, (0, 0), (2, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, '+d')
		phisz.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		phisz.Add(self.widgets['phi'],
				   (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, '-d')
		phisz.Add(label, (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		phisz.Add(self.widgets['phi2'],
				   (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'degs')
		phisz.Add(label, (0, 3), (2, 1), wx.ALIGN_CENTER_VERTICAL)

		offsetsz = wx.GridBagSizer(2, 2)
		label = wx.StaticText(self, -1, 'Offset:')
		offsetsz.Add(label, (0, 0), (2, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, '+d')
		offsetsz.Add(label, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		offsetsz.Add(self.widgets['offset'],
				   (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'um')
		offsetsz.Add(label, (0, 3), (2, 1), wx.ALIGN_CENTER_VERTICAL)
		label = wx.StaticText(self, -1, '-d')
		offsetsz.Add(label, (1, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
		offsetsz.Add(self.widgets['offset2'],
				   (1, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		z0sz = wx.GridBagSizer(2, 2)
		label = wx.StaticText(self, -1, 'Z0:')
		z0sz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		z0sz.Add(self.widgets['z0'],
				   (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'um')
		z0sz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		
		optsz = wx.GridBagSizer(5, 10)
		optsz.Add(phisz, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		optsz.Add(offsetsz, (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		optsz.Add(z0sz, (1, 0), (1, 2), wx.ALIGN_CENTER_VERTICAL)
		optbsz.Add(optsz, 1, wx.ALL|wx.ALIGN_CENTER, 5)
		optsz.AddGrowableCol(0)
		
		zsz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Allow' )
		zsz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		zsz.Add(self.widgets['z0 error'],
				   (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'um of z0 jump between models' )
		zsz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		fsz = wx.GridBagSizer(5, 5)
		label = wx.StaticText(self, -1, 'Smooth' )
		fsz.Add(label, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		fsz.Add(self.widgets['fit data points'], (0, 1), (1, 1), wx.ALIGN_CENTER_VERTICAL|wx.FIXED_MINSIZE)
		label = wx.StaticText(self, -1, 'tilts (>=4) for defocus prediction' )
		fsz.Add(label, (0, 2), (1, 1), wx.ALIGN_CENTER_VERTICAL)

		modelsz = wx.GridBagSizer(5, 5)
		modelsz.Add(magsz, (0, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		modelsz.Add(optbsz, (1, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		modelsz.Add(zsz, (2, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		modelsz.Add(self.widgets['fixed model'], (3, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		modelsz.Add(self.widgets['use z0'], (4, 0), (1, 1), wx.ALIGN_CENTER_VERTICAL)
		modelsz.Add(fsz, (5, 0), (1, 1), wx.ALIGN_RIGHT)

		modelbsz.Add(modelsz, 1, wx.ALL|wx.ALIGN_CENTER, 5)
		modelsz.AddGrowableCol(0)

		sz = wx.GridBagSizer(5, 5)
		sz.Add(tiltsbsz, (0, 0), (1, 2), wx.EXPAND)
		sz.Add(expsbsz, (1, 0), (1, 1), wx.EXPAND)
		sz.Add(bcsbsz, (1, 1), (1, 1), wx.EXPAND)
		sz.Add(miscsbsz, (2, 0), (1, 1), wx.EXPAND)
		sz.Add(modelbsz, (2, 1), (1, 1), wx.EXPAND)
		sz.AddGrowableRow(0)
		sz.AddGrowableRow(1)
		sz.AddGrowableRow(2)
		sz.AddGrowableCol(0)
		sz.AddGrowableCol(1)

		self.Bind(wx.EVT_CHECKBOX, self.onFixedModel, self.widgets['fixed model'])
		return sz

	def onFixedModel(self, evt):
		state = evt.IsChecked()
		self.widgets['fit data points'].Enable(state)

	def getMagChoices(self):
			choices = ['this preset and lower mags', 'only this preset','custom values']
			try:
					mags = self.node.instrument.tem.Magnifications
			except:
				mags = []
			choices.extend( [str(int(m)) for m in mags])
			return choices

class Panel(leginon.gui.wx.Acquisition.Panel):
	settingsdialogclass = SettingsDialog
	def __init__(self, *args, **kwargs):
		leginon.gui.wx.Acquisition.Panel.__init__(self, *args, **kwargs)
		self.toolbar.EnableTool(leginon.gui.wx.ToolBar.ID_BROWSE_IMAGES, False)
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_CHECK_DOSE,
							 'dose',
							 shortHelpString='Check dose')
		self.toolbar.AddTool(leginon.gui.wx.ToolBar.ID_REFRESH,
							 'refresh', shortHelpString='Reset Learning')

		self.toolbar.Bind(wx.EVT_TOOL, self.onResetTiltSeriesList,
											id=leginon.gui.wx.ToolBar.ID_REFRESH)

		self.imagepanel = ImagePanel(self.viewer)

	def addImagePanel(self):
		self.viewer = TomoViewer.Viewer(self, -1)
		self.szmain.Add(self.viewer, (1, 0), (1, 1), wx.EXPAND)

	def onNodeInitialized(self):
		leginon.gui.wx.Acquisition.Panel.onNodeInitialized(self)
		self.toolbar.Bind(wx.EVT_TOOL,
						  self.onCheckDose,
						  id=leginon.gui.wx.ToolBar.ID_CHECK_DOSE)

	def onCheckDose(self, evt):
		threading.Thread(target=self.node.checkDose).start()

	def onResetTiltSeriesList(self, evt):
		self.node.resetTiltSeriesList()

