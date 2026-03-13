import socket
import threading
import sys
import datetime
import base64
import os
from protocol import send_message, receive_message, ParseError

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    
CHUNK = 1024
FORMAT = 8
CHANNELS = 1
RATE = 44100


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
        
        #UDP Socket
        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(("", 0))  
        self.udp_port = self.udp_socket.getsockname()[1]

        self.peer_ip = None
        self.peer_port = None
        self.call_peer = None
        self.media_running = False
        
        self.audio = None
        self.mic_stream = None
        self.speaker_stream = None
        
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
        file = os.path.abspath(os.path.expanduser(file))
        
        if not os.path.exists(file):
            self.error(f"File not found: {file}")
            return
        if not os.path.isfile(file):
            self.error(f"Not a file: {file}")
            return
    
        filename = os.path.basename(file)
        filesize = os.path.getsize(file)
        
        if filesize > 50 * 1024 * 1024:
            self.error("File is too large. Maximum size is 50MB.")
            return
        
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
        file = os.path.abspath(os.path.expanduser(file))
        
        if not os.path.exists(file):
            self.error(f"File not found: {file}")
            return
        if not os.path.isfile(file):
            self.error(f"Not a file: {file}")
            return
        
        filename = os.path.basename(file)
        filesize = os.path.getsize(file)
        
        if filesize > 50 * 1024 * 1024:
            self.error("File is too large. Maximum size is 50MB.")
            return
        
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
    
    def request_call(self, username):
        self.send(
            "P2P_REQUEST",
            "/user",
        headers={
            "From": self.username,
            "To": username,
            "UDP-Port": str(self.udp_port)
        }
    )
        
    def start_media(self, peer = None):

        if self.media_running:
            return
        
        if peer:
            self.call_peer = peer
            
        self.media_running = True
        
        if PYAUDIO_AVAILABLE:
            import os as _os
            devnull_fd = _os.open(_os.devnull, _os.O_WRONLY)
            old_stderr = _os.dup(2)
            _os.dup2(devnull_fd, 2)
            try:
                self.audio = pyaudio.PyAudio()
                
            finally:
                _os.dup2(old_stderr, 2)
                _os.close(devnull_fd)
                _os.close(old_stderr)
            
            input_index = None
            output_index = None
            
            for i in range(self.audio.get_device_count()):
                try:
                    info = self.audio.get_device_info_by_index(i)
                except Exception:
                    continue
                
                if input_index is None and info.get("maxInputChannels", 0) > 0:
                    input_index = i
                if output_index is None and info.get("maxOutputChannels", 0) > 0:
                    output_index = i
                if input_index is not None and output_index is not None:
                    break
                
                if input_index is not None:
                    try:
                        self.mic_stream = self.audio.open(
                            format=pyaudio.paInt16,
                            channels=CHANNELS,
                            rate=RATE,
                            input=True,
                            input_device_index=input_index,
                            frames_per_buffer=CHUNK)
            
                    except Exception as e:
                        self.error(f"Audio device error: {e}. Call connected but no audio.")
                        self.mic_stream = None
                else:
                    self.error("No microphone found. Sending silence.")
                    self.mic_stream = None
                    
                if output_index is not None:
                    try:
                        self.speaker_stream = self.audio.open(
                            format=pyaudio.paInt16,
                            channels=CHANNELS,
                            rate=RATE,
                            output=True,
                            output_device_index=output_index,
                            frames_per_buffer=CHUNK)
            
                    except Exception as e:
                        self.error(f"Speaker open failed (device {output_index}): {e}")
                        self.speaker_stream = None
                else:
                    self.error("No speaker found. Incoming audio will be discarded.")
                    self.speaker_stream = None
                    
                if self.mic_stream and self.speaker_stream:
                    mic_name = self.audio.get_device_info_by_index(input_index).get("name", "?")
                    spk_name = self.audio.get_device_info_by_index(output_index).get("name", "?")
                    print(f"\n [CALL] Audio ready mic={mic_name} speaker={spk_name}")
                    print("> ", end="", flush=True)
                elif not self.mic_stream and not self.speaker_stream:
                    self.error("No audio devices found. Call connected but no audio.")
                                
        else:
            self.error("pyaudio is not installed. Call connected but no audio."
                       "Install with: pip install pyaudio")
            
        threading.Thread(target=self.receive_media, daemon = True).start()
        threading.Thread(target=self.send_media, daemon = True).start()

    def receive_media(self):
        self.udp_socket.settimeout(1.0)
        
        while self.media_running:
            try:
                data, addr = self.udp_socket.recvfrom(65535)
                
                if not self.media_running:
                    break
                
                if self.peer_ip is None or self.peer_port is None:
                    self.peer_ip = addr[0]
                    self.peer_port = addr[1]
                    
                if self.speaker_stream:
                    try:
                        self.speaker_stream.write(data)
                    except Exception:
                        pass
                    
                self.p2p(data, addr)
                
            except socket.timeout:
                continue
            except OSError:
                break
            except Exception as e:
                if self.media_running:
                    self.error(f"Media receive error: {e}")
                break
            
        self.media_running = False

    def send_media(self):
        import time

        while self.media_running:

            if self.peer_ip and self.peer_port:
                
                try:
                    if self.mic_stream:
                        audio_data = self.mic_stream.read(CHUNK, exception_on_overflow=False)
                    else:
                        audio_data = b'\x00' * CHUNK * 2
                    
                    self.udp_socket.sendto(audio_data, (self.peer_ip, self.peer_port))
                
                except OSError:
                    break
                except Exception as e:
                    if self.media_running:
                        self.error(f"Media send error: {e}")
                    break
            
            else:
                time.sleep(0.02)
                
    
    def hangup(self):
        if not self.media_running and not self.call_peer:
            return
        
        if self.call_peer:
            try:
                self.send("HANGUP", "/user",
                          headers={"From": self.username,
                                   "To": self.call_peer})
                
            except Exception:
                pass
            
        self.stop_media()
        
    def stop_media(self):
        self.media_running = False
        self.call_peer = None
        self.peer_ip = None
        self.peer_port = None
        
        if self.mic_stream:
            try:
                self.mic_stream.stop_stream()
                self.mic_stream.close()
            except Exception:
                pass
            self.mic_stream = None
            
        if self.speaker_stream:
            try:
                self.speaker_stream.stop_stream()
                self.speaker_stream.close()
            except Exception:
                pass
            self.speaker_stream = None
            
        if self.audio:
            try:
                self.audio.terminate()
            except Exception:
                pass
            self.audio = None
            
        try:
            self.udp_socket.close()
        except Exception:
            pass

        self.udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.udp_socket.bind(("", 0))
        self.udp_port = self.udp_socket.getsockname()[1]

        
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

                    elif cmd == "P2P_REQUEST":
                        sender = headers.get("From")

                        self.peer_ip = headers.get("Peer-IP")
                        self.peer_port = int(headers.get("UDP-Port", 0)) or None
                        self.call_peer = sender
                        
                        print(f"Incoming call from {sender}")
                        accept = input("Accept call? (y/n): ")

                        if accept.lower() == "y":
                            self.send(
                                "P2P_OFFER",
                                "/user",
                                headers={
                                    "From": self.username,
                                    "To": sender,
                                    "UDP-Port": str(self.udp_port)
                                }
                            )
                            self.start_media(peer=sender)
                            print(f"\n [CALL] Call started with {sender}. "
                                  f"Type /hangup to end.")
                            print("> ", end = "", flush = True)
                        else:
                            self.call_peer = None
                            self.peer_ip = None
                            self.peer_port = None
                            print(f"\n [CALL] Call from {sender} declined.")
                            print("> ", end= "", flush = True)
                            

                    elif cmd == "P2P_OFFER":
                        sender = headers.get("From")

                        self.peer_ip = headers.get("Peer-IP")
                        self.peer_port = int(headers.get("UDP-Port", 0)) or None
                        self.call_peer = sender

                        print(f"\n [CALL] {sender} accepted. Call started. "
                              f"Type /hangup to end.")
                        print("> ", end="", flush=True)
                        self.start_media(peer = sender)
                    
                    elif cmd == "HANGUP":
                        sender = headers.get("From", "peer")
                        print(f"\n [CALL] {sender} ended the call.")
                        print("> ", end = "", flush=True)
                        self.stop_media()


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
    os.makedirs(DIR, exist_ok = True)
    
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
        
    def p2p(data, addr):
        pass
        
        
    client = NetworkClient(message = message, notify = notify, error = error, users = users, file_received = file_received, p2p = p2p)
    
    print(f"\nConnecting to {host}:{port} ...")
    ok, err = client.connect(host, port, username, password)
    
    if not ok:
        print(f"[FAILED] {err}")
        sys.exit(1)
        
    if not PYAUDIO_AVAILABLE:
        print("[WARN] pyaudio not found. Voice calls will connect but have no audio.")
        print("Install with: pip install pyaudio")
        
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
        elif cmd == "/call":
            if len(parts) < 2:
                print(" Usage: /call <username>")
            else:
                client.request_call(parts[1])
                
        elif cmd == "/hangup":
            if not client.media_running:
                print("No active call.")
            else:
                client.hangup()
                print("[CALL] Call ended.")
                
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