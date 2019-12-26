import pickle
from time import sleep
from random import random,randint
from threading import Thread
from Events import event_types
from Logger import Logger, singleton
from BluetoothController import BTCtl

def generateID(check):
	stack = set()
	while True:
		name = "%06d" % randint(0,999999)
		if not check(name) and name not in stack:
			continue
		stack.add(name)
		yield name

		for x in stack:
			if not check(name):
				stack.remove(x)

class Device:
	def __init__(self, mac, pin="0000"):
		self.mac = mac
		self.pin = pin
		self.history = []
		self.sock = None
		self.busy = False

	def __del__(self):
		self.close()

	def __getitem__(self, key):
		return self.__dict__[key]

	def __setitem__(self, key, value):
		self.__dict__[key] = value

	def __str__(self):
		return "Device %s" % self.mac

	def close(self):
		if self.busy is True:
			self.sock = None
			self.busy = False
			sleep(1)

	def connect(self):
		while self.busy is True:
			sleep(1)
		self.busy = True
		self.sock = 1

	def recv(self):
		return "Light:%.2f|Water:%.2f|Temp:%.2f|Hum:%.2f" % tuple(random() * 100 for _ in range(4))

	def send(self, msg):
		return 20

	def setup(self):
		return True

class TrueDevice:
	def __init__(self, mac, pin="0000"):
		self.mac = mac
		self.pin = pin
		self.history = []
		self.sock = None
		self.busy = False

	def __del__(self):
		self.close()

	def __getitem__(self, key):
		return self.__dict__[key]

	def __setitem__(self, key, value):
		self.__dict__[key] = value

	def __str__(self):
		return "Device %s" % self.mac

	def close(self):
		if self.busy is True:
			if self.sock is not None:
				self.sock.close()
			self.sock = None
			self.busy = False
			sleep(1)

	def connect(self):
		while self.busy is True:
			sleep(1)
		self.busy = True
		self.sock = BTCtl().connect(self.mac)

		if self.sock is None:
			self.close()

	def recv(self):
		if self.sock is None:
			return None

		data = bytes()
		while 10 not in data: # "\n" in data
			try:
				rcv = self.sock.recv(128)
				data += rcv
			except Exception as ex:
				Logger().write("[!] Failed to recieve from %s" % str(self), tag="DEVICE")
				Logger().write(ex, tag="EXCEPT")
				self.close()
				return None

		out = data.decode().strip()
		Logger().write("[>] Recieved '%s' from %s" % (out, str(self)), tag="DEVICE")
		return out

	def send(self, msg):
		if self.sock is None:
			return -1

		if isinstance(msg, bytes):
			data = msg
		else:
			cmd = msg.strip()
			Logger().write("[<] Sending '%s' to %s" % (cmd, str(self)), tag="DEVICE")
			data = (cmd + "\n").encode()

		try:
			ret = self.sock.send(data)
			sleep(1) # sleep for proper hc06 reading
			return ret
		except Exception as ex:
			Logger().write("[!] %s has disconnected" % str(self), tag="DEVICE")
			Logger().write(ex, tag="EXCEPT")
			return -1

	def setup(self):
		ret = BTCtl().pair(self.mac, self.pin)
		if ret is False:
			return False

		self.connect()
		pin = "%04d" % randint(0,9999)
		ret = self.send("setup%s%d" % (pin, 0))
		self.close()
		self.busy = True
		BTCtl().remove(self.mac)

		if ret == -1:
			self.close()
			return False

		self.pin = pin
		ret = BTCtl().pair(self.mac, self.pin)
		self.close()

		return ret

@singleton
class Hub(Thread):
	def __init__(self, *args, **kwargs):
		super().__init__(target=self.loop)
		self.fname = "settings.pcl"
		self.devices = {}
		self.events = {}

		self.genDeviceKey = generateID(lambda name: name not in self.devices)
		self.genEventsKey = generateID(lambda name: name not in self.events)
		self.load(self.fname)

	def addDevice(self, mac, pin="0000"):
		key = next(self.genDeviceKey)
		dev = Device(mac, pin)
		self.devices[key] = dev
		self.save()

		Logger().write("[+] Added %s with ID '%s'" % (str(dev), key), tag="HUB")
		return key

	def addEvent(self, ev, dev, time, repeat=None):
		key = next(self.genEventsKey)
		obj = event_types[ev]
		ev = obj(self, dev, time, repeat)
		self.events[key] = ev
		self.save()

		Logger().write("[+] Added %s with ID '%s'" % (str(ev), key), tag="HUB")
		return key

	def clear(self):
		self.devices.clear()
		self.events.clear()

	def findDevice(self, key):
		if ":" not in key:
			return self.findObj(self.devices, key)

		mac = key
		devs = list(filter(lambda x: x["mac"] == mac, self.devices.values()))
		return devs[0] if len(devs) == 1 else None

	def findDeviceID(self, mac):
		devs = list(filter(lambda x: x[1]["mac"] == mac, self.devices.items()))
		return devs[0][0] if len(devs) == 1 else None

	def findEvent(self, idx):
		return self.findObj(self.events, idx)

	def findObj(self, arr, idx):
		obj = arr[idx] if idx in arr else None
		return obj

	def load(self, fname):
		self.clear()
		try:
			with open(fname, "rb") as f:
				devices, events = pickle.load(f)
			self.fname = fname
		except Exception as ex:
			Logger().write(ex, tag="EXCEPT")
			devices = {}
			events = {}

		for idx,(mac,pin) in devices.items():
			self.devices[idx] = Device(mac, pin)
		for idx,(ev,did,time,repeat) in events.items():
			obj = event_types[ev]
			dev = self.findDevice(did)
			if dev is not None:
				self.events[idx] = obj(self, dev, time, repeat)

	def loop(self):
		while True:
			for idx,ev in sorted(self.events.items(), key=lambda x: x[1]["time"]):
				ev.exec(idx)
			self.printStack()
			sleep(0.1)

	def printStack(self):
		with open("stack", "w") as f:
			f.write("%s" % "".join([ "%d. %s\n" % (i, str(e)) for i,e in enumerate(self.events.values()) ]))

	def removeDevice(self, idx):
		dev = self.findDevice(idx)
		self.removeObj(self.devices, idx)
		dev.close()
		BTCtl().remove(dev["mac"])

		for idx in tuple(self.events.keys()):
			ev = self.events[idx]
			if ev.dev["mac"] == dev["mac"]:
				self.removeEvent(idx)

		self.save()
		return True

	def removeEvent(self, idx):
		ev = self.findEvent(idx)
		self.removeObj(self.events, idx)
		ev["started"] = True

		self.save()
		return True

	def removeObj(self, arr, idx):
		obj = arr.pop(idx)
		Logger().write("[-] Removed %s" % str(obj), tag="HUB")

	def save(self, fname=None):
		if not fname:
			fname = self.fname

		devices = { key: [ dev["mac"], dev["pin"] ] for key,dev in self.devices.items() }
		events = { key: [ ev.name, self.findDeviceID(ev["dev"]["mac"]), ev["time"], ev["repeat"] ] for key,ev in self.events.items() }
		with open(fname, "wb") as f:
			pickle.dump((devices, events), f)
		self.fname = fname
