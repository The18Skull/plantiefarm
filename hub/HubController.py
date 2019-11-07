import pickle, events
from time import sleep
from logger import Logger
from random import randint
from utils import singleton
from threading import Thread
from BluetoothController import BTCtl

class Device:
	def __init__(self, mac, pin="0000", name="SmartPot", idx=0):
		self.mac = mac
		self.pin = pin
		self.name = name
		self.sensors = {
			"light": 0.0,
			"water": 0.0,
			"temp": 0.0,
			"hum": 0.0
		}

		self.pin = "%04d" % randint(0,9999)
		self.connect()
		self.send("setup%s%s" % (self.pin, idx))

	def __del__(self):
		self.close()

	def __str__(self):
		return "Device %s" % self.mac

	def close(self):
		BTCtl().close()

	def connect(self):
		BTCtl().connect(self.mac, self.pin)

	def send(self, msg):
		BTCtl().send(msg)

	def recv(self):
		return BTCtl().recv()

@singleton
class Hub(Thread):
	def __init__(self, *args, **kwargs):
		super().__init__(target=self.loop)

		self.fname = "settings.pcl"
		self.run = self.start

		if len(args) != 0:
			self.load(args[0])
		else:
			self.devices = []
			self.events = []

	def addEvent(self, ev):
		self.events.append(ev)

	def addDevice(self, dev):
		self.devices.append(dev)

	def load(self, fname):
		with open(fname, "rb") as f:
			self.devices, self.events = pickle.load(f)
			self.fname = fname

	def loop(self):
		while True:
			ret = ev.exec()
			if ret is None:
				self.events.pop(0)
			self.events.sort(key=lambda x: x.time)
			sleep(1)

	def reset(self):
		self.devices.clear()
		self.events.clear()

	def save(self, fname=self.fname):
		with open(fname, "wb") as f:
			pickle.dump((self.devices, self.events), f)
