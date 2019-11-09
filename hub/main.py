from cbor2 import dumps
from Logger import Logger
from time import time, sleep
from HubController import Hub
from Events import Refresh, Water
from WiFiController import WiFiCtl
from BluetoothController import BTCtl
from flask import Flask, send_from_directory, render_template, request, jsonify

App = Flask(__name__, static_folder="static", template_folder="static")

class MethodParam:
	def __init__(self, name, type, desc):
		self.name = name
		self.type = type
		self.desc = desc

class HTTPMethod:
	def __init__(self, method, url, desc, params):
		self.method = method
		self.url = url
		self.small_desc = desc.split(".")[0]
		self.big_desc = desc
		self.params = params

doc_methods = {
	"Device": [
		HTTPMethod("GET", "/api/scan", "Scan for SmartPot devices. Returns a dictionary of devices with key as device's MAC address and value as device's name. It takes 10 seconds to scan.", []),
		HTTPMethod("GET", "/api/devices", "List connected devices. Returns a dictionary of devices with key as ID and value as device's MAC address.", []),
		HTTPMethod("POST", "/api/device/add", "Add a new SmartPot device.", [ MethodParam("mac", "string", "Device's MAC address.") ]),
		HTTPMethod("GET", "/api/device/get", "Get sensor's values from a device.", [ MethodParam("mac", "string", "Device's MAC address.") ]),
		HTTPMethod("GET", "/api/device/refresh", "Refresh sensor's values for a device.", [ MethodParam("mac", "string", "Device's MAC address.") ]),
		HTTPMethod("GET", "/api/device/water", "Water a plant of device.", [ MethodParam("mac", "string", "Device's MAC address.") ])
	],
	"Event": [
		HTTPMethod("GET", "/api/events", "List planned events. Returns an array of events where each event is a dictionary with fields 'mac', 'type', 'time', 'repeat'.", []),
		HTTPMethod("POST", "/api/event/add", "Add an event.", [
			MethodParam("mac", "string", "Device's MAC address."),
			MethodParam("type", "string", "Event's type. Must be either 'refresh' or 'water'."),
			MethodParam("time", "number", "Unix timestamp UTC time to execute an event."),
			MethodParam("repeat", "number", "Unix timestamp UTC time to add after completion of the event. Can be omitted.")
		])
	]
}

@App.route("/")
def send_main():
	return render_template("index.html", methods=doc_methods)

@App.route("/manual")
def send_manual():
	manual = request.args["manual"].capitalize() if "manual" in request.args else "Device"
	page = int(request.args["page"]) if "page" in request.args else 0

	method = doc_methods[manual][page]
	return render_template("manual.html", method=method)

@App.route("/<path:filename>")
def send_file(filename):
	return send_from_directory(App.static_folder, filename)

@App.route("/api/device/add", methods=[ "POST" ])
def device_add():
	res = { "status": None, "msg": None }
	mac = request.args["mac"] if "mac" in request.args else ""

	if mac:
		dev = Hub().findDevice(mac)
		if dev is None:
			try:
				res["status"] = Hub().addDevice(mac)
				res["msg"] = "OK"
			except Exception:
				res["status"] = False
				res["msg"] = "Failed to add device"
		else:
			res["status"] = False
			res["msg"] = "Device is already paired"
	else:
		res["status"] = False
		res["msg"] = "Mac address is required"

	return jsonify(res)

@App.route("/api/device/get", methods=[ "GET" ])
def device_get():
	res = { "status": None, "msg": None }
	mac = request.args["mac"] if "mac" in request.args else ""

	dev = Hub().findDevice(mac)
	if dev is not None:
		data = dev["sensors"]

		res["status"] = True
		res["msg"] = data if res["status"] else "Failed to add an event"
	else:
		res["status"] = False
		res["msg"] = "There is no such device"

	return jsonify(res)

@App.route("/api/device/refresh", methods=[ "GET" ])
def device_refresh():
	res = { "status": None, "msg": None }
	mac = request.args["mac"] if "mac" in request.args else ""

	dev = Hub().findDevice(mac)
	if dev is not None:
		t = 0
		ev = Refresh(dev, t)

		res["status"] = Hub().addEvent(ev)
		res["msg"] = "OK" if res["status"] else "Failed to add event"
	else:
		res["status"] = False
		res["msg"] = "There is no such device"

	return jsonify(res)

@App.route("/api/device/water", methods=[ "GET" ])
def device_water():
	res = { "status": None, "msg": None }
	mac = request.args["mac"] if "mac" in request.args else ""

	dev = Hub().findDevice(mac)
	if dev is not None:
		t = 0
		ev = Water(dev, t)

		res["status"] = Hub().addEvent(ev)
		res["msg"] = "OK" if res["status"] else "Failed to add event"
	else:
		res["status"] = False
		res["msg"] = "There is no such device"

	return jsonify(res)

@App.route("/api/event/add", methods=[ "POST" ])
def event_add():
	res = { "status": None, "msg": None }
	mac = request.args["mac"] if "mac" in request.args else ""
	ev = request.args["type"].lower() if "type" in request.args else ""
	t = int(request.args["time"]) if "time" in request.args else 0
	repeat = int(request.args["repeat"]) if "repeat" in request.args else None

	dev = Hub().findDevice(mac)
	if dev is not None:
		if ev in ("refresh","water"):
			obj = Refresh if ev == "refresh" else Water
			ev = obj(dev, t, repeat)

			res["status"] = Hub().addEvent(ev)
			res["msg"] = "OK" if res["status"] else "Failed to add event"
		else:
			res["status"] = False
			res["msg"] = "Event type must be either 'refresh' or 'water'"
	else:
		res["status"] = False
		res["msg"] = "There is no such device"

	return jsonify(res)

@App.route("/api/devices", methods=[ "GET" ])
def devices():
	res = { "status": None, "msg": None }
	devices = Hub().devices

	res["status"] = True
	res["msg"] = { x["id"]: x["mac"] for x in devices }

	return jsonify(res)

@App.route("/api/events", methods=[ "GET" ])
def events():
	res = { "status": None, "msg": None }
	events = Hub().events

	res["status"] = True
	res["msg"] = [ {
		"mac": x["dev"]["mac"],
		"type": x.__class__.__name__.lower(),
		"time": x["time"],
		"repeat": x["repeat"]
	} for x in events ]

	return jsonify(res)

@App.route("/api/scan", methods=[ "GET" ])
def scan():
	res = { "status": None, "msg": None }
	BT = BTCtl()

	try:
		res["status"] = True
		res["msg"] = BT.scan()
	except Exception:
		res["status"] = False
		res["msg"] = "Failed to scan for bluetooth devices"

	return jsonify(res)

if __name__ == "__main__":
	BT = BTCtl()
	WF = WiFiCtl()

	while WF.check() is False:
		sock = BT.accept()
		networks = WF.scan()
		data = dumps(networks)
		sock.send(data)

		data = sock.recv(128)
		name, password = data.split(":")
		sock.close()

		WiFiCtl().connect(name, password)
		sleep(1)

	Hub().start()
	App.run(host="0.0.0.0")
