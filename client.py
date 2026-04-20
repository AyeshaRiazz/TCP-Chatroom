from tkinter import *
from tkinter import messagebox
from socket import *
import threading
import os
import subprocess

# Create the socket and connect to the server
client_socket = socket(AF_INET, SOCK_STREAM)
username = input("Enter your name: ")
server_host = 'localhost'
server_port = 5671

client_socket.connect((server_host, server_port))

def open_file(file_path):
    """
    Open the file using the default application based on its extension.
    """
    try:
        if os.name == 'nt':  # Windows
            os.startfile(file_path)
        elif os.name == 'posix':  # macOS/Linux
            subprocess.call(('xdg-open', file_path))
    except Exception as e:
        messagebox.showerror("Error", f"Cannot open file: {e}")

def receive_message():
    """
    Receive messages from the server, including chat messages or updates.
    """
    while True:
        try:
            message = client_socket.recv(1024).decode('ascii')

            if message.startswith("CLIENTS:"):
                # Update connected clients list
                client_list = message.split(':')[1]
                clients = client_list.split(',')  # Split by comma to display each client on a new line

                connected_clients.config(state=NORMAL)
                connected_clients.delete(1.0, END)  # Clear existing list
                for client in clients:
                    connected_clients.insert(END, f"{client.strip()}\n")  # Insert each client on a new line
                connected_clients.config(state=DISABLED)

            elif message.startswith("FILE:"):
                # Handle file transfer
                file_info = message.split(":")
                file_name = file_info[1]
                file_size = int(file_info[2])
                file_data = client_socket.recv(file_size)
                file_path = os.path.join(os.getcwd(), file_name)
                with open(file_path, "wb") as f:
                    f.write(file_data)

                chatlog.config(state=NORMAL)
                chatlog.insert(END, f"[SYSTEM]: You received a file: {file_name}\n", "left")
                chatlog.config(state=DISABLED)
                chatlog.yview(END)

                if messagebox.askyesno("File Received", f"Do you want to open {file_name}?"):
                    open_file(file_path)
            else:
                # Display chat messages from other users
                chatlog.config(state=NORMAL)
                chatlog.insert(END, f"{message}\n", "left")
                chatlog.config(state=DISABLED)
                chatlog.yview(END)

        except Exception as e:
            print("Error in receiving message:", e)
            break

def send_message(event=None):
    """
    Send a message to the server when the Enter key is pressed or the send button is clicked.
    """
    msg = message_entry.get()
    if msg:
        client_socket.send(msg.encode('ascii'))  # Send message to the server
        
        # Display the sent message in the local chat log
        chatlog.config(state=NORMAL)
        chatlog.insert(END, f"You: {msg}\n", "right")
        chatlog.config(state=DISABLED)
        chatlog.yview(END)

        message_entry.delete(0, END)

def client_gui():
    """
    Create and display the GUI for the chatroom client.
    """
    global chatlog, message_entry, connected_clients
    gui = Tk()
    gui.title(f"Chatroom - {username}")
    gui.geometry("800x500")
    gui.config(bg="#ECEEF4")


    # Header Frame
    # header_frame = Frame(gui, bg="#39508A", pady=15)
    # header_frame.pack(fill=X)

    header_label = Label(gui, text=f"{username}'s Chatroom", bg="#39508A", fg="white", font=("Arial", 20, "bold"), pady=15)
    # header_label = Label(header_frame, text=f"{username}'s Chatroom", bg="#39508A", fg="white", font=("Arial", 20, "bold"))
    header_label.pack(fill=X, padx=40, pady=(30, 0))
    # header_label.pack()


    # Left Frame (Chat Area)
    left_frame = Frame(gui, bg="#BFD0E7")
    left_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(40,0), pady=10)
    chatlog = Text(left_frame, bg="#ECEEF4", fg="black", padx=25, pady=20, font=("Arial", 12), wrap=WORD)
    chatlog.pack(fill=BOTH, expand=True, padx=30, pady=(30, 10))
    chatlog.config(state=DISABLED)
    chatlog.tag_configure("left", justify="left")
    chatlog.tag_configure("right", justify="right")

    # Message Entry Frame
    message_frame = Frame(left_frame, bg="#F0F1F6")
    message_frame.pack(fill=X, padx=30, pady=(8, 30))
    message_entry = Entry(message_frame, bg="#F0F1F6", fg="black", bd=0, font=("Arial", 12), width=80)
    message_entry.pack(side=LEFT, fill=X, expand=True, padx=(25, 8))
    message_entry.bind("<Return>", send_message)
    send_button = Button(message_frame, text="Send", command=send_message, bg="#39508A", bd=0, fg="white", font=("Arial", 14, "bold"), padx=30, pady=10)
    send_button.pack(side=RIGHT)

    # Right Frame (Connected Clients Area)
    right_frame = Frame(gui, bg="#BFD0E7", width=150)
    right_frame.pack(side=RIGHT, fill=Y, padx=40, pady=10)
    Label(right_frame, text="Connected Clients", bg="#BFD0E7", fg="black", font=("Arial", 14, "bold")).pack(pady=10)
    connected_clients = Text(right_frame, bg="#F0F1F6", fg="black", bd=0, padx=10, pady=25,  font=("Arial", 12), wrap=WORD, state=DISABLED, height=50)
    connected_clients.pack(fill=BOTH, expand=False, padx=30, pady=25)

    # Start receiving messages
    threading.Thread(target=receive_message, daemon=True).start()

    # Send username to the server
    client_socket.send(username.encode('ascii'))

    # Run the GUI
    gui.mainloop()

if __name__ == "__main__":
    client_gui()
