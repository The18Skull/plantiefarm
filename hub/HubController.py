import pickle
from time import sleep
from random import randint
from threading import Thread
from Logger import Logger, singleton
from BluetoothController import BTCtl

class Device:
	def __init__(self, mac, pin="0000", idx=0):
		self.id = idx
		self.mac = mac
		self.pin = pin
		self.sensors = {
			"light": 0.0,
			"water": 0.0,
			"temp": 0.0,
			"hum": 0.0
		}
		self.sock = None

		BTCtl().pair(self.mac, self.pin)
		self.connect()
		self.pin = "%04d" % randint(0,9999)
		self.send("setup%s%d" % (self.pin, self.id))
		self.close()

		BTCtl().remove(self.mac)
		BTCtl().pair(self.mac, self.pin)

	def __del__(self):
		self.close()

	def __getitem__(self, key):
		return self.__dict__[key]

	def __str__(self):
		return "Device %s" % self.mac

	def close(self):
		if self.sock is not None:
			self.sock.close()
			self.sock = None

	def connect(self):
		self.sock = BTCtl().connect(self.mac)

	def send(self, msg):
		cmd = msg.strip()
		Logger().write("[!] Sending '%s' to %s" % (cmd, str(self)))
		data = (cmd + "\n").encode()
		self.sock.send(data)

	def recv(self):
		data = bytes()
		while 10 not in data: # "\n" in data
			rcv = self.sock.recv(128)
			data += rcv
		print(data)
		out = data.decode().strip()
		Logger().write("[!] Recieved '%s' from %s" % (out, str(self)))
		return out

@singleton
class Hub(Thread):
	def __init__(self, *args, **kwargs):
		super().__init__(target=self.loop)
		self.fname = "settings.pcl"
		self.load(self.fname)

	def addDevice(self, mac):
		arr = [ x["idx"] for x in self.devices ]
		for i in range(0,10000):
			if i not in arr:
				break

		dev = Device(mac, idx=i)
		self.devices.append(dev)
		self.save()
		return True

	def addEvent(self, ev):
		self.events.append(ev)
		self.save()
		return True

	def clear(self):
		self.devices.clear()
		self.events.clear()

	def findDevice(self, mac):
		devs = list(filter(lambda x: x["mac"] == mac, self.devices))
		dev = devs[0] if len(devs) == 1 else None
		return dev

	def load(self, fname):
		try:
			with open(fname, "rb") as f:
				self.devices, self.events = pickle.load(f)
			self.fname = fname
		except Exception:
			self.devices = []
			self.events = []

		for x in self.devices:
			x.close()
		for x in self.events:
			x["started"] = False

	def loop(self):
		while True:
			if len(self.events) != 0:
				ev = self.events[0]
				ret = ev.exec()
				if ret is None:
					self.events.pop(0)
				self.events.sort(key=lambda x: x["time"])
				self.save()
			self.printStack()
			sleep(0.1)

	def printStack(self):
		with open("stack", "w") as f:
			for i,e in enumerate(self.events):
				f.write("%d. %s\n" % (i, str(e)))

	def save(self, fname=None):
		if fname is None:
			fname = self.fname
		with open(fname, "wb") as f:
			pickle.dump((self.devices, self.events), f)
		self.fname = fname

if __name__ == "__main__":
	h = Hub()
	print(1)
