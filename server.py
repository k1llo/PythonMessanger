import asyncio
from asyncio import transports
from typing import Optional


class ClientProtocol(asyncio.Protocol):
    login: str
    server: 'Server'
    transport: transports.Transport

    def __init__(self, server: 'Server'):
        self.server = server
        self.login = None

    def data_received(self, data: bytes):
        decoded = data.decode()
        print(f"<{self.login}>:{decoded}")#print message in server console
        msg = f"{self.login}>:{decoded}"
        self.server.message_history.append(msg)
        if len(self.server.message_history) > 10:
            self.server.message_history.pop(0)

        if self.login is None:
            # login:User
            if decoded.startswith("login:"):
                login = decoded.replace("login:", "").replace("\r\n", "")
                if login in self.server.users:
                    self.transport.write(
                        "Sorry you can't use this login\n".encode()
                    )
                    self.transport.close(self)
                else:
                    self.server.users.append(login)
                    self.login = login

                    self.transport.write(
                        f"Hi {self.login}!\n".encode()
                    )
                    self.send_message_history(self)

        else:
            self.send_message(decoded)

    def send_message(self, message):
        format_string = f"<{self.login}>: {message}"
        encoded = format_string.encode()

        for client in self.server.clients:
            if client.login != self.login:
                client.transport.write(encoded)

    def connection_made(self, transport: transports.Transport):
        self.transport = transport
        self.server.clients.append(self)
        print("Connection open")

    def connection_lost(self, exc):
        self.server.clients.remove(self)
        print("Connection Lost")

    def send_message_history(self, protocol):
        for content in self.server.message_history:
            self.transport.write(content.encode())




class Server:
    clients: list
    users: list
    message_history =[]

    def __init__(self):
        self.clients = []
        self.users = []

    def create_protocol(self):
        return ClientProtocol(self)


    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.create_protocol,
            "127.0.0.1",
            8888
        )

        print("Server started")

        await coroutine.serve_forever()


process = Server()
try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Server was stopped")
