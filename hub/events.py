from Logger import Logger
from threading import Thread
from time import time, sleep
from datetime import datetime as dt

class Event:
	def __init__(self, dev, time=0, repeat=None):
		self.dev = dev # device
		self.time = int(time) # unix timestamp
		self.repeat = repeat # unix timestamp
		self.started = False

	def __getitem__(self, key):
		return self.__dict__[key]

	def __str__(self):
		n = self.__class__.__name__
		t = dt.fromtimestamp(self.time)
		d = str(self.dev)
		return "%s event on %s for %s" % (n, t, d)

	def exec(self):
		now = time() # get current unix timestamp
		if now >= self.time and self.started is False:
			Logger().write("[!] %s is starting" % str(self))
			self.started = True

			Thread(target=self.threadFunc).start()

			if self.repeat is not None:
				self.time += int(self.repeat)

			return self

	def func(self):
		pass

	def threadFunc(self):
		self.dev.connect()
		self.func()
		self.dev.close()
		self.started = False
		Logger().write("[!] %s was finished" % str(self))

class Refresh(Event):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def func(self):
		self.dev.send("get")
		out = self.dev.recv()

		res = {}
		for x in out.lower().split("|"):
			key, value = x.split(":")
			res[key] = float(value)
	
		self.dev.sensors.update(res)

class Water(Event):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def func(self):
		self.dev.send("set90")
		sleep(2)
		self.dev.send("set0")
