import scope

def factory(scopeclass):
	class scopedict(scopeclass):
		keylist = ['screen current', 'beam blank', 'gun tilt', 'gun shift',
								'high tension', 'intensity', 'dark field mode', 'stigmator',
								'spot size', 'beam tilt', 'beam shift', 'image shift',
								'defocus', 'magnification', 'corrected stage position',
								'stage position', 'low dose', 'low dose mode',
								'diffraction mode', 'reset defocus', 'screen position',
								'holder status', 'holder type', 'stage status', 'column valves',
								'vacuum status', 'turbo pump']

		def __init__(self):
			scopeclass.__init__(self)
			self.correctedstage = True

		def exit(self):
			scopeclass.exit(self)
	
		def __repr__(self):
			return repr(self.copy())
		
		def copy(self):
			data = {}
			for key in self.keylist:
				data[key] = self.__getitem__(key)
			return data
	
		def __cmp__(self, dict):
			return cmp(self.copy(), dict)	
		
		def __len__(self):
			return len(self.keylist)

		def __setitem__(self, key, val):
			if key == 'screen current':
				pass
			elif key == 'beam blank':
				self.setBeamBlank(val)
			elif key == 'gun tilt':
				self.setGunTilt(val, 'absolute')
			elif key == 'gun shift':
				self.setGunShift(val, 'absolute')
			elif key == 'high tension':
				self.setHighTension(val)
			elif key == 'intensity':
				self.setIntensity(val, 'absolute')
			elif key == 'dark field mode':
				self.setDarkFieldMode(val)
			elif key == 'stigmator':
				self.setStigmator(val, 'absolute')
			elif key == 'spot size':
				self.setSpotSize(val, 'absolute')
			elif key == 'beam tilt':
				self.setBeamTilt(val, 'absolute')
			elif key == 'beam shift':
				self.setBeamShift(val, 'absolute')
			elif key == 'image shift':
				self.setImageShift(val, 'absolute')
			elif key == 'defocus':
				self.setDefocus(val, 'absolute')
			elif key == 'magnification':
				self.setMagnification(val)
			elif key == 'stage position':
				self.setStagePosition(val, 'absolute')
			elif key == 'corrected stage position':
				self.setCorrectedStagePosition(val)
			elif key == 'low dose':
				self.setLowDose(val)
			elif key == 'low dose mode':
				self.setLowDoseMode(val)
			elif key == 'diffraction mode':
				self.setDiffractionMode(val)
			elif key == 'reset defocus':
				if val == 1:
					self.resetDefocus()
				elif val == 0:
					pass
				else:
					raise ValueError
			elif key == 'screen position':
				self.setScreen(val)
			elif key == 'holder type':
				self.setHolderType(val)
			elif key == 'turbo pump':
				return self.setTurboPump(val)
			elif key == 'column valves':
				self.setColumnValves(val)
			else:
				raise KeyError
			return 0
		
		def __getitem__(self, key):
			if key == 'screen current':
				return self.getScreenCurrent()
			elif key == 'beam blank':
				return self.getBeamBlank()
			elif key == 'gun tilt':
				return self.getGunTilt()
			elif key == 'gun shift':
				return self.getGunShift()
			elif key == 'high tension':
				return self.getHighTension()
			elif key == 'intensity':
				return self.getIntensity()
			elif key == 'dark field mode':
				return self.getDarkFieldMode()
			elif key == 'stigmator':
				return self.getStigmator()
			elif key == 'spot size':
				return self.getSpotSize()
			elif key == 'beam tilt':
				return self.getBeamTilt()
			elif key == 'beam shift':
				return self.getBeamShift()
			elif key == 'image shift':
				return self.getImageShift()
			elif key == 'defocus':
				return self.getDefocus()
			elif key == 'magnification':
				return self.getMagnification()
			elif key == 'stage position':
				return self.getStagePosition()
			elif key == 'corrected stage position':
				return self.getCorrectedStagePosition()
			elif key == 'low dose':
				return self.getLowDose()
			elif key == 'low dose mode':
				return self.getLowDoseMode()
			elif key == 'diffraction mode':
				return self.getDiffractionMode()
			elif key == 'reset defocus':
				return 0
			elif key == 'screen position':
				return self.getScreen()
			elif key == 'holder type':
				return self.getHolderType()
			elif key == 'holder status':
				return self.getHolderStatus()
			elif key == 'stage status':
				return self.getStageStatus()
			elif key == 'turbo pump':
				return self.getTurboPump()
			elif key == 'column valves':
				return self.getColumnValves()
			elif key == 'vacuum status':
				return self.getVacuumStatus()
			else:
				raise KeyError

		def setCorrectedStagePosition(self, value):
			self.correctedstage = value
			return self.correctedstage

		def getCorrectedStagePosition(self):
			return self.correctedstage

		def setStagePosition(self, value, type='absolute'):
			# pre-position x and y (maybe others later)
			if self.correctedstage and ('x' in value or 'y' in value):
				delta = 2e-6
				stagenow = self.getStagePosition()
				# calculate pre-position
				prevalue = {}
				if 'x' in value:
					prevalue['x'] = value['x'] - delta
				else:
					prevalue['x'] = stagenow['x'] - delta
				if 'y' in value:
					prevalue['y'] = value['y'] - delta
				else:
					prevalue['y'] = stagenow['y'] - delta
				scopeclass.setStagePosition(self, prevalue, type)
			return scopeclass.setStagePosition(self, value, type)
	
		def keys(self):
			return list(self.keylist)
	
		def values(self):
			data = self.copy()
			return data.values()
		
		def clear(self):
			return 0
	
		def __delitem__(self, key):
			return 0
	
		def items(self):
			data = self.copy()
			return data.items()
		
		def iteritems(self):
			data = self.copy()
			return data.iteritems()
		
		def iterkeys(self):
			return iter(self.keylist)
		
		def itervalues(self):
			data = self.copy()
			return data.itervalues()
	
		def has_key(self, key):
			return key in self.keys()
		
		def update(self, dict):
			for k, v in dict.items():
				self.__setitem__(k,v)
			return 0
		
		def get(self, key, failobj=None):
			return 0
		
		def setdefault(self, key, failobj=None):
			return 0
		
		def popitem(self):
			return 0
		
		def __contains__(self, key):
			return key in self.keylist
		
		def __iter__(self):
			return self.iterkeys()

	return scopedict
