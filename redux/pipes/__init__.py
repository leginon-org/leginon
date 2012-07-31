# this is pipes/__init__.py

registered = {}
def register(cls):
	global registered
	registered[cls.__name__] = cls

from read import Read
register(Read)
from power import Power
register(Power)
from mask import Mask
register(Mask)
from shape import Shape
register(Shape)
from scale import Scale
register(Scale)
from format import Format
register(Format)
from lpf import LPF
register(LPF)
from sqrt import Sqrt
register(Sqrt)
from pad import Pad
register(Pad)
from histogram import Histogram
register(Histogram)
from simulate import Simulate
register(Simulate)
from leginonread import Leginon
register(Leginon)
