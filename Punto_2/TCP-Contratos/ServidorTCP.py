import socket
import threading
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asymmetric_padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import os

class Cliente:
    def __init__(self, nombre, dos, aes_key):
        self.nombre = nombre
        self.dos = dos
        self.conectado = True
        self.aes_key = aes_key  # Clave AES

clientes = []
private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
mensajes_pendientes = {}

def iniciar_servidor():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 5004))
    server_socket.listen()

    print("Iniciando el servidor...")
    while True:
        try:
            client_socket, _ = server_socket.accept()
            dis = client_socket.makefile('rb')
            dos = client_socket.makefile('wb')

            # Recibir la clave pública del cliente
            public_key_pem = b""
            while True:
                line = dis.readline().strip()
                if line == b'':  # Fin de la clave PEM
                    break
                public_key_pem += line + b'\n'
            print(f"Clave pública recibida del cliente: {public_key_pem.decode()}")

            client_public_key = serialization.load_pem_public_key(public_key_pem, backend=default_backend())

            # Generar una clave AES aleatoria
            aes_key = os.urandom(32)  # Clave de 256 bits

            # Cifrar la clave AES con la clave pública RSA del cliente
            encrypted_aes_key = client_public_key.encrypt(
                aes_key,
                asymmetric_padding.OAEP(
                    mgf=asymmetric_padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            # Enviar la clave AES cifrada al cliente (sin agregar newline)
            dos.write(encrypted_aes_key)
            dos.flush()
            print(f"Clave AES cifrada enviada al cliente: {encrypted_aes_key.hex()}")

            client_name = dis.readline().strip().decode()
            print(f"Nombre del cliente recibido: {client_name}")
            cliente = Cliente(client_name, dos, aes_key)
            clientes.append(cliente)

            threading.Thread(target=recibir_mensajes_cliente, args=(cliente, dis)).start()
        except Exception as e:
            print(f"Error al aceptar la conexión del cliente: {e}")

# Nueva función para descifrar usando AES GCM
def decrypt_message_aes_gcm(aes_key, nonce, encrypted_message, tag):
    decryptor = Cipher(algorithms.AES(aes_key), modes.GCM(nonce, tag), backend=default_backend()).decryptor()
    return decryptor.update(encrypted_message) + decryptor.finalize()

def recibir_mensajes_cliente(cliente, dis):
    while True:
        try:
            full_message = dis.readline().strip()
            if not full_message:
                raise ConnectionResetError("El cliente ha cerrado la conexión.")
            
            if full_message == b"SolicitarPendientes":
                enviar_mensajes_pendientes(cliente)
                continue

            nonce = full_message[:12]
            tag = full_message[12:28]
            encrypted_message = full_message[28:]
            
            print(f"Mensaje cifrado recibido: {encrypted_message.hex()}")
            decrypted_message = decrypt_message_aes_gcm(cliente.aes_key, nonce, encrypted_message, tag)
            decrypted_message = decrypted_message.decode('utf-8')

            print(f"Mensaje recibido desde el cliente ({cliente.nombre}): {decrypted_message}")

            if decrypted_message == "Terminar":
                actualizar_estado_cliente(cliente, False)
                break
            else:
                enviar_mensaje_otros_clientes(cliente, cliente.nombre, decrypted_message)
        except Exception as e:
            print(f"Error al recibir el mensaje del cliente: {e}")
            actualizar_estado_cliente(cliente, False)
            break

def enviar_mensaje_otros_clientes(sender_cliente, sender_name, message):
    for cliente in clientes:
        if cliente != sender_cliente:
            if cliente.conectado:
                try:
                    cliente.dos.write(f"{sender_name}: {message}\n".encode())
                    cliente.dos.flush()
                    print(f"Mensaje enviado a {cliente.nombre}: {message}")
                except Exception as e:
                    print(f"Error al enviar mensaje a {cliente.nombre}: {e}")
                    actualizar_estado_cliente(cliente, False)
            else:
                if cliente.nombre not in mensajes_pendientes:
                    mensajes_pendientes[cliente.nombre] = []
                mensajes_pendientes[cliente.nombre].append(f"{sender_name}: {message}")
                print(f"Mensaje almacenado para {cliente.nombre}: {message}")

def enviar_mensajes_pendientes(cliente):
    if cliente.nombre in mensajes_pendientes:
        for mensaje in mensajes_pendientes[cliente.nombre]:
            try:
                cliente.dos.write(f"{mensaje}\n".encode())
                cliente.dos.flush()
                print(f"Mensaje pendiente enviado a {cliente.nombre}: {mensaje}")
            except Exception as e:
                print(f"Error al enviar mensaje pendiente a {cliente.nombre}: {e}")
                actualizar_estado_cliente(cliente, False)
        del mensajes_pendientes[cliente.nombre]
        
def actualizar_estado_cliente(cliente, conectado):
    cliente.conectado = conectado

if __name__ == "__main__":
    iniciar_servidor()