'''
usage:
myfft = pyami.fft.calculator.forward(myimage)
'''
from main import calculator

# for convenience, make pyami.fft have methods of calculator
this_dict = globals()
for name in dir(calculator):
	if not name.startswith('_'):
		this_dict[name] = getattr(calculator, name)
