import re, os
from time import sleep
from os.path import exists
from Logger import Logger, singleton
from Commands import run, InteractiveCommand
from bluetooth import BluetoothSocket, RFCOMM

def get_port():
	while True:
		for port in range(1,9): # limit 8 devices
			s = BluetoothSocket(RFCOMM)
			try:
				s.bind(("", port))
				s.close()
				return port
			except:
				s.close()
		sleep(1)

@singleton
class BTCtl:
	def __init__(self, *args, **kwargs):
		self.pin = "5835"
		self.pattern = re.compile(r"Device (?P<mac>(?:[a-f0-9]{2}:?){6}) (?P<name>.*)", flags=re.I)
		self.macPattern = re.compile(r"(?P<mac>(?:[a-f0-9]{2}:?){6})", flags=re.I)
		self.pairPattern1 = re.compile(r"Enter PIN code", flags=re.I)
		self.pairPattern2 = re.compile(r"Confirm passkey \d+ \(yes/no\)", flags=re.I)
		self.env = InteractiveCommand("sudo bluetoothctl", out="btout")

	def __del__(self):
		self.close()

	def accept(self, check_pin=True):
		self.env.send("pairable on")
		self.env.send("discoverable on")

		sock = BluetoothSocket(RFCOMM)
		port = get_port()
		sock.bind(("", port))
		sock.listen(1)

		Logger().write("[!] Waiting for connection")
		while True:
			client, addr = sock.accept()
			mac = addr[0]

			try:
				msg = client.recv(8).decode().strip()
			except:
				client.close()
				continue

			if check_pin is True and msg != self.pin:
				Logger().write("[!] Authentication failed")
				client.close()
				continue

			break
		Logger().write("[!] Device %s has connected" % mac)

		self.env.send("discoverable off")
		self.env.send("pairable off")

		return client

	def clear(self):
		deviceList = self.paired()
		for mac in deviceList:
			self.remove(mac)
		Logger().write("[!] All paired devices were removed")

	def close(self):
		self.env.close()

	def connect(self, mac):
		Logger().write("[!] Establishing a connection with %s" % mac)

		try:
			sock = BluetoothSocket(RFCOMM)
			port = get_port()
			sock.connect((mac, port))
			Logger().write("[!] Connected to %s" % mac)
		except Exception:
			Logger().write("[!] Connection to %s was refused" % mac)
			sock = None

		return sock

	def devices(self):
		out = run("sudo bluetoothctl devices")
		return self.parse(out)

	def pair(self, mac, pin="0000"):
		Logger().write("[!] Connecting to %s with pin %s" % (mac, pin))

		deviceList = self.paired()
		if mac not in deviceList:
			Logger().write("[!] %s is unknown" % mac)
			for i in range(3): # 3 attempts, 10 sec per attempt
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
			elif self.pairPattern2.search(out):
				self.env.send("yes")
			elif "Pairing successful" in out:
				Logger().write("[!] Paired with %s" % mac)
				break
			elif "Failed to pair" in out:
				Logger().write("[!] Failed to pair with %s" % mac)
				self.remove(mac)
				return False
			sleep(1)

		return True

	def paired(self):
		out = run("sudo bluetoothctl paired-devices")
		return self.parse(out)

	def parse(self, out):
		deviceList = { mac: name.strip() for (mac,name) in self.pattern.findall(out) }
		return deviceList

	def remove(self, mac):
		run("sudo bluetoothctl remove %s" % mac)
		Logger().write("[!] Device %s was removed" % mac)

	def scan(self, wait=10):
		Logger().write("[!] Looking for BT devices")
		# scan for devices
		run("sudo bluetoothctl --timeout 10 scan on")
		# get list of available devices
		return self.devices()
