from redux.pipe import Pipe
import pyami.fft

# Two threads doing power at the same time may be causing trouble.
# Make a thread lock to prevent this.
import threading
import sys
powerlock = threading.Lock()
sys.stderr.write('**power thread lock in effect')

pyami.fft.calculator.stashing_on = False

class Power(Pipe):
	switch_arg = 'power'
	def run(self, input):
		# lock power calculation to one thread at a time
		powerlock.acquire()
		try:
			output = pyami.fft.calculator.power(input, full=True, centered=True)
		finally:
			powerlock.release()
		return output

