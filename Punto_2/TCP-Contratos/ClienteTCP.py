import tkinter as tk
from tkinter import messagebox, scrolledtext, simpledialog
import socket
import threading
from cryptography.hazmat.primitives.asymmetric import padding as asymmetric_padding
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.asymmetric import rsa
import os

class ClienteTCP(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Cliente TCP")
        self.geometry("600x500")
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        self.socket = None
        self.dis = None
        self.dos = None
        self.client_name = ""
        self.server_address = ""
        self.is_connected = False
        self.aes_key = None  # Clave AES

        # Generar el par de claves RSA (privada y pública) para el cliente
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        self.public_key = self.private_key.public_key()

        # Área de chat
        self.chat_area = scrolledtext.ScrolledText(self, state='disabled', wrap='word')
        self.chat_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        # Campo para ingresar mensajes
        self.message_field = tk.Entry(self, font=('Arial', 14))
        self.message_field.pack(side=tk.LEFT, padx=10, pady=10, fill=tk.X, expand=True)

        # Botón para enviar mensajes
        send_button = tk.Button(self, text="Enviar", command=self.send_message)
        send_button.pack(side=tk.RIGHT, padx=10, pady=10)

        # Indicador de estado de los mensajes
        self.message_status_indicator = tk.Label(self, text="", bg="gray", fg="white")
        self.message_status_indicator.pack(side=tk.BOTTOM, fill=tk.X)

        # Botones para desconectar y reconectar
        button_frame = tk.Frame(self)
        button_frame.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=10)

        self.disconnect_button = tk.Button(button_frame, text="Desconectar", bg="red", command=self.disconnect_from_server)
        self.disconnect_button.pack(side=tk.LEFT, padx=5)

        self.reconnect_button = tk.Button(button_frame, text="Reconectar", bg="cyan", command=self.reconnect_to_server)
        self.reconnect_button.pack(side=tk.LEFT, padx=5)

        self.server_public_key = None

        # Conectar al servidor al iniciar la aplicación
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
                print(f"Conectando al servidor {self.server_address} como {self.client_name}")
                self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.socket.connect((self.server_address, 5004))
                self.dis = self.socket.makefile('rb')
                self.dos = self.socket.makefile('wb')
    
                # Enviar la clave pública del cliente al servidor
                public_key_pem = self.public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                )
                self.dos.write(public_key_pem + b'\n')
                self.dos.flush()
                print("Clave pública enviada al servidor")
    
                # Recibir la clave AES cifrada y descifrarla con la clave privada del cliente
                encrypted_aes_key = self.dis.read(256)  # Leer exactamente 256 bytes
                print(f"Clave AES cifrada recibida: {encrypted_aes_key.hex()}")
                self.aes_key = self.private_key.decrypt(
                    encrypted_aes_key,
                    asymmetric_padding.OAEP(
                        mgf=asymmetric_padding.MGF1(algorithm=hashes.SHA256()),
                        algorithm=hashes.SHA256(),
                        label=None
                    )
                )
                print(f"Clave AES descifrada: {self.aes_key.hex()}")
    
                self.dos.write((self.client_name + '\n').encode())
                self.dos.flush()
                self.is_connected = True
                print("Nombre del cliente enviado al servidor")
    
                # Crear un hilo para recibir mensajes
                self.receive_messages_thread = threading.Thread(target=self.receive_messages)
                self.receive_messages_thread.daemon = True
                self.receive_messages_thread.start()
            else:
                self.show_error_and_exit("Conexión cancelada por el usuario.")
        except (socket.error, OSError) as e:
            print(f"Error al conectar con el servidor: {e}")
            self.show_error_and_exit("Error al reconectar con el servidor.")

    # Método para enviar mensajes
    def send_message(self):
        if not self.is_connected:
            messagebox.showerror("Error", "No estás conectado al servidor.")
            return

        message = self.message_field.get().encode('utf-8')
        self.show_message(f"{self.client_name}: {message.decode()}")

        nonce, encrypted_message, tag = self.encrypt_message_aes_gcm(self.aes_key, message)
        print(f"Mensaje cifrado: {encrypted_message.hex()}")

        try:
            self.dos.write(nonce + tag + encrypted_message + b'\n')
            self.dos.flush()
            print(f"Mensaje enviado: {nonce.hex()} {tag.hex()} {encrypted_message.hex()}")
            if message.lower() == b"terminar":
                self.terminate_connection()
        except (socket.error, OSError) as e:
            print(f"Error al enviar el mensaje: {e}")
            self.show_error_and_exit("Error 504: No se puede conectar con el servidor.")

        self.message_field.delete(0, tk.END)

    # Método para recibir mensajes del servidor
    def receive_messages(self):
        try:
            while True:
                message = self.dis.readline().strip().decode()
                if message:
                    print(f"Mensaje recibido del servidor: {message}")
                    self.show_message(message)
        except (socket.error, OSError) as e:
            print(f"Error al recibir el mensaje: {e}")
            self.show_error_and_exit("Error 504: No se puede conectar con el servidor.")

    def encrypt_message_aes_gcm(self, aes_key, message):
        nonce = os.urandom(12)  # Nonce de 12 bytes para GCM
        cipher = Cipher(algorithms.AES(aes_key), modes.GCM(nonce), backend=default_backend())
        encryptor = cipher.encryptor()
        encrypted_message = encryptor.update(message) + encryptor.finalize()
        return nonce, encrypted_message, encryptor.tag

    def disconnect_from_server(self):
        try:
            if self.is_connected:
                self.dos.write(b"Desconectar\n")
                self.dos.flush()
                self.socket.close()
                self.is_connected = False
                print("Desconectado del servidor")
        except (socket.error, OSError) as e:
            print(f"Error al desconectar del servidor: {e}")
            self.show_error_and_exit("Error al desconectar del servidor.")

    def reconnect_to_server(self):
        if not self.is_connected:
            self.connect_to_server()
            if self.is_connected:
                self.receive_messages_thread = threading.Thread(target=self.receive_messages)
                self.receive_messages_thread.daemon = True
                self.receive_messages_thread.start()
                self.request_pending_messages()
            
    def request_pending_messages(self):
        try:
            self.dos.write(b"SolicitarPendientes\n")
            self.dos.flush()
            print("Solicitud de mensajes pendientes enviada al servidor")
        except (socket.error, OSError) as e:
            print(f"Error al solicitar mensajes pendientes: {e}")
            self.show_error_and_exit("Error al solicitar mensajes pendientes.")

    def terminate_connection(self):
        try:
            self.dos.write(b"Terminar\n")
            self.dos.flush()
            self.socket.close()
            self.quit()
            print("Conexión terminada con el servidor")
        except (socket.error, OSError) as e:
            print(f"Error al terminar la conexión: {e}")
            self.show_error_and_exit("Error al terminar la conexión con el servidor.")

    def show_message(self, message):
        self.chat_area.config(state='normal')
        self.chat_area.insert(tk.END, message + '\n')
        self.chat_area.config(state='disabled')

    def show_error_and_exit(self, error_message):
        messagebox.showerror("Error", error_message)
        self.quit()

    def on_closing(self):
        if messagebox.askokcancel("Salir", "¿Quieres salir?"):
            if self.is_connected:
                self.terminate_connection()
            self.quit()

if __name__ == "__main__":
    client_app = ClienteTCP()
    client_app.mainloop()