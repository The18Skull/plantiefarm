from datetime import datetime as dt

def singleton(cls):
	instances = {}

	def getinstance(*args, **kwargs):
		if cls not in instances:
			instances[cls] = cls(*args, **kwargs)
		return instances[cls]

	return getinstance

@singleton
class Logger:
	def __init__(self, *args, **kwargs):
		fname = "logs/%s %s.log" % (args[0] if len(args) != 0 else "out", dt.now().strftime("%H-%M %d-%m-%Y"))
		self.open(fname)

	def open(self, fname):
		self.fname = fname
		with open(self.fname, "a") as f:
			f.write("\n\n\t\t[!] NEW SESSION (%s)\n" % dt.now().ctime())

	def write(self, *args, tag="INFO"):
		msg = "[%s] [%s]\t%s" % (dt.now().strftime("%H:%M:%S %d/%m/%Y"), tag, "".join(str(x) for x in args))
		with open(self.fname, "a") as f:
			f.write(msg + "\n")
		print(msg)
