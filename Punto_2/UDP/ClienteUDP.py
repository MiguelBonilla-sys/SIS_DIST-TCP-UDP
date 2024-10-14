import tkinter as tk
from tkinter import messagebox
import socket

class ClienteUDP(tk.Tk):

    def __init__(self):
        super().__init__()

        # Configuración de la ventana
        self.title("Cliente UDP")
        self.geometry("400x300")
        self.configure(bg="#add8e6")  # Light blue background

        # Declaración de campos de la GUI y variables relacionadas con el socket UDP
        self.nombreField = tk.Entry(self)
        self.codigoField = tk.Entry(self)
        self.edadField = tk.Entry(self)
        self.semestreField = tk.Entry(self)
        self.ciudadField = tk.Entry(self)

        self.enviarButton = tk.Button(self, text="Enviar", command=self.enviar_datos, bg="#4682b4", fg="white")
        self.limpiarButton = tk.Button(self, text="Limpiar", command=self.limpiar_campos, bg="#4682b4", fg="white")

        # Diseño de la ventana con grid
        self.create_widgets()

        # Inicialización del socket UDP y obtención de la dirección del servidor
        try:
            self.miSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.host = "192.168.1.11"
            self.puertoServidor = 9107
        except socket.error as e:
            self.show_error_dialog(f"Error al crear el socket: {e}")

    # Método para crear los widgets y layout
    def create_widgets(self):
        label_font = ("Arial", 14, "bold")
        button_font = ("Arial", 14)

        tk.Label(self, text="Nombre del estudiante:", font=label_font, bg="#add8e6").grid(row=0, column=0, padx=10, pady=5, sticky="e")
        self.nombreField.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(self, text="Código:", font=label_font, bg="#add8e6").grid(row=1, column=0, padx=10, pady=5, sticky="e")
        self.codigoField.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(self, text="Edad:", font=label_font, bg="#add8e6").grid(row=2, column=0, padx=10, pady=5, sticky="e")
        self.edadField.grid(row=2, column=1, padx=10, pady=5)

        tk.Label(self, text="Semestre:", font=label_font, bg="#add8e6").grid(row=3, column=0, padx=10, pady=5, sticky="e")
        self.semestreField.grid(row=3, column=1, padx=10, pady=5)

        tk.Label(self, text="Ciudad de residencia:", font=label_font, bg="#add8e6").grid(row=4, column=0, padx=10, pady=5, sticky="e")
        self.ciudadField.grid(row=4, column=1, padx=10, pady=5)

        # Espacio vacío
        tk.Label(self, text="", bg="#add8e6").grid(row=5, column=0)
        tk.Label(self, text="", bg="#add8e6").grid(row=5, column=1)

        # Botones
        self.enviarButton.config(font=button_font)
        self.enviarButton.grid(row=6, column=0, padx=10, pady=5, sticky="e")

        self.limpiarButton.config(font=button_font)
        self.limpiarButton.grid(row=6, column=1, padx=10, pady=5, sticky="w")

    # Método para enviar datos al servidor
    def enviar_datos(self):
        try:
            # Construcción del mensaje con los datos del estudiante
            mensaje = f"{self.nombreField.get()};{self.codigoField.get()};{self.edadField.get()};{self.semestreField.get()};{self.ciudadField.get()}"
            buffer = mensaje.encode()

            # Creación y envío del paquete UDP
            self.miSocket.sendto(buffer, (self.host, self.puertoServidor))

            messagebox.showinfo("Éxito", "Datagrama enviado con éxito!")
        except socket.error as e:
            self.show_error_dialog(f"Error al enviar el datagrama: {e}")

    # Método para limpiar los campos de texto
    def limpiar_campos(self):
        self.nombreField.delete(0, tk.END)
        self.codigoField.delete(0, tk.END)
        self.edadField.delete(0, tk.END)
        self.semestreField.delete(0, tk.END)
        self.ciudadField.delete(0, tk.END)

    # Método para mostrar un mensaje de error en un cuadro de diálogo
    def show_error_dialog(self, errorMessage):
        messagebox.showerror("Error", errorMessage)

# Método principal que inicia la aplicación
if __name__ == "__main__":
    app = ClienteUDP()
    app.mainloop()
