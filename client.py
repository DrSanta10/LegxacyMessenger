import socket
import threading
import sys
import datetime
import base64
import os
from protocol import send_message, receive_message, ParseError

HOST = "100.87.127.9"
PORT = 5000

DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "received")

class NetworkClient:
    def __init__(self, message = None, notify = None,
                 error = None, p2p = None, users = None, file_received = None):
        self.message = message or (lambda *a: None)
        self.notify = notify or (lambda *a: None)
        self.error = error or (lambda *a: None)
        self.p2p = p2p or (lambda *a: None)
        self.users = users or (lambda *a: None)
        self.file_received = file_received or (lambda *a: None)
        
        self.sock = None
        self.username = None
        self.running = False
        
    def connect(self, host, port, username, password):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.settimeout(5)
            self.sock.connect((host, port))
            self.sock.settimeout(None)
            self.username = username
            
            send_message(self.sock, "LOGIN", "/server",
                         headers = {"From": username, "Password": password})
            
            resp = receive_message(self.sock)
            
            if resp["status_code"] == 200:
                self.running = True
                threading.Thread(target = self.receive, daemon = True).start()
                return True, ""
            else:
                err = resp.get("body") or f"Login failed ({resp['status_code']})"
                self.sock.close()
                self.sock = None
                return False, err
            
        except ConnectionRefusedError:
            return False, f"Cannot connect to {host}:{port}"
        except socket.timeout:
            return False, "Connection timed out."
        except Exception as e:
            return False, str(e)
        
    def disconnect(self):
        self.running = False
        if self.sock:
            try:
                send_message(self.sock, "LOGOUT", "/server",
                             headers = {"From": self.username})
            except Exception:
                pass
            
            try:
                self.sock.close()
            except Exception:
                pass
        self.sock = None
            
    
    def send_msg(self, to, text):
        self.send("MSG", "/user", 
                   headers = {"From": self.username, "To": to,
                              "Content-Type": "text/plain",
                              "Timestamp": now()},
                   body = text)
        
    def group_msg(self, group, text):
        self.send("MSG", "/group", 
                   headers = {"From": self.username, "Group-ID": group,
                              "Content-Type": "text/plain",
                              "Timestamp": now()},
                   body = text)
        
    def send_file(self, to, file):
        if not os.path.isfile(file):
            self.error(f"File not found: {file}")
            return
    
        filename = os.path.basename(file)
        filesize = os.path.getsize(file)
        
        try:
            with open(file, "rb") as f:
                raw = f.read()
            data = base64.b64encode(raw).decode("utf-8")
        except Exception as e:
            self.error(f"Could not read file: {e}")
            return
        
        self.send("FILE_SEND", "/user", headers = 
                  {
                      "From": self.username,
                      "To": to,
                      "Filename": filename,
                      "Content-Type": "application/octet-stream",
                      "Timestamp": now()
                  }, body = data)
        
    def send_file_group(self, group, file):
        if not os.path.isfile(file):
            self.error(f"File not found: {file}")
            return
        
        filename = os.path.basename(file)
        filesize = os.path.getsize(file)
        
        try:
            with open(file, "rb") as f:
                raw = f.read()
            data = base64.b64encode(raw).decode("utf-8")
        except Exception as e:
            self.error(f"Could not read file: {e}")
            return
        
        self.send("FILE_SEND", "/group", headers = 
                  { "From": self.username,
                    "Group-ID": group,
                    "Filename": filename,
                    "Content-Type": "application/octet-stream",
                    "Timestamp": now()
                  }, body = data)
            
        
    def create_group(self, group):
        self.send("CREATE_GROUP", "/server", 
                   headers = {"From": self.username, "Group-ID": group})
        
    def join_group(self, group):
        self.send("JOIN_GROUP", "/server", 
                   headers = {"From": self.username, "Group-ID": group})
        
    def leave_group(self, group):
        self.send("LEAVE_GROUP", "/server", 
                   headers = {"From": self.username, "Group-ID": group})
        
    def list_users(self):
        self.send("LIST_USERS", "/server", 
                  headers = {"From": self.username})

    def list_groups(self):
        self.send("LIST_GROUPS", "/server", 
                  headers = {"From": self.username})
        
    def ping(self):
        self.send("PING", "/server", headers = {"From": self.username})
        
    def send(self, command, target, headers = None, body = ""):
        if not self.sock:
            self.error("Not connected.")
            return
        try:
            send_message(self.sock, command, target, headers, body)
        except Exception as e:
            self.error(f"Send error: {e}")
            
    def receive(self):
        while self.running:
            try:
                msg = receive_message(self.sock)
                headers = msg.get("headers", {})
                body = msg.get("body", "")
            
                if msg["type"] == "request":
                    cmd = msg["command"]
                
                    if cmd == "MSG":
                        sender = headers.get("From", "unknown")
                        group_id = headers.get("Group-ID")
                        timestamp = headers.get("Timestamp", now())
                        chat = group_id if group_id else sender
                        self.message(chat, sender, body, timestamp)
                        
                    elif cmd == "FILE_SEND":
                        sender = headers.get("From", "unknown")
                        group_id = headers.get("Group-ID")
                        file = headers.get("Filename", "file")
                        timestamp = headers.get("Timestamp", now())
                        chat = group_id if group_id else sender
                        
                        try:
                            data = base64.b64decode(body)
                        except Exception:
                            self.error(f"Corrupt file received from {sender}.")
                            continue
                        
                        self.file_received(sender, file, data, timestamp, chat)
                    
                    elif cmd == "NOTIFY":
                        group_id = headers.get("Group-ID", "")
                        self.notify(group_id, body)

                elif msg["type"] == "response":
                    code = msg["status_code"]
                    if code in (200, 201):
                        if body and headers.get("Content-Type") == "text/plain":
                            names = [n.strip() for n in body.split(",") if n.strip()]
                            self.users(names)
                    else:
                        self.error(body or f"Server error {code}")
                    
            except ConnectionError:
                if self.running:
                    self.error("Disconnected from server.")
                break
            except ParseError as e:
                self.error(f"Protocol error: {e}")
            except Exception as e:
                if self.running:
                    self.error(f"Receive error: {e}")
                break
            
        self.running = False
                
def now():
    return datetime.datetime.now().strftime("%H:%M")


def save_file(file, data):
    os.makedirs(DIR, exist = True)
    
    base, ext = os.path.splitext(file)
    destination = os.path.join(DIR, file)
    counter = 1
    
    while os.path.exists(destination):
        destination = os.path.join(DIR, f"{base}_{counter}{ext}")
        counter += 1
        
    with open(destination, "wb") as f:
        f.write(data)
    return destination
 
def terminal():
    host = input(f"Server host [{HOST}]: ").strip() or HOST
    port_str = input(f"Server port [{PORT}]: ").strip()
    port = int(port_str) if port_str else PORT
    username = input("Username: ").strip()
    password = input("Password: ").strip()
    
    def message(chat, sender, body, ts):
        print(f"\n [{ts}] {sender} -> {username}: {body}")
        print("> ", end = "", flush = True)
        
    def notify(group, body):
        print(f"\n [NOTIFY] {group}: {body}")
        print("> ", end = "", flush = True)
        
    def error(msg):
        print(f"\n [ERROR] {msg}")
        print("> ", end = "", flush = True)
        
    def users(names):
        print(f"\n [USERS] Online: {', '.join(names) if names else '(none)'}")
        print("> ", end = "", flush = True)
    
    def file_received(sender, file, data, ts, chat):
        destination = save_file(file, data)
        print(f"\n [{ts}] FILE from {sender}: '{file}' " 
              f"saved to {destination}")
        print("> ", end="", flush=True)
        
        
    client = NetworkClient(message = message, notify = notify, error = error, users = users, file_received = file_received)
    
    print(f"\nConnecting to {host}:{port} ...")
    ok, err = client.connect(host, port, username, password)
    
    if not ok:
        print(f"[FAILED] {err}")
        sys.exit(1)
        
    print(f"Logged in as '{username}'.\n")
    
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        
        if not line:
            continue
        
        parts = line.split(" ", 2)
        cmd = parts[0].lower()
        
        if cmd == "/msg":
            if len(parts) < 3:
                print(" Usage: /msg <username> <message>")
            else:
                client.send_msg(parts[1], parts[2])
        elif cmd == "/group":
            if len(parts) < 3:
                print(" Usage: /group <group_name> <message>")
            else:
                client.group_msg(parts[1], parts[2])
        elif cmd == "/file":
            if len(parts) < 3:
                print("Usage: /file <username> <filepath>")
            else:
                target = parts[1]
                path = parts[2].strip()
                print(f"Sending '{os.path.basename(path)}' to {target}")
                client.send_file(target, path)
        elif cmd == "/gfile":
            if len(parts) < 3:
                print("Usage: /gfile <group_name> <filepath>")
            else:
                group = parts[1]
                path = parts[2].strip()
                print(f"Sending '{os.path.basename(path)}' to group {group}")
                client.send_file_group(group, path)
        elif cmd == "/create":
            if len(parts) < 2:
                print(" Usage: /create <group_name>")
            else:
                client.create_group(parts[1])
        elif cmd == "/join":
            if len(parts) < 2:
                print(" Usage: /join <group_name>")
            else:
                client.join_group(parts[1])
        elif cmd == "/leave":
            if len(parts) < 2:
                print(" Usage: /leave <group_name>")
            else:
                client.leave_group(parts[1])
        elif cmd == "/users":
            client.list_users()
        elif cmd == "/quit":
            break
        else:
            print(f"Unknown command '{cmd}'.")
            
    client.disconnect()
    print("Goodbye.")
     
            
if __name__ == "__main__":
    terminal()