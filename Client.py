import threading
from socket import *
from customtkinter import *


class LoginWindow(CTk):
    def __init__(self):
        super().__init__()
        self.geometry("300x200")
        self.title("Login to Bombachat")

        self.username_entry = CTkEntry(self, placeholder_text="Username")
        self.username_entry.pack(pady=10)

        self.password_entry = CTkEntry(self, placeholder_text="Password", show="*")
        self.password_entry.pack(pady=10)

        self.status_label = CTkLabel(self, text="")
        self.status_label.pack(pady=5)

        self.login_button = CTkButton(self, text="Login", command=self.attempt_login)
        self.login_button.pack(pady=10)

        self.sock = socket(AF_INET, SOCK_STREAM)

    def attempt_login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            self.status_label.configure(text="Будь ласка уведи оба поля.")
            return

        try:
            self.sock.connect(('localhost', 8080))
            auth_data = f"AUTH@{username}@{password}\n"
            self.sock.sendall(auth_data.encode())

            response = self.sock.recv(1024).decode().strip()
            if response == "AUTH_OK":
                self.destroy()
                MainWindow(username, self.sock).mainloop()
            else:
                self.status_label.configure(text="Логін провалено.")
                self.sock.close()
                self.sock = socket(AF_INET, SOCK_STREAM)  # Reset socket for retry
        except Exception as e:
            self.status_label.configure(text=f"Помилка з підключенням{e}")


class MainWindow(CTk):
    def __init__(self, username, sock):
        super().__init__()
        self.geometry('500x400')
        self.title("Bombachat")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.username = username
        self.sock = sock

        self.create_widgets()
        self.connected = True
        threading.Thread(target=self.recv_message, daemon=True).start()

    def create_widgets(self):
        self.chat_field = CTkTextbox(self, font=('Arial', 14), state='disabled')
        self.chat_field.pack(padx=10, pady=10, fill='both', expand=True)

        frame = CTkFrame(self)
        frame.pack(padx=10, pady=5, fill='x')

        self.message_entry = CTkEntry(frame, placeholder_text='Введіть повідомлення:')
        self.message_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.message_entry.bind('<Return>', lambda event: self.send_message())

        self.send_button = CTkButton(frame, text='Надіслати', command=self.send_message)
        self.send_button.pack(side='right')

    def add_message(self, text):
        def update_gui():
            self.chat_field.configure(state='normal')
            self.chat_field.insert(END, text + '\n')
            self.chat_field.configure(state='disabled')
            self.chat_field.see(END)

        self.after(0, update_gui)

    def send_message(self):
        message = self.message_entry.get().strip()
        if message:
            self.add_message(f"Я: {message}")
            data = f"TEXT@{self.username}@{message}\n"
            try:
                self.sock.sendall(data.encode())
            except:
                self.add_message("[Система] Не вдалося надіслати повідомлення.")
            self.message_entry.delete(0, END)
            self.message_entry.focus()

    def recv_message(self):
        buffer = ""
        while self.connected:
            try:
                chunk = self.sock.recv(4096)
                if not chunk:
                    break
                buffer += chunk.decode()
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    self.handle_line(line.strip())
            except:
                self.add_message("[Система] З'єднання втрачено.")
                break
        self.sock.close()

    def handle_line(self, line):
        parts = line.split("@", 2)
        if len(parts) >= 3 and parts[0] == "TEXT":
            author = parts[1]
            message = parts[2]
            if author != self.username:
                self.add_message(f"{author}: {message}")

    def on_close(self):
        self.connected = False
        try:
            self.sock.close()
        except:
            pass
        self.destroy()


if __name__ == "__main__":
    app = LoginWindow()
    app.mainloop()
