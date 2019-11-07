from time import sleep
from logger import Logger
from HubController import Hub
from WiFiController import WiFiCtl
from datetime import datetime as dt
from BluetoothController import BTCtl
from flask import Flask, send_from_directory, request, abort, jsonify

App = Flask(__name__, static_folder="static")

def comment():
	"""
	@App.route("/")
	def send_main():
		return send_file("index.html")

	@App.route("/<path:filename>")
	def send_file(filename):
		return send_from_directory(App.static_folder, filename)

	@App.route("/uploads/<path:filename>")
	def send_uploaded(filename):
		return send_from_directory("uploads", filename)

	@App.route("/upload", methods=[ "POST" ])
	def upload():
		fl = request.files["file"]
		ext = fl.filename.split(".")[-1]
		resource = request.form["resource"]
		if resource in [ "Scopus", "Web of Science" ] and ext in [ "txt", "docx" ]:
			index = len(listdir("./uploads")) # file counter
			filepath = "./uploads/%d.%s" % (index, ext)
			fl.save(filepath)
			res = { "id": index }
			if ext == "txt":
				with open(filepath, "r") as f:
					text = f.read()
			elif ext == "docx":
				text = word2txt().convert(filepath)
			t0 = time.time()
			if resource == "Web of Science":
				res["result"] = sciparser.WoS().parse(text)
			else: # resource == "Scopus"
				res["result"] = sciparser.Scopus().parse(text)
			for (i, article) in enumerate(res["result"]):
				year = re.search(r"\d{4}", article["source"]["date"])
				if year:
					article["date"] = year[0]
				journal = g.db.findJournal(article["source"]["title"])
				print("[V]" if journal["id"] else "[X]", article["source"]["title"], "|", journal["title"]) # debug
				article["source"]["id"] = journal["id"]
				article["source"]["title"] = journal["title"]
				article["country"] = journal["country"]
				if not g.db.saveArticle(index, article, fl.filename, resource):
					del res["result"][i]
			res["resource"] = resource
			res["time"] = time.time() - t0
			res["status"] = "success"
			print("[!] Completed in %f sec." % res["time"]) # log but mostly debug
			return jsonify(res)
		else:
			abort(400)

	@App.route("/approve", methods=[ "POST" ])
	def approve():
		if request.is_json:
			id = request.json["id"]
			articles = request.json["articles"]
			for (key, value) in articles.items():
				g.db.approveArticle(id, key, value)
			return "success"
		abort(400)

	@App.route("/api/approved", methods=[ "GET" ])
	def get_approved():
		start = 0
		if "start" in request.args:
			start = request.args["start"]
		res = g.db.getApproved(start)
		return jsonify(res)

	@App.route("/api/faculties", methods=[ "GET" ])
	def get_faculties():
		res = [ [ "РЭФ", "ФТФ" ], [ "МТФ", "ФЛА" ], [ "МТФ", "ФТФ" ] ]
		return jsonify(res)

	@App.route("/api/resources", methods=[ "GET" ])
	def get_resources():
		# Beautiful title: RegExp
		res = {
			"Web of Science": "wos|web|science",
			"Scopus": "scop?u?s?"
		}
		return jsonify(res)

	@App.route("/api/staff", methods=[ "GET" ])
	def get_staff():
		res = list()
		if "search" in request.args:
			res = g.db.findStaff(request.args["search"].lower())
		return jsonify(res)

	@App.route("/api/staff", methods=[ "POST" ])
	def add_staff():
		staff = None
		if len(request.args) != 0:
			staff = request.args
		elif len(request.form) != 0:
			staff = request.form
		elif request.is_json:
			staff = request.json
		if staff is not None:
			if type(staff) != list:
				staff = [ staff ]
			res = g.db.addStaff(staff)
			return jsonify(res)
		abort(400)

	@App.route("/api/editstaff", methods=[ "POST" ])
	def edit_staff():
		staff = None
		if len(request.args) != 0:
			staff = request.args
		elif len(request.form) != 0:
			staff = request.form
		elif request.is_json:
			staff = request.json
		if staff is not None:
			if type(staff) != list:
				staff = [ staff ]
			res = g.db.editStaff(staff)
			return jsonify(res)
		abort(400)

	@App.route("/api/journals", methods=[ "POST" ])
	def add_journals():
		journals = None
		if len(request.args) != 0:
			journals = request.args
		elif len(request.form) != 0:
			journals = request.form
		elif request.is_json:
			journals = request.json
		if journals is not None:
			if type(journals) != list:
				journals = [ journals ]
			res = g.db.addJournals(journals)
			return jsonify(res)
		abort(400)

	@App.route("/api/translit", methods=[ "GET" ])
	def transliterate():
		if "string" in request.args:
			res = { "string": request.args["string"] }
			res["result"] = translit.encode(res["string"])
			return jsonify(res)
		abort(400)
	"""

if __name__ == "__main__":
	while WiFiCtl().check() is False:
		BT = BTCtl()
		BT.accept(); BT.listen()
		data = BT.recv()
		name, password = data.split(":")
		WiFiCtl().connect(name, password)
		sleep(1)
	Hub().run()
	App.run()
