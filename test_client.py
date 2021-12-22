from client import Client


client = Client("0.0.0.0", 8080)

print(client.stun_request())
client.bind()
client.accept_connections()
