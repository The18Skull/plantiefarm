from Logger import Logger
from threading import Thread
from time import time, sleep
from datetime import datetime as dt

class Event:
	def __init__(self, master, dev, time=0, repeat=None):
		self.master = master # link to hub
		self.dev = dev # device
		self.time = int(time) # unix timestamp
		self.repeat = repeat # unix timestamp
		self.started = False # start flag
		self.name = self.__class__.__name__.lower() # event's name

	def __getitem__(self, key):
		return self.__dict__[key]

	def __setitem__(self, key, value):
		self.__dict__[key] = value

	def __str__(self):
		n = self.name.capitalize()
		t = dt.fromtimestamp(self.time).strftime("%H:%M:%S %d/%m/%Y")
		d = str(self.dev)
		return "%s event on %s for %s" % (n, t, d)

	def exec(self, idx):
		now = time() # get current unix timestamp
		if now >= self.time and self.started is False:
			self.started = True
			Logger().write("[!] %s is starting" % str(self), tag="EVENT")
			Thread(target=self.threadFunc, args=(idx,)).start()

	def func(self):
		pass

	def threadFunc(self, idx):
		ret = self.func()

		self.master.removeEvent(idx)
		self.started = False

		now = int(time())
		Logger().write("[!] %s was %s" % (str(self), "finished" if ret is True else "failed"), tag="EVENT")
		if self.master.findDeviceID(self.dev["mac"]) is None:
			return

		if ret is False:
			newTime = now + 10
			self.master.addEvent(self.name, self.dev, newTime)

		if self.repeat is not None:
			newTime = self.time + int(self.repeat)
			self.time = newTime if newTime > now else now + int(self.repeat)
			self.master.addEvent(self.name, self.dev, self.time, self.repeat)

class Setup(Event):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def func(self):
		self.repeat = None
		return self.dev.setup()

class Refresh(Event):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def func(self):
		self.dev.connect()
		ret = self.dev.send("get")
		out = self.dev.recv()
		self.dev.close()

		if ret == -1 or out is None:
			return False

		res = { "time": int(time()) }
		for x in out.lower().split("|"):
			key, value = x.split(":")
			res[key] = float(value)

		self.dev.history.append(res)
		return True

class Water(Event):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def func(self):
		self.dev.connect()
		r1 = self.dev.send("set90")
		sleep(3)
		r2 = self.dev.send("set0")
		self.dev.close()

		if -1 in (r1,r2):
			return False
		return True

event_types = {
	"setup": Setup,
	"refresh": Refresh,
	"water": Water
}
