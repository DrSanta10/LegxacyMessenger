import socket
import threading
import sys
import datetime
from protocol import receive_message, send_response, send_message, validate, ParseError

HOST = "0.0.0.0"
PORT = 5000
MAX = 50

lock = threading.Lock()
sessions = {}
groups = {}


def log(label, msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{label:10}] {msg}")
    
def forward(target_user, parsed):
    sock = sessions.get(target_user)
    if not sock:
        return False
    try:
        send_message(sock, parsed["command"], parsed["target"],
                     headers = parsed["headers"], body = parsed["body"])
        return True
    except Exception as e:
        log("FORWARD", f"Failed to forward to {target_user}: {e}")
        return False
    
def clean(username):
    with lock:
        sessions.pop(username, None)
        
        for name in list(groups):
            groups[name].discard(username)
            
            if not groups[name]:
                del groups[name]
                
def handle_login(connection, parsed, address):
    username = parsed["headers"].get("From", "").strip()
    
    if not username:
        send_response(connection, 400, {"To": ""}, body = "Username cannot be empty.")
        return None
    
    with lock:
        if username in sessions:
            send_response(connection, 409, 
                          {"To": username, "Error-Code": "409", 
                           "Content-Type": "text/plain"},
                          body = "Username already in use.")
            log("LOGIN", f"Duplicate username '{username}' from {address}.")
            return None
        sessions[username] = connection
        
    send_response(connection, 200, {"To": username})
    log("LOGIN", f"'{username}' connected from {address}.")
    return username

def handle_logout(connection, parsed, username):
    clean(username)
    send_response(connection, 200, {"To": username})
    log("LOGOUT", f"'{username}' logged out")

def handle_msg(connection, parsed, username):
    headers = parsed["headers"]
    group_id = headers.get("Group-ID")
    to = headers.get("To")
    
    if group_id:
        with lock:
            members = groups.get(group_id)
            
        if members is None:
            send_response(connection, 404, {"To": username}, 
                          body = f"Group '{group_id}' does not exist.")
            return
        if username not in members:
            send_response(connection, 401, {"To": username}, 
                          body = "You are not a member of this group.")
            return
        
        delivered = 0
        with lock:
            for member in list(members):
                if member != username and forward(member, parsed):
                    delivered += 1
                    
        send_response(connection, 200, {"To": username})
        log("MSG", f"'{username}' -> group '{group_id}' ({delivered} delivered)")
        
    elif to:
        with lock:
            ok = forward(to, parsed)
            
        if ok:
            send_response(connection, 200, {"To": username})
            log("MSG", f"'{username}' -> '{to}'")
        else:
            send_response(connection, 404, {"To": username}, 
                          body = f"User '{to}' is not online.")
    else:
        send_response(connection, 400, {"To": username}, 
                          body = "MSG requeires a To or Group-ID header.")
            
def handle_create_group(connection, parsed, username):
    name = parsed["headers"].get("Group-ID", "").strip()
    if not name:
        send_response(connection, 400, {"To": username}, body = "Group-ID cannot be empty.")
        return
    
    with lock:
        if name in groups:
            send_response(connection, 409, {"To": username}, 
                          body = f"Group '{name}' already exists.")
            return
        groups[name] = {username}
        
    send_response(connection, 201, {"To": username, "Group-ID": name})
    log("GROUP", f"'{username}' created group '{name}'")
    
def handle_join_group(connection, parsed, username):
    name = parsed["headers"].get("Group-ID", "").strip()
    if not name:
        send_response(connection, 400, {"To": username}, body = "Group-ID cannot be empty.")
        return
    
    with lock:
        if name not in groups:
            send_response(connection, 404, {"To": username}, 
                          body = f"Group '{name}' does not exists.")
            return
        groups[name].add(username)
        members = list(groups[name])
        
    send_response(connection, 200, {"To": username, "Group-ID": name})
    
    with lock:
        for member in members:
            if member != username:
                socket = sessions.get(member)
                if socket:
                    try:
                        send_message(socket, "NOTIFY", "/server", 
                                     headers = {"From": "server", "To": member,
                                                "Group-ID": name},
                                     body = f"{username} joined the group.")
                    except Exception:
                        pass
    
    log("GROUP", f"'{username}' joined '{name}'")
    
    
def handle_ping(connection, parsed, username):
    send_response(connection, 200, {"To": username})
    
    
HANDLERS = {
    "LOGOUT": handle_logout,
    "MSG": handle_msg,
    "CREATE_GROUP": handle_create_group,
    "JOIN_GROUP": handle_join_group,
    "PING": handle_ping,
}

def client_thread(connection, address):
    log("CONNECT", f"New connection from {address}")
    username = None
    
    try:
        while username is None:
            parsed = receive_message(connection)
            if parsed["command"] != "LOGIN":
                send_response(connection, 401, {"To": ""},
                              body = "You must LOGIN first.")
                continue
            username = handle_login(connection, parsed, address)
            
        while True:
            parsed = receive_message(connection)
            
            if parsed["type"] != "request":
                continue
            
            command = parsed["command"]
            log("RECV", f"'{username}' -> {command}")
            
            ok, reason = validate(parsed)
            if not ok:
                send_response(connection, 400, {"To": username}, body = reason)
                continue
            
            if command == "LOGOUT":
                handle_logout(connection, parsed, username)
                break
            
            handler = HANDLERS.get(command)
            if handler:
                handler(connection, parsed, username)
            else:
                send_response(connection, 400, {"To": username}, 
                              body = f"Unsupported command: {command}")
                
    except ConnectionError:
        log("DISCONNECT", f"'{username or address}' disconnected")
    except ParseError as e:
        log("PARSE_ERR", f"'{username or address}': {e}")
    except Exception as e:
        log("ERROR", f"'{username or address}': {e}")
    finally:
        if username:
            clean(username)
            log("CLEANUP", f"Session for '{username}' removed")
        try:
            connection.close()
        except Exception:
            pass


def server(host = HOST, port = PORT):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(MAX)
    
    log("Server", f"LegxacyMessenger server listening on {host}:{port}")
    log("Server", "Waiting for connections")
    
    try:
        while True:
            connection, address = srv.accept()
            t = threading.Thread(target=client_thread, args=(connection, address), daemon=True)
            t.start()
            with lock:
                log("SERVER", f"Active sessions: {len(sessions)}")
    except KeyboardInterrupt:
        log("SERVER", "Shutting down.")
    finally:
        srv.close()
        
if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    server(port = port)