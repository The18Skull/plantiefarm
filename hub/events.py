from time import sleep
from datetime import datetime as dt

class Event:
	def __init__(self, dev, time, repeat=None):
		self.dev = dev # device
		self.time = time # datetime
		self.repeat = repeat # timedelta

	def __str__(self):
		return "%s event on %s" % (self.__class__.__name__, self.time)

	def exec(self):
		now = dt.now()
		if now >= self.time:
			self.dev.connect()
			self.func()
			self.dev.close()
			self.time = now + self.repeat
			return self
		return None

	def func(self):
		pass

class Receive(Event):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def func(self):
		self.dev.send("get")
		out = self.dev.recv()
		res = { key: float(value) for key, value in x.split(":") for x in out.lower().split("|") }
		self.dev.sensors.update(res)

class Water(Event):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def func(self):
		self.dev.send("set90")
		sleep(2)
		self.dev.send("set0")
