import camera

def factory(cameraclass):
  class cameradict(cameraclass):
      def __init__(self, dict=None):
          cameraclass.__init__(self)
          self.data = {"x offset" : 0, "y offset": 0,
                       "x dimension" : 512, "y dimension" : 512,
                       "x binning" : 1, "y binning" : 1,
                       "exposure time" : 500,
                       "exposure type" : "illuminated",
                       "datatype code" : "H",
                       "image data" : None}
  
          if dict is not None:
              self.update(dict)
  
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
          setkeys = ["x offset", "y offset", "x dimension", "y dimension",
                     "x binning", "y binning", "exposure time", "exposure type"]
          if key in setkeys:
              self.data[key] = item
              return 0
          else:
              raise ValueError
        
      def __delitem__(self, key):
          return 0
      def clear(self):
          return 0
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
          return 0
      def get(self, key, failobj=None):
          return 0
      def setdefault(self, key, failobj=None):
          return 0
      def popitem(self):
          return 0
      def __contains__(self, key):
          return key in self.data
      def __iter__(self):
          return iter(self.data)
      def refresh(self):
          self.data["image data"] = self.getImage(self.data["x offset"], self.data["y offset"],
                                            self.data["x dimension"], self.data["y dimension"],
                                             self.data["x binning"], self.data["y binning"],
                                             self.data["exposure time"], self.data["exposure type"])
          return 0

  return cameradict
