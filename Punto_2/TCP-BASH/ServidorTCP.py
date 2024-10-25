import socket
import threading
import os
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

class Cliente:
    def __init__(self, nombre, dos, public_key):
        self.nombre = nombre
        self.dos = dos
        self.public_key = public_key
        self.conectado = True
        self.mensajes_pendientes = []

class Mensaje:
    def __init__(self, nombre_cliente, contenido):
        self.nombre_cliente = nombre_cliente
        self.contenido = contenido

clientes = []
mensajes = []

CLIENTS_FILE = "clientes.txt"

def iniciar_servidor():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 5004))
    server_socket.listen()

    # Generar par de claves RSA
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    print("Iniciando el servidor...")
    while True:
        print("Servidor iniciado, esperando clientes...")

        client_socket, _ = server_socket.accept()
        dis = client_socket.makefile('rb')
        dos = client_socket.makefile('wb')

        client_name = dis.readline().strip().decode()
        print(f"Nombre del cliente recibido: {client_name}")  # Línea de depuración

        # En lugar de dis.read(), usar readline para recibir la clave pública
        client_public_pem = dis.readline().strip()  # Usar readline para asegurarte de recibir todo el contenido
        print(f"Clave pública recibida:\n{client_public_pem.decode()}")  # Línea de depuración
        client_public_key = serialization.load_pem_public_key(client_public_pem)

        cliente = Cliente(client_name, dos, client_public_key)
        clientes.append(cliente)

        # Enviar clave pública del servidor al cliente
        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        print(f"Clave pública del servidor enviada:\n{public_pem.decode()}")  # Línea de depuración
        dos.write(public_pem)
        dos.write(b'\n')  # Asegúrate de que haya un salto de línea al final
        dos.flush()

        enviar_mensajes_pendientes(cliente)
        threading.Thread(target=recibir_mensajes_cliente, args=(cliente, dis, dos, private_key)).start()
        
def recibir_mensajes_cliente(cliente, dis, dos, private_key):
    while True:
        try:
            encrypted_message = dis.readline().strip()
            client_message = private_key.decrypt(
                encrypted_message,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            ).decode()
            print(f"Mensaje recibido desde el cliente ({cliente.nombre}): {client_message}")
            if client_message == "Terminar":
                print("Terminando la conexión con el cliente...")
                actualizar_estado_cliente(cliente, False)
                if os.path.exists(CLIENTS_FILE):
                    os.remove(CLIENTS_FILE)
                break
            elif client_message == "Desconectar":
                print("Desconectando al cliente...")
                dos.write(b"Desconectado\n")
                dos.flush()
                actualizar_estado_cliente(cliente, False)
                with open(CLIENTS_FILE, "a") as file:
                    file.write(f"{cliente.nombre},False\n")
            elif client_message == "Reconectar":
                print("Reconectando al cliente...")
                actualizar_estado_cliente(cliente, True)
                enviar_mensajes_pendientes(cliente)
            elif client_message == "RECUPERAR_MENSAJES":
                enviar_mensajes_pendientes(cliente)
            elif client_message.startswith("ENVIAR_ARCHIVO"):
                recibir_archivo(dis, client_message)
            elif client_message.startswith("DESCARGAR_ARCHIVO"):
                enviar_archivo(cliente, client_message)
            else:
                mensajes.append(Mensaje(cliente.nombre, client_message))
                enviar_mensaje_otros_clientes(cliente, cliente.nombre, client_message)
        except Exception as e:
            print(f"Error al recibir el mensaje del cliente: {e}")
            actualizar_estado_cliente(cliente, False)
            break

def recibir_archivo(dis, client_message):
    try:
        _, filename, filesize = client_message.split()
        filesize = int(filesize)
        with open(filename, 'wb') as f:
            while filesize > 0:
                data = dis.read(min(filesize, 1024))
                if not data:
                    break
                f.write(data)
                filesize -= len(data)
        print(f"Archivo recibido: {filename}")
        notificar_nuevo_archivo(filename)
    except Exception as e:
        print(f"Error al recibir el archivo: {e}")

def enviar_archivo(cliente, client_message):
    try:
        _, filename = client_message.split()
        if os.path.exists(filename):
            filesize = os.path.getsize(filename)
            cliente.dos.write(f"DESCARGAR_ARCHIVO {filename} {filesize}\n".encode())
            cliente.dos.flush()
            with open(filename, 'rb') as f:
                while True:
                    data = f.read(1024)
                    if not data:
                        break
                    cliente.dos.write(data)
                    cliente.dos.flush()
            print(f"Archivo enviado: {filename}")
        else:
            cliente.dos.write(f"ERROR Archivo no encontrado: {filename}\n".encode())
            cliente.dos.flush()
    except Exception as e:
        print(f"Error al enviar el archivo: {e}")

def notificar_nuevo_archivo(filename):
    for cliente in clientes:
        if cliente.conectado:
            try:
                cliente.dos.write(f"NUEVO_ARCHIVO {filename}\n".encode())
                cliente.dos.flush()
            except Exception as e:
                print(f"Error al notificar al cliente sobre el nuevo archivo: {e}")

def actualizar_estado_cliente(cliente, conectado):
    cliente.conectado = conectado

def enviar_mensajes_pendientes(cliente):
    for mensaje in cliente.mensajes_pendientes:
        try:
            cliente.dos.write(f"{mensaje}\n".encode())
            cliente.dos.flush()
        except Exception as e:
            print(f"Error al enviar el mensaje al cliente: {e}")
    cliente.mensajes_pendientes.clear()

def enviar_mensaje_otros_clientes(sender_cliente, sender_name, message):
    for cliente in clientes:
        if cliente != sender_cliente:
            if cliente.conectado:
                enviar_mensaje(cliente, Mensaje(sender_name, message))
            else:
                cliente.mensajes_pendientes.append(f"{sender_name}: {message}")

def enviar_mensaje(cliente, mensaje):
    try:
        encrypted_message = cliente.public_key.encrypt(
            f"{mensaje.nombre_cliente}: {mensaje.contenido}".encode(),
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        cliente.dos.write(encrypted_message + b'\n')
        cliente.dos.flush()
        mensaje.enviado = True
    except Exception as e:
        print(f"Error al enviar el mensaje al cliente: {e}")

if __name__ == "__main__":
    iniciar_servidor()