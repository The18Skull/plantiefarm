import pickle
from time import sleep
from random import randint
from threading import Thread
from Events import Refresh, Water
from Logger import Logger, singleton
from BluetoothController import BTCtl

class Device:
	def __init__(self, mac, pin="0000"):
		self.mac = mac
		self.pin = pin
		self.history = { 0: {
			"light": 0.0,
			"water": 0.0,
			"temp": 0.0,
			"hum": 0.0
		} }
		self.sock = None

	def __del__(self):
		self.close()

	def __getitem__(self, key):
		return self.__dict__[key]

	def __setitem__(self, key, value):
		self.__dict__[key] = value

	def __str__(self):
		return "Device %s" % self.mac

	def close(self):
		if self.sock is not None:
			self.sock.close()
			self.sock = None

	def connect(self):
		self.sock = BTCtl().connect(self.mac)

	def send(self, msg):
		if isinstance(msg, bytes):
			data = msg
		else:
			cmd = msg.strip()
			Logger().write("[!] Sending '%s' to %s" % (cmd, str(self)))
			data = (cmd + "\n").encode()

		self.sock.send(data)

	def setup(self):
		BTCtl().pair(self.mac, self.pin)
		self.connect()
		self.pin = "%04d" % randint(0,9999)
		self.send("setup%s%d" % (self.pin, 0))
		self.close()

		BTCtl().remove(self.mac)
		BTCtl().pair(self.mac, self.pin)

	def recv(self):
		data = bytes()
		while 10 not in data: # "\n" in data
			try:
				rcv = self.sock.recv(128)
				data += rcv
			except:
				Logger().write("[!] Failed to recieve from %s" % str(self))
				self.close()
				return None

		out = data.decode().strip()
		Logger().write("[!] Recieved '%s' from %s" % (out, str(self)))
		return out

@singleton
class Hub(Thread):
	def __init__(self, *args, **kwargs):
		super().__init__(target=self.loop)
		self.fname = "settings.pcl"
		self.devices = {}
		self.events = {}

		self.load(self.fname)

	def addDevice(self, mac):
		arr = [ int(x) for x in self.devices.keys() ]
		for i in range(0,10000):
			if i not in arr:
				break

		dev = Device(mac)
		self.devices[i] = dev
		self.save()

		Logger().write("[+] Added %s with ID %d" % (str(dev), i))
		return i

	def addEvent(self, ev, dev, time, repeat=None):
		arr = [ int(x) for x in self.events.keys() ]
		for i in range(0,10000):
			if i not in arr:
				break

		obj = Refresh if ev == "refresh" else Water
		ev = obj(self, dev, time, repeat, idx=i)
		self.events[i] = ev
		self.save()

		Logger().write("[+] Added %s with ID %d" % (str(ev), i))
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
		except Exception:
			devices = {}
			events = {}

		for idx,(mac,pin) in devices.items():
			self.devices[idx] = Device(mac, pin)
		for idx,(ev,did,time,repeat) in events.items():
			obj = Refresh if ev == "refresh" else Water
			dev = self.findDevice(did)
			if dev is not None:
				self.events[idx] = obj(self, dev, time, repeat, idx=idx)

	def loop(self):
		while True:
			events = sorted(self.events.items(), key=lambda x: x[1]["time"])
			if len(events) != 0:
				idx = events[0][0]
				ev = self.events[idx]
				ev.exec()
			self.printStack()
			sleep(0.1)

	def printStack(self):
		with open("stack", "w") as f:
			for i,e in enumerate(self.events.values()):
				f.write("%d. %s\n" % (i, str(e)))

	def removeDevice(self, idx):
		dev = self.findDevice(idx)
		self.removeObj(self.devices, idx)
		dev.close()
		BTCtl().remove(dev["mac"])

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
		Logger().write("[-] Removed %s" % str(obj))

	def save(self, fname=None):
		if fname is None:
			fname = self.fname

		devices = { key: [ dev["mac"], dev["pin"] ] for key,dev in self.devices.items() }
		events = { key: [ ev.name, self.findDeviceID(ev["dev"]["mac"]), ev["time"], ev["repeat"] ] for key,ev in self.events.items() }
		with open(fname, "wb") as f:
			pickle.dump((devices, events), f)
		self.fname = fname

if __name__ == "__main__":
	h = Hub()
	print(1)
