import socket
import threading
import os

# Clase interna para representar a un cliente
class Cliente:
    def __init__(self, nombre, dos):
        self.nombre = nombre
        self.dos = dos
        self.conectado = True
        self.mensajes_pendientes = []

# Clase interna para representar un mensaje
class Mensaje:
    def __init__(self, nombre_cliente, contenido):
        self.nombre_cliente = nombre_cliente
        self.contenido = contenido

# Listas para almacenar los clientes y los mensajes
clientes = []
mensajes = []

# Constante para el nombre del archivo de clientes
CLIENTS_FILE = "clientes.txt"

# Método principal del servidor
def iniciar_servidor():
    # Creación del socket del servidor en el puerto 5004
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('0.0.0.0', 5004))
    server_socket.listen()

    print("Iniciando el servidor...")
    while True:
        print("Servidor iniciado, esperando clientes...")

        # Aceptación de una conexión de un cliente
        client_socket, addr = server_socket.accept()

        # Creación de los streams de entrada y salida
        dis = client_socket.makefile('rb')
        dos = client_socket.makefile('wb')

        # Lectura del nombre del cliente
        client_name = dis.readline().strip().decode()
        cliente = Cliente(client_name, dos)
        clientes.append(cliente)

        # Envío de mensajes pendientes al cliente reconectado
        enviar_mensajes_pendientes(cliente)

        # Creación y ejecución del hilo para recibir mensajes del cliente
        threading.Thread(target=recibir_mensajes_cliente, args=(cliente, dis, dos)).start()

# Método para recibir mensajes del cliente
def recibir_mensajes_cliente(cliente, dis, dos):
    while True:
        try:
            client_message = dis.readline().strip().decode()
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
                recibir_archivo(cliente, dis, client_message)
            elif client_message.startswith("DESCARGAR_ARCHIVO"):
                enviar_archivo(cliente, client_message)
            else:
                mensajes.append(Mensaje(cliente.nombre, client_message))
                enviar_mensaje_otros_clientes(cliente, cliente.nombre, client_message)
        except Exception as e:
            print(f"Error al recibir el mensaje del cliente: {e}")
            actualizar_estado_cliente(cliente, False)
            break

# Método para recibir archivos del cliente
def recibir_archivo(cliente, dis, client_message):
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

# Método para enviar archivos al cliente
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

# Método para notificar a los clientes sobre un nuevo archivo
def notificar_nuevo_archivo(filename):
    for cliente in clientes:
        if cliente.conectado:
            try:
                cliente.dos.write(f"NUEVO_ARCHIVO {filename}\n".encode())
                cliente.dos.flush()
            except Exception as e:
                print(f"Error al notificar al cliente sobre el nuevo archivo: {e}")

# Método para actualizar el estado de conexión de un cliente
def actualizar_estado_cliente(cliente, conectado):
    cliente.conectado = conectado

# Método para enviar los mensajes pendientes a un cliente
def enviar_mensajes_pendientes(cliente):
    for mensaje in cliente.mensajes_pendientes:
        try:
            cliente.dos.write(f"{mensaje}\n".encode())
            cliente.dos.flush()
        except Exception as e:
            print(f"Error al enviar el mensaje al cliente: {e}")
    cliente.mensajes_pendientes.clear()

# Método para enviar un mensaje a los otros clientes
def enviar_mensaje_otros_clientes(sender_cliente, sender_name, message):
    for cliente in clientes:
        if cliente != sender_cliente:
            if cliente.conectado:
                enviar_mensaje(cliente, Mensaje(sender_name, message))
            else:
                cliente.mensajes_pendientes.append(f"{sender_name}: {message}")

# Método para enviar un mensaje a un cliente
def enviar_mensaje(cliente, mensaje):
    try:
        cliente.dos.write(f"{mensaje.nombre_cliente}: {mensaje.contenido}\n".encode())
        cliente.dos.flush()
        mensaje.enviado = True
    except Exception as e:
        print(f"Error al enviar el mensaje al cliente: {e}")

# Iniciar el servidor
if __name__ == "__main__":
    iniciar_servidor()