from time import sleep
from subprocess import run as execCmd, Popen, PIPE

def run(*args, **kwargs):
	if len(args) == 0:
		return ""
	if isinstance(args[0], str):
		args = (args[0].split(), *args[1:])
	kwargs["stdout"] = PIPE
	env = execCmd(*args, **kwargs)
	out = env.stdout
	return out.decode()

class InteractiveCommand(Popen):
	def __init__(self, *args, **kwargs):
		fname = kwargs.pop("out") if "out" in kwargs else "out"

		args = (args[0].split(),)
		kwargs["stdin"] = PIPE
		kwargs["stdout"] = open(fname, "wb")
		kwargs["stderr"] = kwargs["stdout"]
		super().__init__(*args, **kwargs)

		self.fin = open(fname, "rb")
		self.fout = self.stdin

	def __del__(self):
		self.close()

	def close(self):
		self.stop()
		self.fin.close()
		self.fout.close()
		self.terminate()

	def read(self):
		out = self.fin.read()
		return out.decode()

	def send(self, cmd):
		cmd = (cmd.strip() + "\n").encode()
		self.fout.write(cmd)
		self.fout.flush()
		sleep(1)

	def stop(self):
		self.send("\003") # ctrl+c
