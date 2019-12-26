from time import sleep
from Logger import Logger
from HubController import Hub
from Events import event_types
from WiFiController import WiFiCtl
from datetime import datetime as dt
from BluetoothController import BTCtl
from flask import Flask, send_from_directory, render_template, request, jsonify

App = Flask(__name__, static_folder="static", template_folder="static")

class MethodParam:
	def __init__(self, name, type, desc):
		self.name = name
		self.type = type
		self.desc = desc

	def __getitem__(self, key):
		return self.__dict__[key]

class HTTPMethod:
	def __init__(self, method, url, desc, params):
		self.method = method
		self.url = url
		self.small_desc = desc.split(".")[0]
		self.big_desc = desc
		self.params = params

	def __getitem__(self, key):
		return self.__dict__[key]

doc_methods = {
	"Device": [
		HTTPMethod("GET", "/api/scan", "Scan for SmartPot devices. Returns a dictionary of devices with key as device's MAC address and value as device's name. It takes 10 seconds to scan.", []),
		HTTPMethod("GET", "/api/devices", "List connected devices. Returns a dictionary of devices with key as ID and value as device's MAC address.", []),
		HTTPMethod("POST", "/api/device/add", "Add a new SmartPot device.", [
			MethodParam("mac", "string", "Device's MAC address."),
			MethodParam("pin", "string", "Device's PIN for bluetooth pairing (optional).")
		]),
		HTTPMethod("GET", "/api/device/get", "Get all records of sensor's values for a device.", [ MethodParam("id", "number", "Device's ID.") ]),
		HTTPMethod("GET", "/api/device/last", "Get sensor's last values for a device.", [ MethodParam("id", "number", "Device's ID.") ]),
		HTTPMethod("GET", "/api/device/refresh", "Refresh sensor's values for a device.", [ MethodParam("id", "number", "Device's ID.") ]),
		HTTPMethod("GET", "/api/device/remove", "Remove a device.", [ MethodParam("id", "number", "Device's ID.") ]),
		HTTPMethod("GET", "/api/device/water", "Water a plant of device.", [ MethodParam("id", "number", "Device's ID.") ])
	],
	"Event": [
		HTTPMethod("GET", "/api/events", "List planned events. Returns an array of events where each event is a dictionary with fields 'id', 'device's id', 'type', 'time', 'repeat'.", []),
		HTTPMethod("POST", "/api/event/add", "Add an event.", [
			MethodParam("id", "number", "Device's ID."),
			MethodParam("type", "string", "Event's type. Must be one of '%s'." % ("', '".join([ x.capitalize() for x in event_types.keys() ]))),
			MethodParam("time", "number", "Unix timestamp UTC time to execute an event."),
			MethodParam("repeat", "number", "Unix timestamp UTC time to add after completion of the event. Can be omitted.")
		]),
		HTTPMethod("GET", "/api/event/remove", "Remove an event.", [ MethodParam("id", "number", "Event's id.") ])
	]
}

doc_algorithms = {
	"default": [
		{ "action": "refresh", "repeat": 60 }, # once per minute
		{ "action": "water", "repeat": 43200 } # once per 12 hours
	]
}

@App.before_request
def before_request():
	Logger().write("[%s] %s" % (request.method, request.full_path.rstrip("?")), tag="HTTP")

@App.route("/")
def send_main():
	def getLast(obj, tag):
		return obj["history"][-1][tag] if len(obj["history"]) != 0 else ""

	devs = {
		i: {
			"mac": dev["mac"],
			"pin": dev["pin"],
			"history": len(dev["history"]),
			"hum": getLast(dev, "hum"),
			"light": getLast(dev, "light"),
			"temp": getLast(dev, "temp"),
			"water": getLast(dev, "water")
		} for i,dev in Hub().devices.items()
	}
	evts = {
		i: {
			"type": ev.name.capitalize(),
			"dev": Hub().findDeviceID(ev.dev["mac"]),
			"time": dt.fromtimestamp(ev.time).strftime("%H:%M:%S %d/%m/%Y")
		} for i,ev in Hub().events.items()
	}

	return render_template("index.html", devices=devs, events=evts)

@App.route("/api")
def send_api():
	return render_template("api.html", methods=doc_methods)

@App.route("/manual")
def send_manual():
	manual = request.args["manual"].capitalize() if "manual" in request.args else "Device"
	page = int(request.args["page"]) if "page" in request.args else 0

	method = doc_methods[manual][page]
	return render_template("manual.html", method=method)

@App.route("/<path:filename>")
def send_file(filename):
	return send_from_directory(App.static_folder, filename)

@App.route("/api/scan", methods=[ "GET" ])
def scan():
	res = { "status": None, "msg": None }

	try:
		res["status"] = True
		res["msg"] = BTCtl().scan()
	except Exception as ex:
		Logger().write(ex, tag="EXCEPT")
		res["status"] = False
		res["msg"] = "Failed to scan for bluetooth devices"

	return jsonify(res)

@App.route("/api/devices", methods=[ "GET" ])
def devices():
	res = { "status": None, "msg": None }
	devices = Hub().devices.items()

	res["status"] = True
	res["msg"] = { i: d["mac"] for i,d in devices }

	return jsonify(res)

@App.route("/api/device/add", methods=[ "POST" ])
def device_add():
	res = { "status": None, "msg": None }
	mac = request.args["mac"] if "mac" in request.args else ""
	pin = request.args["pin"] if "pin" in request.args else "0000"

	if mac and BTCtl().macPattern.match(mac):
		dev = Hub().findDevice(mac)
		if dev is None:
			BTCtl().remove(mac)
			idx = Hub().addDevice(mac, pin)
			dev = Hub().findDevice(idx)
			if dev is not None:
				try:
					Hub().addEvent("setup", dev, 0)
					res["status"] = True
					res["msg"] = idx
				except Exception as ex:
					Logger().write(ex, tag="EXCEPT")
					Hub().removeDevice(idx)
					res["status"] = False
					res["msg"] = "Failed to setup device"
			else:
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
	idx = request.args["id"] if "id" in request.args else ""

	dev = Hub().findDevice(idx)
	if dev is not None:
		data = dev["history"]

		if len(data) != 0:
			res["status"] = True
			res["msg"] = data
		else:
			res["status"] = False
			res["msg"] = "The history is empty. Refresh the device"
	else:
		res["status"] = False
		res["msg"] = "There is no such device"

	return jsonify(res)

@App.route("/api/device/last", methods=[ "GET" ])
def device_last():
	res = { "status": None, "msg": None }
	idx = request.args["id"] if "id" in request.args else ""

	dev = Hub().findDevice(idx)
	if dev is not None:
		data = dev["history"]

		if len(data) != 0:
			res["status"] = True
			res["msg"] = data[-1]
		else:
			res["status"] = False
			res["msg"] = "The history is empty. Refresh the device"
	else:
		res["status"] = False
		res["msg"] = "There is no such device"

	return jsonify(res)

@App.route("/api/device/refresh", methods=[ "GET" ])
def device_refresh():
	res = { "status": None, "msg": None }
	idx = request.args["id"] if "id" in request.args else ""

	dev = Hub().findDevice(idx)
	if dev is not None:
		res["status"] = True
		res["msg"] = Hub().addEvent("refresh", dev, 0)
	else:
		res["status"] = False
		res["msg"] = "There is no such device"

	return jsonify(res)

@App.route("/api/device/remove", methods=[ "POST" ])
def device_remove():
	res = { "status": None, "msg": None }
	idx = request.args["id"] if "id" in request.args else ""

	dev = Hub().findDevice(idx)
	if dev is not None:
		res["status"] = Hub().removeDevice(idx)
		res["msg"] = "OK" if res["status"] else "Failed to remove device"
	else:
		res["status"] = False
		res["msg"] = "There is no such device"

	return jsonify(res)

@App.route("/api/device/water", methods=[ "POST" ])
def device_water():
	res = { "status": None, "msg": None }
	idx = request.args["id"] if "id" in request.args else ""

	dev = Hub().findDevice(idx)
	if dev is not None:
		res["status"] = True
		res["msg"] = Hub().addEvent("water", dev, 0)
	else:
		res["status"] = False
		res["msg"] = "There is no such device"

	return jsonify(res)

@App.route("/api/events", methods=[ "GET" ])
def events():
	res = { "status": None, "msg": None }
	events = Hub().events.items()

	res["status"] = True
	res["msg"] = { i: {
		"id": Hub().findDeviceID(ev["dev"]["mac"]),
		"type": ev["name"],
		"time": ev["time"],
		"repeat": ev["repeat"]
	} for i,ev in events }

	return jsonify(res)

@App.route("/api/event/add", methods=[ "POST" ])
def event_add():
	res = { "status": None, "msg": None }
	idx = request.args["id"] if "id" in request.args else ""
	ev = request.args["type"].lower() if "type" in request.args else ""
	time = int(request.args["time"]) if "time" in request.args else 0
	repeat = int(request.args["repeat"]) if "repeat" in request.args else None

	dev = Hub().findDevice(idx)
	if dev is not None:
		if ev in event_types.keys():
			res["status"] = True
			res["msg"] = Hub().addEvent(ev, dev, time, repeat)
		else:
			res["status"] = False
			res["msg"] = "Event type must be either 'refresh' or 'water'"
	else:
		res["status"] = False
		res["msg"] = "There is no such device"

	return jsonify(res)

@App.route("/api/event/remove", methods=[ "POST" ])
def event_remove():
	res = { "status": None, "msg": None }
	idx = request.args["id"] if "id" in request.args else -1

	ev = Hub().findEvent(idx)
	if ev is not None:
		res["status"] = Hub().removeEvent(idx)
		res["msg"] = "OK" if res["status"] else "Failed to remove event"
	else:
		res["status"] = False
		res["msg"] = "There is no such event"

	return jsonify(res)

if __name__ == "__main__":
	Logger("hub")
	Logger().write("[!] SmartHub is booting", tag="BOOT")
	WF = WiFiCtl()

	Logger().write("[!] Checking Wi-Fi connection", tag="BOOT")
	ip = WF.check()
	if ip is False:
		Logger().write("[!] Wi-Fi network is not available. Please setup Wi-Fi network using Bluetooth CLI with PIN '%s'" % BTCtl().pin, tag="BOOT")

	while ip is False:
		ip = WF.check()
		sleep(1)
	Logger().write("[!] Connected to Wi-Fi network with ip address '%s'" % ip, tag="BOOT")

	Logger().write("[!] SmartHub has started", tag="BOOT")
	Hub().start()
	App.run(host="0.0.0.0")
