import camera

def factory(cameraclass):
	class cameradict(cameraclass):
		def __init__(self, dict=None):
			cameraclass.__init__(self)
			self.data = {"offset": {'x': 0, 'y': 0}, \
										"dimension": {'x': 512, 'y': 512}, \
										"binning": {'x': 1, 'y': 1}, \
										"exposure time" : 500, \
										"image data" : None}
			if dict is not None:
				self.update(dict)

		def exit(self):
			cameraclass.exit(self)

		def __repr__(self):
			self.refresh()
			return repr(self.data)

		def __cmp__(self, dict):
			self.refresh()
			if isinstance(dict, cameradict):
				return cmp(self.data, dict.data)
			else:
				return cmp(self.data, dict)

		def __len__(self):
			return len(self.data)

		def __getitem__(self, key):
			if key == "image data":
				self.refresh()
			return self.data[key]
	  
		def __setitem__(self, key, item):
			setkeys = ["offset", "dimension", "binning", "exposure time"]
			if key in setkeys:
				self.data[key] = item
			else:
				raise ValueError
		
		def __delitem__(self, key):
			pass

		def clear(self):
			pass

		def copy(self):
			return self.data.copy()

		def keys(self):
			return self.data.keys()

		def items(self):
			self.refresh()
			return self.data.items()

		def iteritems(self):
			self.refresh()
			return self.data.iteritems()

		def iterkeys(self):
			return self.data.iterkeys()

		def itervalues(self):
			self.refresh()
			return self.data.itervalues()

		def values(self):
			self.refresh()
			return self.data.values()

		def has_key(self, key):
			return self.data.has_key(key)

		def update(self, dict):
			if isinstance(dict, cameradict):
				self.data.update(dict.data)
			else:
				for k, v in dict.items():
					self[k] = v

		def get(self, key, failobj=None):
			pass

		def setdefault(self, key, failobj=None):
			pass
			
		def popitem(self):
			pass

		def __contains__(self, key):
			return key in self.data

		def __iter__(self):
			return iter(self.data)

		def refresh(self):
			self.data["image data"] = self.getImage(self.data["offset"], \
																							self.data["dimension"], \
																							self.data["binning"], \
																							self.data["exposure time"])

	return cameradict

