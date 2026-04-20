from tkinter import *
from socket import *
import _thread
from tkinter.filedialog import askopenfilename

clients = []  # List of connected clients
client_names = {}  # Map sockets to usernames
client_chats = {}  # Dictionary to store client chats

def broadcast(message, sender=None, send_client_list=False, file_data=None):
    """
    Broadcast messages to all connected clients.
    If `send_client_list` is True, the message contains the updated client list.
    """
    for client in clients:
        try:
            if send_client_list:
                # Send updated client list
                client_list = ",".join(client_names.values())
                client.send(f"CLIENTS:{client_list}".encode('ascii'))
            else:
                # Send chat message or file
                if file_data:
                    # Send file data to the client
                    client.send(f"FILE:{file_data[0]}:{file_data[1]}".encode('ascii'))
                else:
                    # Send chat message
                    if client != sender:
                        client.send(message.encode('ascii'))
        except:
            clients.remove(client)

def handle_client(client):
    """
    Handle messages from a specific client.
    """
    while True:
        try:
            message = client.recv(1024).decode('ascii')
            if message:
                # Check for file message
                if message.startswith("FILE:"):
                    file_info = message.split(":")
                    file_name = file_info[1]
                    file_size = int(file_info[2])

                    # Receive the actual file
                    file_data = client.recv(file_size)
                    with open(file_name, "wb") as f:
                        f.write(file_data)
                    broadcast(f"{client_names[client]} has shared a file: {file_name}")
                else:
                    broadcast(f"{client_names[client]}: {message}", sender=client)

                if client not in client_chats:
                    client_chats[client] = []
                client_chats[client].append(f"{client_names[client]}: {message}")
                
        except:
            # Handle client disconnection
            client_name = client_names[client]
            clients.remove(client)
            del client_names[client]
            broadcast(f"{client_name} has left the chat.")
            broadcast("", send_client_list=True)
            update_client_list()  # Update the client list in the server GUI
            client.close()
            break

def accept_connections():
    """
    Accept incoming client connections.
    """
    while True:
        client, addr = server_socket.accept()
        print(f"Connection established with {addr}")
        update_server_chat(f"Connection established with {addr}", is_connection_message=True)

        # Get the client's username
        username = client.recv(1024).decode('ascii')
        clients.append(client)
        client_names[client] = username

        # Notify everyone about the new client
        broadcast(f"{username} has joined the chat.")
        broadcast("", send_client_list=True)

        # Update the client list in the server GUI
        update_client_list()

        # Start a thread to handle the new client
        _thread.start_new_thread(handle_client, (client,))

def update_server_chat(message, is_connection_message=False):
    """
    Update the server's chat log with the received message.
    """
    chatlog.config(state=NORMAL)
    
    # Only show connection messages in the left side chat log
    if is_connection_message:
        chatlog.insert(END, f"[SYSTEM]: {message}\n")
    chatlog.config(state=DISABLED)
    chatlog.yview(END)

def send_server_message():
    """
    Send a message from the server to all clients.
    """
    global server_textbox
    msg = server_textbox.get("0.0", END).strip()
    if msg:
        broadcast(f"SERVER: {msg}")
        update_server_chat(f"SERVER: {msg}")
        server_textbox.delete("0.0", END)

def update_client_list():
    """
    Update the list of clients in the right panel.
    """
    global clients_listbox
    clients_listbox.delete(0, END)
    for client_name in client_names.values():
        clients_listbox.insert(END, client_name)

def select_file():
    """
    Opens a file dialog to select a file and broadcasts it to all clients.
    """
    file_path = askopenfilename()
    if file_path:
        file_name = file_path.split("/")[-1]
        with open(file_path, "rb") as file:
            file_data = file.read()
        
        # Broadcast the file to clients
        for client in clients:
            # Send file metadata
            file_size = len(file_data)
            client.send(f"FILE:{file_name}:{file_size}".encode('ascii'))
            client.send(file_data)

        broadcast(f"SERVER has shared a file: {file_name}")

def monitor_chats():
    """
    Monitor chats from all clients and display them in the server's GUI.
    """
    monitor_window = Toplevel()  # Open a new window to display the chat logs
    monitor_window.title("Monitor Client Chats")

    # Text box to display all client chats
    monitor_chatlog = Text(monitor_window, bg="#CDE1D9", fg="black", font=("Arial", 12), wrap=WORD)
    monitor_chatlog.pack(fill=BOTH, expand=True, padx=5, pady=5)
    monitor_chatlog.config(state=DISABLED)

    # Loop through client chats and display
    for client, chat_messages in client_chats.items():
        for message in chat_messages:
            monitor_chatlog.config(state=NORMAL)
            monitor_chatlog.insert(END, message + "\n")
            monitor_chatlog.config(state=DISABLED)

    monitor_window.mainloop()

# GUI Function
def server_gui():
    global chatlog, server_textbox, clients_listbox

    # Initialize GUI
    gui = Tk()
    gui.title("Chatroom Server")
    gui.geometry("800x500")
    gui.config(bg="#ECF4F0")

    # Header
    header = Label(gui, text="Server Control Panel", bg="#398A68", fg="white",
                   font=("Arial", 20, "bold"), pady=15)
    header.pack(fill=X, padx=40, pady=(30, 0))  # 20px left/right margin, 20px top margin
    
   # Left Frame (Chat Area)
    left_frame = Frame(gui, bg="#D3E4DD", height=100)  # Set a fixed height for the left_frame
    left_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=(40,0), pady=20)

    connections_label = Label(left_frame, text="Connections", bg="#D3E4DD", fg="#000000", font=("Arial", 15, "bold"))
    connections_label.pack(pady=(10, 5))  # Padding between the heading and the client list

    # Chat Log Area
    chatlog = Text(left_frame, bg="#ECF4F0", fg="#001E55", bd=0, font=("Arial", 12), wrap=WORD, width=20)
    chatlog.tag_config("notice", foreground="#ffcc00")  # System notifications
    chatlog.tag_config("chat", foreground="#1fc600")  # Chat messages

    # Add horizontal padding (e.g., 20px on both sides of chatlog)
    chatlog.pack(fill=BOTH, expand=True, padx=20, pady=20)  # Padding between chatlog and the frame
    chatlog.config(state=DISABLED)

    # Create a frame to hold broadcast message, input field, and buttons
    broadcast_frame = Frame(gui, bg="#D3E4DD")  # Light color for the frame
    broadcast_frame.pack(fill=X, padx=40, pady=(25, 5))  # Padding between buttons and other elements

    # Broadcast Message Label
    broadcast_label = Label(broadcast_frame, text="Broadcast Message", bg="#D3E4DD", fg="#000000", font=("Arial", 15, "bold"))
    broadcast_label.pack(pady=(5, 5))  # Padding between the label and the input field

    # Server Message Input
    server_textbox = Text(broadcast_frame, height=3, bg="#ECF4F0", fg="black", font=("Arial", 12), padx=20, pady=14, bd=0)
    server_textbox.pack(fill=X, padx=20, pady=(5, 5))
    server_textbox.bind("<Return>", lambda event: send_server_message())

    # Create a frame to hold the buttons side by side
    button_frame = Frame(broadcast_frame, bg="#D3E7D9")  # Light color for buttons frame
    button_frame.pack(pady=(5, 15))  # Padding between buttons and other elements

    # Send Button for Server to Broadcast Messages
    send_button = Button(button_frame, text="Send Message", command=send_server_message, bg="#398A68", fg="white", bd=0, padx=16, pady=3,  font=("Arial", 12))
    send_button.pack(side=LEFT, padx=5)  # Place the Send button on the left side with some padding

    # Select File Button
    file_button = Button(button_frame, text="Select File to Share", command=select_file, bg="#000", fg="white", bd=0, padx=16, pady=3, font=("Arial", 12))
    file_button.pack(side=LEFT, padx=5)  # Place the File button on the left side with some padding

  

    # Monitor Button to show client chats
    monitor_button = Button(gui, text="Monitor Chatroom", command=monitor_chats, bg="black", fg="white", bd=0, padx=16, pady=3,  font=("Arial", 14))
    monitor_button.pack(pady=(30, 30))

    # Right Frame (Client List)
    right_frame = Frame(gui, bg="#D3E4DD", width=400)
    right_frame.pack(side=RIGHT, fill=Y, padx=35, pady=27)

    # Client List Label
    client_label = Label(right_frame, text="Online Clients ", bg="#388565", fg="white",
                         font=("Arial", 14, "bold"), pady=5)
    client_label.pack(fill=X)

    # Listbox for Displaying Clients
    clients_listbox = Listbox(right_frame, bg="#D3E4DD", fg="black",bd=0, font=("Arial", 12),  width=90)
    clients_listbox.pack(fill=BOTH, expand=True, padx=30, pady=20)

    # Start accepting connections
    _thread.start_new_thread(accept_connections, ())

    # Run the GUI
    gui.mainloop()

if __name__ == '__main__':
    # Initialize server socket
    server_socket = socket(AF_INET, SOCK_STREAM)
    server_host = 'localhost'
    server_port = 5671
    server_socket.bind((server_host, server_port))
    server_socket.listen(5)

    print(f"Server started on {server_host}:{server_port}")

    # Start GUI
    server_gui()
