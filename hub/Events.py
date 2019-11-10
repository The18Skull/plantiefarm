from Logger import Logger
from threading import Thread
from time import time, sleep
from datetime import datetime as dt

class Event:
	def __init__(self, master, dev, time=0, repeat=None, idx=0):
		self.master = master # link to hub
		self.dev = dev # device
		self.time = int(time) # unix timestamp
		self.repeat = repeat # unix timestamp
		self.started = False # start flag
		self.id = idx # unique id
		self.name = self.__class__.__name__.lower() # event's name

	def __getitem__(self, key):
		return self.__dict__[key]

	def __setitem__(self, key, value):
		self.__dict__[key] = value

	def __str__(self):
		n = self.name.capitalize()
		t = dt.fromtimestamp(self.time)
		d = str(self.dev)
		return "%s event on %s for %s" % (n, t, d)

	def exec(self):
		now = time() # get current unix timestamp
		if now >= self.time and self.started is False:
			Logger().write("[!] %s is starting" % str(self))
			self.started = True
			Thread(target=self.threadFunc).start()
			self.master.removeEvent(self.id)

	def func(self):
		pass

	def threadFunc(self):
		self.dev.connect()
		if self.dev["sock"] is not None:
			self.func()
		self.dev.close()
		Logger().write("[!] %s was finished" % str(self))

		if self.repeat is not None:
			now = time()
			newTime = self.time + int(self.repeat)
			self.time = newTime if newTime > now else now + int(self.repeat)
			self.master.addEvent(self.name, self.dev, self.time, self.repeat)
		self.started = False

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
		sleep(3)
		self.dev.send("set0")
