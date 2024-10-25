import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog, filedialog
import socket
import threading
import os
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding

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

        # Generar par de claves RSA
        self.private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        self.public_key = self.private_key.public_key()

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

    def connect_to_server(self):
        try:
            if self.socket:
                self.socket.close()
                self.is_connected = False

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

                # Enviar clave pública al servidor
                public_pem = self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                self.dos.write(public_pem + b'\n')
                self.dos.flush()

                # Recibir clave pública del servidor
                server_public_pem = self.dis.readline().strip()
                self.server_public_key = serialization.load_pem_public_key(server_public_pem)

                self.is_connected = True

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

    def send_message(self):
        if not self.is_connected:
            messagebox.showerror("Error", "No estás conectado al servidor.")
            return

        message = self.message_field.get()
        self.show_message(f"{self.client_name}: {message}")
        self.update_message_status_indicator("Se está enviando")

        try:
            encrypted_message = self.server_public_key.encrypt(
                message.encode(),
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            self.dos.write(encrypted_message + b'\n')
            self.dos.flush()
            self.update_message_status_indicator("Enviado y recibido")
            if message.lower() == "terminar":
                self.terminate_connection()
        except (socket.error, OSError) as e:
            self.update_message_status_indicator("Se cerró el servidor")
            self.show_error_and_exit("Error 504: No se puede conectar con el servidor.")
            print(e)

        self.message_field.delete(0, tk.END)

    def receive_messages(self):
        try:
            while True:
                encrypted_message = self.dis.readline().strip()
                if encrypted_message:
                    decrypted_message = self.private_key.decrypt(
                        encrypted_message,
                        padding.OAEP(
                            mgf=padding.MGF1(algorithm=hashes.SHA256()),
                            algorithm=hashes.SHA256(),
                            label=None
                        )
                    )
                    self.show_message(decrypted_message.decode())
        except (socket.error, OSError):
            self.show_error_and_exit("Error 504: No se puede conectar con el servidor.")

    # Otros métodos (send_file, disconnect_from_server, reconnect_to_server, terminate_connection, show_message, show_error_and_exit, update_message_status_indicator, on_closing) permanecen igual

if __name__ == "__main__":
    client_app = ClienteTCP()
    client_app.mainloop()