from datetime import datetime as dt

def singleton(cls):
	instances = {}

	def getinstance(*args, **kwargs):
		name = args[0] if len(args) != 0 else "None"
		if cls not in instances:
			instances[cls] = {}
		if name not in instances[cls]:
			instances[cls][name] = cls()
		return instances[cls][name]

	return getinstance

@singleton
class Logger:
	def __init__(self, *args, **kwargs):
		self.fname = "out.log"
		if len(args) != 0:
			self.open(args[0])

	def open(self, fname):
		self.fname = fname
		with open(self.fname, "a") as f:
			f.write("\n\n\t\t\t[!] NEW SESSION (%s)" % dt.now().ctime())

	def write(self, *args):
		msg = "".join(str(x) for x in args)
		with open(self.fname, "a") as f:
			f.write(msg + "\n")
		print(msg)
