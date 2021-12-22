from socket import *
import os
from threading import Thread

def clear_screen():
	if os.name=="nt":
		os.system("cls")
	else:
		os.system("clear")


class Client:

	def __init__(self):
		self.soc = socket(family=AF_INET, type=SOCK_DGRAM)
		self.soc.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)

	def connect(self, host, port):
		self.host = host
		self.port = port
		print("Connecting...")
		self.soc.connect((host, port))
		print("Connected to {}:{}".format(host, port))

	def receiver(self):
		print("Receiver Started")
		data = b''
		temp = self.soc.recv(1)
		while temp:
			if temp==b"\x00":
				print("\n{} <-- {}".format( str(data, 'utf-8'), "{}:{}".format(self.host, self.port)))
				data = b''
				temp = self.soc.recv(1)
			data += temp
			temp = self.soc.recv(1)

	def send(self, data):
		data += "\0"
		data = str.encode(data, 'utf-8')
		self.soc.send(data)


if __name__=="__main__":
	c1 = Client()
	c1.connect('<PUBLIC_IP_GET_FROM_TEST_CLIENT>', '<PUBLIC_PORT_GET_FROM_TEST_CLIET> as Integer')
	receiver_thred = Thread(target=c1.receiver)
	receiver_thred.start()

	# clear_screen()
	while True:
		data = input("Write a MSG: ")
		c1.send(data)

