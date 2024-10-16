# Taller de Sockets en Python

Este proyecto contiene ejemplos y ejercicios de implementación de sockets en Python para sistemas distribuidos, incluyendo conexiones TCP y UDP para la comunicación entre cliente y servidor.

## Autores

- Javier Mauricio Plata Párraga
- Juan Sebastián Fandiño Novoa
- Johan Camilo Mesa Ríos
- Miguel Angel Bonilla Torres

## Contenido del Taller

- **Dns.py**: Realiza una consulta DNS inversa utilizando los módulos `socket` y `sys` para obtener el nombre del host, alias y direcciones IP asociadas a una dirección IP.

- **Gethostname.py**: Usa el módulo `socket` de Python para obtener el nombre del host y su dirección IP.

- **Ip_address.py**: Utiliza el módulo `ipaddress` para manejar una dirección IP, proporcionando información detallada sobre ella.

### Ejercicios de Cliente-Servidor

El taller incluye varios ejemplos de comunicación entre cliente y servidor utilizando sockets TCP y UDP:

#### TCP

- **TCP Calculadora**: 
  - Cliente (`client_calc.py`): Envío de dos números y una operación aritmética al servidor.
  - Servidor (`server_calc.py`): Recepción de datos, realización de la operación (suma o resta) y envío del resultado al cliente.

- **TCP Echo**: 
  - Cliente (`client_echo.py`): Conexión al servidor y envío de un mensaje, esperando una respuesta de "eco".
  - Servidor (`server_echo.py`): Recibe el mensaje del cliente y lo devuelve como respuesta.

#### UDP

- **UDP Calculadora**:
  - Cliente (`client_calc.py`): Envío de dos números y una operación al servidor mediante el protocolo UDP.
  - Servidor (`server_calc.py`): Recepción de datos, realización de la operación (suma o resta) y envío del resultado al cliente.

#### Servidor Concurrente

- **Servidor Concurrente (`server_calc_conc.py`)**: Utiliza el protocolo TCP para manejar múltiples conexiones con clientes de manera concurrente mediante hilos, permitiendo atender múltiples solicitudes simultáneamente.

## Resumen del Código TCP y UDP

### Cliente y Servidor TCP

- **ClienteTCP.py**: Implementa un cliente para un chat TCP utilizando Python y la librería Tkinter para la interfaz gráfica. Permite enviar mensajes y archivos al servidor, gestionar la conexión y reconexión, y recibir mensajes de otros clientes conectados.
  - **Conectar al Servidor**: El método `connect_to_server` establece la conexión con el servidor y crea un hilo para recibir mensajes entrantes sin bloquear la interfaz gráfica.
  - **Envío de Mensajes y Archivos**: Los métodos `send_message` y `send_file` permiten al cliente enviar mensajes y archivos al servidor, respectivamente.
  - **Recepción de Mensajes**: El método `receive_messages` escucha mensajes del servidor y los muestra en la interfaz gráfica.

- **ServidorTCP.py**: Define un servidor TCP que gestiona múltiples clientes, retransmitiendo mensajes y archivos entre ellos y almacenando mensajes para clientes desconectados.
  - **Manejo de Clientes**: Cada cliente es manejado mediante un hilo para asegurar una comunicación simultánea sin bloqueos.
  - **Mensajes Pendientes**: El servidor almacena los mensajes para los clientes desconectados y los envía cuando se reconectan.
  - **Envío y Recepción de Archivos**: Los métodos `recibir_archivo` y `enviar_archivo` permiten manejar la transferencia de archivos entre el servidor y los clientes.

### Cliente y Servidor UDP

- **ClienteUDP.py**: Implementa un cliente para un chat UDP utilizando Tkinter. Permite enviar información al servidor y cuenta con una interfaz gráfica para facilitar la entrada de datos.
  - **Configuración del Socket**: El cliente crea un socket UDP para enviar los datos ingresados por el usuario al servidor.
  - **Envío de Datos**: El método `enviar_datos` se encarga de construir y enviar un datagrama al servidor con los datos ingresados.

- **ServidorUDP.py**: Define un servidor UDP que escucha mensajes de los clientes y los muestra en la consola, permitiendo un seguimiento de los datos enviados.
  - **Recepción de Mensajes**: El servidor recibe los mensajes y muestra la dirección del cliente junto con el contenido del mensaje.
  - **Contador de Mensajes**: El servidor cuenta cuántos mensajes ha recibido y termina después de un número fijo de mensajes.



## Explicaciones y Conceptos Clave

- **Manejo de Direcciones**: Uso de DNS y funciones de socket para obtener información sobre hosts y direcciones IP.
- **Sockets TCP y UDP**: Ejemplos básicos de comunicación cliente-servidor utilizando estos dos protocolos, con explicación de sus diferencias.
- **Concurrencia en Servidores**: Implementación de un servidor concurrente utilizando hilos para manejar múltiples clientes de forma eficiente.
