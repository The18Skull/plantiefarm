import pickle
from time import sleep
from random import randint
from threading import Thread
from Events import event_types
from Logger import Logger, singleton
from BluetoothController import BTCtl

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

		self.load(self.fname)

	def addDevice(self, mac, pin="0000"):
		arr = [ int(x) for x in self.devices.keys() ]
		for i in range(0,10000):
			if i not in arr:
				break

		dev = Device(mac, pin)
		self.devices[i] = dev
		self.save()

		Logger().write("[+] Added %s with ID %d" % (str(dev), i), tag="HUB")
		return i

	def addEvent(self, ev, dev, time, repeat=None):
		arr = [ int(x) for x in self.events.keys() ]
		for i in range(0,10000):
			if i not in arr:
				break

		obj = event_types[ev]
		ev = obj(self, dev, time, repeat)
		self.events[i] = ev
		self.save()

		Logger().write("[+] Added %s with ID %d" % (str(ev), i), tag="HUB")
		return i

	def clear(self):
		self.devices.clear()
		self.events.clear()

	def findDevice(self, idx):
		if not isinstance(idx, str):
			return self.findObj(self.devices, idx)

		mac = idx
		devs = list(filter(lambda x: x["mac"] == mac, self.devices.values()))
		dev = devs[0] if len(devs) == 1 else None
		return dev

	def findDeviceID(self, mac):
		devs = list(filter(lambda x: x[1]["mac"] == mac, self.devices.items()))
		idx = devs[0][0] if len(devs) == 1 else None
		return idx

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
				self.events[idx] = obj(self, dev, time, repeat, idx=idx)

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
		if fname is None:
			fname = self.fname

		devices = { key: [ dev["mac"], dev["pin"] ] for key,dev in self.devices.items() }
		events = { key: [ ev.name, self.findDeviceID(ev["dev"]["mac"]), ev["time"], ev["repeat"] ] for key,ev in self.events.items() }
		with open(fname, "wb") as f:
			pickle.dump((devices, events), f)
		self.fname = fname
