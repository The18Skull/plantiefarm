import re
from time import sleep
from Commands import run
from Logger import Logger, singleton

@singleton
class WiFiCtl:
	def __init__(self, *args, **kwargs):
		self.pattern = re.compile(r"Cell \d+ - Address: (?P<mac>(?:[0-9a-f]{2}:?){6}).+?ESSID:\"(?P<name>.+?)\"", flags=re.I | re.S)
		with open("network", "r") as f:
			self.template = f.read()

	def check(self):
		out = run("ifconfig")
		if "wlan0" in out:
			i = out.index("wlan0: flags="); s = out[i:]
			if "inet " not in s or s.index("inet ") - i > 200:
				Logger().write("[!] Failed to establish a Wi-Fi connection")
				return False
		else:
			Logger().write("[!] Wi-Fi interface was not found")
			return False
		return True

	def connect(self, name, password):
		Logger().write("[!] Connecting to Wi-Fi network '%s'" % name)
		with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as f:
			f.write(self.template % (name, password))
		run("wpa_cli -i wlan0 reconfigure")
		# check the connection
		sleep(5)
		return self.check()

	def disconnect(self):
		Logger().write("[!] Reseting Wi-Fi settings")
		with open("/etc/wpa_supplicant/wpa_supplicant.conf", "w") as f:
			f.write(self.template.split("network")[0])
		run("wpa_cli -i wlan0 reconfigure")

	def scan(self):
		Logger().write("[!] Scanning Wi-Fi networks")
		out = run("sudo iwlist wlan0 scan")
		networks = { mac: name.strip() for (mac,name) in self.pattern.findall(out.decode()) }
		return networks