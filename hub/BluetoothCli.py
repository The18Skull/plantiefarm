from time import sleep
# from json import dumps
from cbor2 import dumps
from Logger import Logger
from threading import Thread
from HubController import Device
from WiFiController import WiFiCtl
from BluetoothController import BTCtl

def threadFunc(sock):
	dev = Device("")
	dev["sock"] = sock

	while True:
		msg = dev.recv()
		if not msg:
			break

		cmd = msg.split()
		if cmd[0] == "connect" and len(cmd) == 2:
			name, password = cmd[1].split(":")
			ip = WiFiCtl().connect(name, password)
			dev.send("OK" if ip is not None else "FAIL")
		elif cmd[0] == "scan":
			networks = WiFiCtl().scan()
			data = dumps(networks)
			dev.send(data)
		elif cmd[0] == "check":
			ip = WiFiCtl().check()
			dev.send(str(ip))
		elif cmd[0] == "disconnect":
			WiFiCtl().disconnect()
			dev.send("OK")
		else:
			dev.send("Unknown command")

		sleep(1)

	Logger().write("[-] Client has disconnected")
	dev.close()

if __name__ == "__main__":
	Logger("cli.log")
	BT = BTCtl()
	Logger().write("[!] Bluetooth Command Line Interface has started. Waiting for connections")
	while True:
		sock = BT.accept(check_pin=True)
		Thread(target=threadFunc, args=(sock,)).start()
		sleep(1)
