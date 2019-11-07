import re, os
from time import sleep
from logger import Logger
from os.path import exists
from utils import singleton
from threading import Thread
from bluetooth import BluetoothSocket, RFCOMM, discover_devices, lookup_name, _get_available_port as get_port

@singleton
class BTCtl:
	def __init__(self, *args, **kwargs):
		self.sockets = []

	def accept(self):
		pass

	def close(self):
		pass

	def connect(self, mac, pin):
		pass

	def devices(self):
		pass

	def recv(self):
		pass

	def send(self, *args, **kwargs):
		pass

if __name__ == "__main__":
	pass
