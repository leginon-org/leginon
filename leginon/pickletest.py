#!/usr/bin/env python
import strictdict
import Numeric
import cPickle

t = strictdict.TypedDict(type_map_or_seq={'image':Numeric.ArrayType})
print 't', t

p = cPickle.dumps(t)

