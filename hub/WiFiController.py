import re
from time import sleep
from Commands import run
from Logger import Logger, singleton

@singleton
class WiFiCtl:
	def __init__(self, *args, **kwargs):
		self.interface = self.getInterface()
		self.checkPattern = re.compile(r"%s: flags.+?inet (?P<ip>(?:\d{,3}\.?){4})" % self.interface, flags=re.I | re.S)
		self.pattern = re.compile(r"Cell \d+ - Address: (?P<mac>(?:[0-9a-f]{2}:?){6}).+?ESSID:\"(?P<name>.+?)\"", flags=re.I | re.S)
		with open("network", "r") as f:
			self.template = f.read()

	def check(self):
		out = run("ifconfig")

		if self.interface in out:
			res = self.checkPattern.search(out)
			if res: return res["ip"]
			else: Logger().write("[!] Failed to establish a Wi-Fi connection", tag="WFCTL")
		else: Logger().write("[!] Wi-Fi interface was not found", tag="WFCTL")

		return "null"

	def connect(self, name, password):
		Logger().write("[!] Connecting to Wi-Fi network '%s'" % name, tag="WFCTL")
		with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as f:
			f.write(self.template % (name, password))
		run("wpa_cli -i %s reconfigure" % self.interface)
		# check the connection
		sleep(10)
		return self.check()

	def disconnect(self):
		Logger().write("[!] Reseting Wi-Fi settings", tag="WFCTL")
		with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as f:
			f.write(self.template.split("network")[0])
		run("wpa_cli -i %s reconfigure" % self.interface)

	def getInterface(self):
		out = run("sudo iw dev")
		res = re.search(r"\tInterface (\S+)", out, flags=re.I)
		if res is not None:
			res = res[1]
		return res

	def scan(self):
		Logger().write("[!] Scanning Wi-Fi networks", tag="WFCTL")
		out = run("sudo iwlist %s scan" % self.interface)
		networks = { mac: name.strip()[:16] for (mac,name) in self.pattern.findall(out) }
		return networks
