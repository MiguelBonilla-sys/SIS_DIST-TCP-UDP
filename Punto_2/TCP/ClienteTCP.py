import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog, filedialog
import socket
import threading
import os

class ClienteTCP(tk.Tk):

    def __init__(self):
        super().__init__()

        # Configuración de la ventana
        self.title("Cliente TCP")
        self.geometry("600x500")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Declaración de variables para la conexión y comunicación con el servidor
        self.socket = None
        self.dis = None
        self.dos = None
        self.client_name = ""
        self.server_address = ""
        self.is_connected = False

        # Creación de componentes de la interfaz gráfica
        self.chat_area = scrolledtext.ScrolledText(self, state='disabled', wrap='word')
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        self.message_field = tk.Entry(self, font=('Arial', 14))
        self.message_field.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.X, expand=True)

        send_button = tk.Button(self, text="Enviar", command=self.send_message)
        send_button.pack(side=tk.RIGHT, padx=10, pady=10)

        self.message_status_indicator = tk.Label(self, text="", bg="gray", fg="white")
        self.message_status_indicator.pack(side=tk.BOTTOM, fill=tk.X)

        button_frame = tk.Frame(self)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        self.disconnect_button = tk.Button(button_frame, text="Desconectar", bg="red", command=self.disconnect_from_server)
        self.disconnect_button.pack(side=tk.LEFT, padx=5)

        self.reconnect_button = tk.Button(button_frame, text="Reconectar", bg="cyan", command=self.reconnect_to_server)
        self.reconnect_button.pack(side=tk.LEFT, padx=5)

        self.send_file_button = tk.Button(button_frame, text="Enviar Archivo", bg="green", command=self.send_file)
        self.send_file_button.pack(side=tk.LEFT, padx=5)

        # Conectar al servidor
        self.connect_to_server()

    # Método para conectar al servidor
    def connect_to_server(self):
        try:
            if self.socket:
                self.socket.close()
                self.is_connected = False

            # Solicitar dirección del servidor y nombre del cliente solo si no están definidos
            if not self.server_address:
                self.server_address = simpledialog.askstring("Conectar al servidor", "Dirección IP del servidor:")
            if not self.client_name:
                self.client_name = simpledialog.askstring("Conectar al servidor", "Nombre del cliente:")

            if self.server_address and self.client_name:
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.server_address, 5004))
                self.dis = self.socket.makefile('rb')
                self.dos = self.socket.makefile('wb')

                self.dos.write((self.client_name + '\n').encode())
                self.dos.flush()
                self.is_connected = True

                # Solicitar mensajes no entregados
                self.dos.write(b"RECUPERAR_MENSAJES\n")
                self.dos.flush()

                self.receive_messages_thread = threading.Thread(target=self.receive_messages)
                self.receive_messages_thread.daemon = True
                self.receive_messages_thread.start()
            else:
                self.show_error_and_exit("Conexión cancelada por el usuario.")
        except (socket.error, OSError) as e:
            self.show_error_and_exit("Error al reconectar con el servidor.")
            print(e)

    # Método para enviar mensajes al servidor
    def send_message(self):
        if not self.is_connected:
            messagebox.showerror("Error", "No estás conectado al servidor.")
            return

        message = self.message_field.get()
        self.show_message(f"{self.client_name}: {message}")
        self.update_message_status_indicator("Se está enviando")

        try:
            self.dos.write((message + '\n').encode())
            self.dos.flush()
            self.update_message_status_indicator("Enviado y recibido")
            if message.lower() == "terminar":
                self.terminate_connection()
        except (socket.error, OSError) as e:
            self.update_message_status_indicator("Se cerró el servidor")
            self.show_error_and_exit("Error 504: No se puede conectar con el servidor.")
            print(e)

        self.message_field.delete(0, tk.END)

    # Método para enviar archivos al servidor
    def send_file(self):
        if not self.is_connected:
            messagebox.showerror("Error", "No estás conectado al servidor.")
            return
    
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg")])
        if not file_path:
            return
    
        try:
            filename = os.path.basename(file_path)
            filesize = os.path.getsize(file_path)
            self.dos.write(f"ENVIAR_ARCHIVO {filename} {filesize}\n".encode())
            self.dos.flush()
    
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(1024)
                    if not data:
                        break
                    self.socket.sendall(data)
            self.show_message(f"Archivo enviado: {filename}")
        except (socket.error, OSError) as e:
            self.show_error_and_exit("Error al enviar el archivo.")
            print(e)

    # Método para recibir mensajes del servidor
    def receive_messages(self):
        try:
            while True:
                message = self.dis.readline().strip().decode()
                if message:
                    if message.startswith("NUEVO_ARCHIVO"):
                        _, filename = message.split()
                        self.show_message(f"Nuevo archivo disponible: {filename}")
                        self.solicitar_descarga_archivo(filename)
                    elif message.startswith("DESCARGAR_ARCHIVO"):
                        _, filename, filesize = message.split()
                        self.recibir_archivo(filename, int(filesize))
                    else:
                        self.show_message(message)
        except (socket.error, OSError):
            self.show_error_and_exit("Error 504: No se puede conectar con el servidor.")

    # Método para solicitar la descarga de un archivo
    def solicitar_descarga_archivo(self, filename):
        try:
            self.dos.write(f"DESCARGAR_ARCHIVO {filename}\n".encode())
            self.dos.flush()
        except (socket.error, OSError) as e:
            self.show_error_and_exit("Error al solicitar la descarga del archivo.")
            print(e)

    # Método para recibir un archivo del servidor
    def recibir_archivo(self, filename, filesize):
        try:
            with open(filename, 'wb') as f:
                while filesize > 0:
                    data = self.dis.read(min(filesize, 1024))
                    if not data:
                        break
                    f.write(data)
                    filesize -= len(data)
            self.show_message(f"Archivo descargado: {filename}")
        except (socket.error, OSError) as e:
            self.show_error_and_exit("Error al recibir el archivo.")
            print(e)

    # Método para desconectar del servidor
    def disconnect_from_server(self):
        try:
            if self.is_connected:
                self.dos.write(b"Desconectar\n")
                self.dos.flush()
                self.is_connected = False
                self.update_message_status_indicator("Desconectado")
        except (socket.error, OSError) as e:
            self.show_error_and_exit("Error al desconectar del servidor.")
            print(e)

    # Método para reconectar al servidor
    def reconnect_to_server(self):
        print("Intentando reconectar...")  # Línea de depuración
        if not self.is_connected:
            self.connect_to_server()

    # Método para terminar la conexión con el servidor
    def terminate_connection(self):
        try:
            self.dos.write(b"Terminar\n")
            self.dos.flush()
            self.socket.close()
            self.quit()
        except (socket.error, OSError) as e:
            self.show_error_and_exit("Error al terminar la conexión con el servidor.")
            print(e)

    # Método para mostrar mensajes en el área de chat
    def show_message(self, message):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, message + '\n')
        self.chat_area.config(state='disabled')

    # Método para mostrar errores y terminar la ejecución
    def show_error_and_exit(self, error_message):
        messagebox.showerror("Error", error_message)
        self.quit()

    # Método para actualizar el indicador de estado de los mensajes
    def update_message_status_indicator(self, status):
        if status == "Enviado y recibido":
            self.message_status_indicator.config(bg="green", text=status)
        elif status == "Se está enviando":
            self.message_status_indicator.config(bg="yellow", text=status)
        elif status == "Se cerró el servidor":
            self.message_status_indicator.config(bg="red", text=status)
        elif status == "Desconectado":
            self.message_status_indicator.config(bg="blue", text=status)

    # Método para cerrar la aplicación de forma correcta
    def on_closing(self):
        if messagebox.askokcancel("Salir", "¿Quieres salir?"):
            if self.is_connected:
                self.terminate_connection()
            self.quit()

# Método principal para iniciar la aplicación
if __name__ == "__main__":
    client_app = ClienteTCP()
    client_app.mainloop()