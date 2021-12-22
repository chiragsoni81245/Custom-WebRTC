from socket import *
import os
from threading import Thread
import re
from concurrent.futures import ThreadPoolExecutor


class Client:

	def __init__(self, host, port):
		self.host = host
		self.port = port
		self._conn_handler_thread_pool = ThreadPoolExecutor(10)
		self._receiver_thread_pool = ThreadPoolExecutor(10)
		self.connections = []
		self.receivers = {}

	def stun_request(self, host="3.132.150.53", port=3478):
		print("Connecting to STUN Server...")
		# Create Socket
		self.socket_obj = socket(family=AF_INET, type=SOCK_DGRAM)
		self.socket_obj.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		# Bind Socket
		self.socket_obj.bind(( self.host, self.port ))
		# Connect Socket
		self.socket_obj.connect((host, port))

		print("STUN Request to {}:{}".format(host, port))
		data = b''
		temp = self.socket_obj.recv(1)
		while temp:
			if temp==b"\x00":
				break
			data += temp
			temp = self.socket_obj.recv(1)

		data = str(data, 'utf-8')
		self.socket_obj.close()
		self.socket_obj = None
		if re.fullmatch("^(?:\d{1,3}\.){3}\d{1,3}:\d+$", data):
			temp_data = data.strip().split(":")
			self.public_ip, self.public_port = temp_data[0], int(temp_data[1])
			print("STUN request successfully completed")
			return (self.public_ip, self.public_port)
		else:
			print("-->", data)
			raise ValueError("Invalid Respose from STUN Request")

	def bind(self):
		'''
			This function is to bind port with our socket and then
			start listening on that port
		'''
		self.socket_obj = socket(family=AF_INET, type=SOCK_DGRAM)
		self.socket_obj.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		try:
			print("Binding to port {} ...".format(self.port))
			self.socket_obj.bind(( self.host, self.port ))
			# One argument is listen function is the no. of unaccepted connection allowed before refusing new connections
			print("Listening...")
			self.socket_obj.listen(5)
		except error as msg:
			print("Socket Binding error {}".format(str(msg)))
			print("Retrying...")
			self.bind()

	def accept_connections(self):
		'''
			This function is for Establishing Connections before that socket must be listening
		'''
		try:
			while True:
				conn, address = self.socket_obj.accept()
				print("Connection has been established! | {}:{}".format(address[0],address[1]))

				thread = self._conn_handler_thread_pool.submit(
					self.conn_handler, 
					conn, address
				)
				self.connections.append((conn, address, thread))

		except Exception as error:
			print("Error in accepting connections")
			print(error)


	def receiver(self, conn, address):
		print("Receiver Started for {}".format(address))
		data = b''
		temp = conn.recv(1)
		while temp:
			if temp==b"\x00":
				print("\n{} <-- {}".format( str(data, 'utf-8'), address))
				data = b''
				temp = conn.recv(1)
			data += temp
			temp = conn.recv(1)

	def conn_handler(self, conn, address):
		receiver_thread_obj = self._receiver_thread_pool.submit(
			self.receiver,
			conn, address
		)
		self.receivers[address] = receiver_thread_obj

		while True:
			msg = input("Write a MSG to {}:{} - ".format(address[0], address[1]))
			while msg=="":
				msg = input("Write a MSG to {}:{} - ".format(address[0], address[1]))
			
			msg+="\0"
			msg = str.encode(msg, 'utf-8')
			conn.send(msg)