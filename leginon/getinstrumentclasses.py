#!/usr/bin/env python
'''
find classes in leginondata.py that have 'tem' and 'ccdcamera' as fields
'''

import inspect
import leginondata

for attr in leginondata.__dict__.keys():
   ob = getattr(data, attr)
   if inspect.isclass(ob):
     if issubclass(ob, leginondata.Data):
       fields = ob.typemap()
       keys = [field[0] for field in fields]
       if 'tem' in keys and 'ccdcamera' in keys:
         print attr
