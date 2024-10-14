import socket

def main():
    # Arreglo de bytes para almacenar los datos recibidos
    buffer = bytearray(1024)

    # StringBuilder para concatenar los mensajes recibidos
    received_messages = []  # Usaremos una lista para almacenar los mensajes recibidos

    # Contador para contar los mensajes recibidos
    message_count = 0

    try:
        # Imprime un mensaje indicando que el servidor UDP ha iniciado
        print("Servidor UDP iniciado")

        # Indica que el servidor está esperando a un cliente
        print("En espera de un cliente")

        # Creación del socket UDP en el puerto 9107
        socket_udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_udp.bind(('0.0.0.0', 9107))

        # Bucle para atender siempre las peticiones entrantes
        while True:
            # Construcción del DatagramPacket para recibir peticiones
            data, address = socket_udp.recvfrom(1024)

            # Muestra información sobre el cliente que envía el mensaje
            print(f"Recibo la información de un cliente")
            print(f"IP origen: {address[0]}")
            print(f"Puerto origen: {address[1]}")

            # Convertimos los datos recibidos a una cadena de texto
            message = data.decode('utf-8').strip()

            # Añadimos el mensaje recibido a la lista
            received_messages.append(message)
            print(f"Mensaje: {message}")

            # Incrementamos el contador de mensajes recibidos
            message_count += 1

            # Si se han recibido 5 mensajes, salimos del bucle
            if message_count >= 5:
                break

            # Muestra un mensaje indicando que el servidor está esperando a un cliente
            print("Servidor UDP en espera de un cliente\n")

        # Imprime todos los mensajes recibidos después de haberlos recibido todos
        print(f"Mensajes recibidos: {' '.join(received_messages)}")

    except socket.error as e:
        # Captura y maneja la excepción de socket.error, en caso de que ocurra al crear el socket o recibir el datagrama
        print(f"Error en el socket: {e}")

if __name__ == "__main__":
    main()
