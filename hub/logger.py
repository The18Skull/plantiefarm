from utils import singleton

@singleton
class Logger:
	def __init__(self, *args, **kwargs):
		self.fname = "out.log"
		if len(args) != 0:
			self.open(args[0])

	def open(self, fname):
		self.fname = fname

	def write(self, *args):
		msg = "".join(str(x) for x in args)
		with open(self.fname, "a") as f:
			f.write(msg + "\n")
		print(msg)
