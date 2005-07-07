import threading

def Player(*args, **kwargs):
	return _Player(*args, **kwargs)

class _Player(threading._Verbose):
	def __init__(self, callback=None, verbose=None):
		threading._Verbose.__init__(self, verbose)
		self.__cond = threading.Condition(threading.RLock())
		self.__flag = 'play'
		self.__callback = callback

	def state(self):
		return self.__flag

	def play(self):
		self.__cond.acquire()
		try:
			self.__flag = 'play'
			self.__cond.notifyAll()
			if callable(self.__callback):
				self.__callback(self.__flag)
		finally:
			self.__cond.release()

	def pause(self):
		self.__cond.acquire()
		try:
			self.__flag = 'pause'
			if callable(self.__callback):
				self.__callback(self.__flag)
		finally:
			self.__cond.release()

	def stop(self):
		self.__cond.acquire()
		try:
			self.__flag = 'stop'
			self.__cond.notifyAll()
			if callable(self.__callback):
				self.__callback(self.__flag)
		finally:
			self.__cond.release()

	def stopqueue(self):
		self.__cond.acquire()
		try:
			self.__flag = 'stopqueue'
			self.__cond.notifyAll()
			if callable(self.__callback):
				self.__callback(self.__flag)
		finally:
			self.__cond.release()

	def wait(self, timeout=None):
		self.__cond.acquire()
		try:
			if self.__flag == 'pause':
				self.__cond.wait(timeout)
			state = self.__flag
		finally:
			self.__cond.release()
		return state

if __name__ == '__main__':
	import time

	player = Player()

	def _player():
		while True:
			command = player.wait(0.0)
			print command
			if command == 'stop':
				break
			time.sleep(1.0)

	threading.Thread(target=_player).start()

	while True:
		command = raw_input()
		if hasattr(player, command):
			attr = getattr(player, command)
			if callable(attr):
				attr()
			else:
				print attr

