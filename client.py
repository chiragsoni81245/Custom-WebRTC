from socket import *
import os, sys
from threading import Thread
import re
from concurrent.futures import ThreadPoolExecutor
from time import sleep

class Client:

	def __init__(self, host, port):
		self.host = host
		self.port = port
		# Create Socket
		self.socket_obj = socket(family=AF_INET, type=SOCK_DGRAM)
		self.socket_obj.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
		self._conn_handler_thread_pool = ThreadPoolExecutor(10)
		self._receiver_thread_pool = ThreadPoolExecutor(10)
		self.connections = []
		self.received_data = {}

	def stun_request(self, host="3.132.150.53", port=3478):
		print("Connecting to STUN Server...")
		
		print("STUN Request to {}:{}".format(host, port))
		# Sending Request to STUN Server
		request = "whoami\0"
		for i in request:
			self.socket_obj.sendto(i.encode('utf-8'), (host, port))
		print("Listning for STUN server response...")
		data = b''
		temp = self.socket_obj.recv(1)
		while temp!=b"\x00":
			data += temp
			temp = self.socket_obj.recv(1)

		data = str(data, 'utf-8')

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
			This function is to bind port with our socket
		'''
		try:
			print("Binding to port {} ...".format(self.port))
			self.socket_obj.bind(( self.host, self.port ))
		except error as msg:
			print("Socket Binding error {}".format(str(msg)))
			print("Retrying...")
			self.bind()

	def request_peer(self, host, port):
		try:
			offer_message = "Hey!\0"
			for i in offer_message:
				self.socket_obj.sendto(i.encode('utf-8'), (host,port))
			print("Waiting for Peer to response...")
			data, error_msg = b'', False
			while True:
				temp, address = self.socket_obj.recvfrom(1)
				if address!=(host,port):
					print("Unknown Client {}:{} tries to Connect".format(address[0], address[1]))
					continue
				if len(data.decode('utf-8'))>2:
					error_msg = "Message length exeded!"
					print(error_msg)
					break
				if temp==b"\x00":
					break
				data += temp
				
			
			peer_response = data.decode('utf-8')
			if error_msg or peer_response!="Yo":
				raise ValueError('Wrong Response of peer request from {}:{}'.format(host, port))
			
			print("Connected!")
			self._conn_handler_thread_pool.submit(self.receiver)
			self._conn_handler_thread_pool.submit(self.message_printer)
			self.message_sender((host, port))

		except Exception as error:
			print("Error in requesting peer")
			print(error)

	def response_to_peer(self, host, port):
		response_for_peer = "Yo\0"
		for i in response_for_peer:
			self.socket_obj.sendto(i.encode('utf-8'), (host,port))

		print("Waiting for Peer to response...")
		data, error_msg = b'', False
		while True:
			temp, address = self.socket_obj.recvfrom(1)
			if address!=(host,port):
				print("Unknown Client {}:{} tries to Connect".format(address[0], address[1]))
				continue
			if len(data.decode('utf-8'))>4:
				error_msg = "Message length exeded!"
				print(error_msg)
				break
			if temp==b"\x00":
				break
			data += temp
			
		peer_response = data.decode('utf-8')
		if error_msg or peer_response!="Hey!":
			raise ValueError('Wrong Response of peer request from {}:{}'.format(host, port))

		print("Connected!")
		self._conn_handler_thread_pool.submit(self.receiver)
		self._conn_handler_thread_pool.submit(self.message_printer)
		self.message_sender((host, port))

	def receiver(self):
		while True:
			temp, address = self.socket_obj.recvfrom(1)
			while temp!=b'\x00':
				if address in self.received_data:
					if not self.received_data[address][1]:
						self.received_data[address][0] += temp
				else:
					self.received_data[address] = [temp, False]
				temp, address = self.socket_obj.recvfrom(1)
			self.received_data[address][1] = True

	def message_printer(self):
		while True:
			keys = self.received_data.keys()
			has_to_be_deleted_keys = []
			for address in keys:
				if self.received_data[address][1]:
					print("\nMessage[{}:{}]<-- {}".format(address[0], address[1], self.received_data[address][0].decode('utf-8')))
					has_to_be_deleted_keys.append(address)

			for key in has_to_be_deleted_keys:
				del self.received_data[key]
			sleep(0.01)

	def message_sender(self, address):
		while True:
			msg = input("Write a MSG to {}:{} - ".format(address[0], address[1]))
			while msg=="":
				msg = input("Write a MSG to {}:{} - ".format(address[0], address[1]))
			
			msg+="\0"
			for i in msg:
				self.socket_obj.sendto(i.encode('utf-8'), address)


if __name__=="__main__":
	c1 = Client('0.0.0.0', int(sys.argv[1]))
	c1.bind()
	print(c1.stun_request())