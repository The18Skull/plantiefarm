import re, os
from time import sleep
from logger import Logger
from os.path import exists
from utils import singleton
from commands import InteractiveCommand, run

@singleton
class BTCtl:
	def __init__(self, *args, **kwargs):
		self.delim = re.compile(r"\[bluetooth\]", flags=re.I)
		self.acceptPattern = re.compile(r"Connection from (?P<mac>(?:[a-f0-9]{2}:?){6}) to (?P<path>(?:/[a-z0-9]+)+)", flags=re.I)
		self.connPattern = re.compile(r"Connected (?P<path>(?:/[a-z0-9]+)+) to (?P<mac>(?:[a-f0-9]{2}:?){6}) on channel \d+", flags=re.I)
		self.pattern = re.compile(r"Device (?P<mac>(?:[a-f0-9]{2}:?){6}) (?P<name>.*)", flags=re.I)
		self.pairPattern1 = re.compile(r"Enter PIN code", flags=re.I)
		self.pairPattern2 = re.compile(r"Confirm passkey \d+ \(yes/no\)", flags=re.I)
		self.env = InteractiveCommand("sudo bluetoothctl", out="btout")
		self.dbus = None
		self.fd = None

	def accept(self):
		self.reset()
		self.env.send("pairable on")
		self.env.send("discoverable on")
		Logger().write("[!] Waiting for connection")
		while True:
			out = self.env.read()
			res = list(filter(lambda x: x[1] == "Paired: yes", self.pattern.findall(out)))
			if len(res) != 0:
				mac = res[0][0]
				Logger().write("[!] Device %s was paired" % mac)
				break
			sleep(1)
		self.env.send("pairable off")
		self.env.send("discoverable off")

	def close(self):
		if self.fd is not None:
			os.close(self.fd) # close i/o bus
			self.fd = None
		if self.dbus:
			self.dbus.stop()
			self.dbus = None
		# run("sudo rfcomm release hci0")
		run("sudo killall rfcomm")

	def connect(self, mac, pin="0000"):
		self.close()
		Logger().write("[!] Connecting to %s" % mac)
		deviceList = self.paired()
		if mac not in deviceList:
			for i in range(10):
				deviceList = self.scan()
				if mac in deviceList:
					break
				sleep(1)
			if mac not in deviceList:
				Logger().write("[!] %s was not found" % mac)
				return False
			Logger().write("[!] Pairing with %s" % mac)
			self.env.send("pair %s" % mac)
			while True:
				out = self.env.read()
				if self.pairPattern1.search(out):
					self.env.send(pin)
					break
				elif self.pairPattern2.search(out):
					self.env.send("yes")
					break
				sleep(1)
		Logger().write("[!] Establishing a connection with %s" % mac)
		self.dbus = InteractiveCommand("sudo rfcomm connect hci0 %s" % mac, out="null")
		self.wait(self.connPattern)
		self.fd = os.open("/dev/rfcomm0", os.O_RDWR)
		Logger().write("[!] Connected to %s" % mac)

	def devices(self):
		self.env.send("devices")
		return self.parse()

	def listen(self):
		self.close()
		Logger().write("[!] Waiting for connection")
		self.dbus = InteractiveCommand("sudo rfcomm watch hci0", out="null")
		# self.env.send("connect %s" % mac)
		self.wait(self.acceptPattern)
		self.fd = os.open("/dev/rfcomm0", os.O_RDWR)
		Logger().write("[!] A device has connected")

	def paired(self):
		self.env.send("paired-devices")
		return self.parse()

	def parse(self):
		out = self.env.read()
		deviceList = { mac: name.strip() for (mac,name) in self.pattern.findall(out) }
		return deviceList

	def recv(self, bufSize=128):
		if self.fd is None:
			return
		# os.lseek(self.fd, 0, os.SEEK_SET)
		data = os.read(self.fd, bufSize)
		out = data.decode()
		return out

	def reset(self):
		self.close()
		deviceList = self.paired()
		for mac in deviceList:
			self.env.send("remove %s" % mac)
		Logger().write("[!] All paired devices were removed")

	def scan(self, wait=5):
		# scan for devices
		self.env.send("scan on")
		sleep(wait)
		self.env.send("scan off")
		# get list of available devices
		return self.devices()

	def send(self, msg):
		if self.fd is None:
			return
		# os.lseek(self.fd, 0, os.SEEK_SET)
		data = (msg.strip() + "\n").encode()
		os.write(self.fd, data)

	def wait(self, pattern):
		while True:
			if exists("/dev/rfcomm0"):
				break
			# out = self.dbus.read()
			# res = pattern.search(out)
			# print(out, "\n\n\n", res)
			# if res is not None:
			# 	self.fd = os.open(res["path"], os.O_RDWR)
			# 	break
			sleep(1)

if __name__ == "__main__":
	BT = BTCtl()
	# BT.accept()
	BT.listen()
	print(BT.recv())
	BT.send("ok")
	print(BT.recv())
	BT.close()
