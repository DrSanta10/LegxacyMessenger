import socket
import threading
import sys
import datetime
import database as db
from protocol import receive_message, send_response, send_message, validate, ParseError

HOST = "0.0.0.0"
PORT = 5000
MAX = 50

lock = threading.Lock()
sessions = {}
#groups = {}


def log(label, msg):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{label:10}] {msg}")
    
def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    
def forward(target_user, parsed):
    with lock:
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
        
        """"
        for name in list(groups):
            groups[name].discard(username)
            
            if not groups[name]:
                del groups[name]
        """

def pending(username, connection):
    pend = db.get_pending(username)
    if not pend:
        return
    
    log("PENDING", f"Delivering {len(pend)} queued message(s) to '{username}'")
    
    for msg in pend:
        try:
            body = msg["body"]
            sender = msg["sender"]
            timestamp = msg["timestamp"]
            
            if db.is_file_body(body):
                filename, data = db.parse_file(body)
                
                if filename and data:
                    send_message(connection, "FILE_SEND", "/user", headers = {
                        "From": sender,
                        "To": username,
                        "Filename": filename,
                        "Content-Type": "application/octet-stream",
                        "Timestamp": timestamp,
                        "Offline": "true"
                    }, body = data)
            else:
                send_message(connection, "MSG", "/user", headers = {
                        "From": sender,
                        "To": username,
                        "Content-Type": "text/plain",
                        "Timestamp": timestamp,
                        "Offline": "true"
                    }, body = body)
        except Exception as e:
            log("PENDING", f"Could not deliver the queued item to '{username}': {e}")
            break
        
    try:
        db.delivered(username)
    except Exception as e:
        log("PENDING", f"Failed for '{username}': {e}")
    
                
def handle_login(connection, parsed, address):
    username = parsed["headers"].get("From", "").strip()
    password = parsed["headers"].get("Password", "").strip()
    
    if not username:
        send_response(connection, 400, {"To": ""}, body = "Username cannot be empty.")
        return None
    
    if not password:
        send_response(connection, 400, {"To": username}, body = "Password cannot be empty.")
        return None
    
    with lock:
        if username in sessions:
            old = sessions[username]
            stale = False
            try:
                old.getpeername()
                old.send(b"")
            except OSError:
                stale = True
                
            if stale:
                log("LOGIN", f"Removing stale session of '{username}'")
                sessions.pop(username, None)
                
                try:
                    old.close()
                except Exception:
                    pass
            else:
                send_response(connection, 409, 
                          {"To": username, "Error-Code": "409", 
                           "Content-Type": "text/plain"},
                          body = "Username already in use.")
                log("LOGIN", f"Duplicate session for '{username}'")
                return None
    
    if not db.user_exists(username):
        ok, err = db.register_user(username, password)
        if not ok:
            send_response(connection, 409, {"To": username}, body = err)
            return None
        log("LOGIN", f"Registered new user '{username}'")
    else:
        if not db.verify_user(username, password):
            send_response(connection, 409, 
                          {"To": username, "Error-Code": "401", 
                           "Content-Type": "text/plain"},
                          body = "Incorrect password.")
            log("LOGIN", f"Wrong password for '{username}' from {address}")
            return None
        
    with lock:
        sessions[username] = connection
        
    send_response(connection, 200, {"To": username})
    log("LOGIN", f"'{username}' connected from {address}.")
    
    with lock:
        log("SERVER", f"Active sessions: {len(sessions)}")
    
    try:
        pending(username, connection)
    except Exception as e:
        log("PENDING", f"Error during offline delivery for '{username}': {e}")
    
    return username

def handle_logout(connection, parsed, username):
    clean(username)
    send_response(connection, 200, {"To": username})
    log("LOGOUT", f"'{username}' logged out")

def handle_msg(connection, parsed, username):
    headers = parsed["headers"]
    group_id = headers.get("Group-ID")
    to = headers.get("To")
    body = parsed["body"]
    timestamp = headers.get("Timestamp", now())
    
    if group_id:
        members = db.get_members(group_id)
            
        if members is None:
            send_response(connection, 404, {"To": username}, 
                          body = f"Group '{group_id}' does not exist.")
            return
        if not db.is_member(group_id, username):
            send_response(connection, 401, {"To": username}, 
                          body = "You are not a member of this group.")
            return
        
        db.store_message(username, body, group = group_id, timestamp = timestamp)
        
        delivered = 0
        for member in members:
            if member != username and forward(member, parsed):
                delivered += 1
                    
        send_response(connection, 200, {"To": username})
        log("MSG", f"'{username}' -> group '{group_id}' ({delivered}/{len(members) - 1} delivered)")
        
    elif to:
        
        db.store_message(username, body, recipient= to, timestamp = timestamp)
        
        ok = forward(to, parsed)
            
        if ok:
            send_response(connection, 200, {"To": username})
            log("MSG", f"'{username}' -> '{to}' (delivered)")
        else:
            send_response(connection, 200, {"To": username})
            log("MSG", f"'{username}' -> '{to}' (queued: '{to}' is offline).")
            
    else:
        send_response(connection, 400, {"To": username}, 
                          body = "MSG requeires a To or Group-ID header.")
            

def handle_file_send(connection, parsed, username):
    headers = parsed["headers"]
    group_id = headers.get("Group-ID")
    to = headers.get("To")
    filename = headers.get("Filename", "file")
    data = parsed["body"]
    timestamp = headers.get("Timestamp", now())
    
    if group_id:
        members = db.get_members(group_id)
        if members is None:
            send_response(connection, 404, {"To": username}, body = f"Group '{group_id}' does not exist.")
            return
        
        if not db.is_member(group_id, username):
            send_response(connection, 401, {"To": username}, body = "You are not a member of this group.")
            return
        
        delivered = 0
        for member in members:
            if member != username and forward(member, parsed):
                delivered += 1
                
        send_response(connection, 200, {"To": username})
        log("FILE", f"'{username}' -> group '{group_id}' '{filename}' " f"({delivered}/{len(members) - 1} delivered)")
        
    elif to:
        db.store_file(username, filename, data, recipient=to, timestamp = timestamp)

        ok = forward(to, parsed)
            
        if ok:
            send_response(connection, 200, {"To": username})
            log("FILE", f"'{username}' -> '{to}' '{filename}' (delivered)")
        else:
            send_response(connection, 200, {"To": username})
            log("FILE", f"'{username}' -> '{to}' '{filename}' (queued: '{to}' is offline)")
            
    else:
        send_response(connection, 400, {"To": username}, body = "FILE_SEND required a To or Group-ID header.")

def handle_create_group(connection, parsed, username):
    name = parsed["headers"].get("Group-ID", "").strip()
    if not name:
        send_response(connection, 400, {"To": username}, body = "Group-ID cannot be empty.")
        return
    
    ok, err = db.create_group(name, created_by= username)
    if not ok:
        send_response(connection, 409, {"To": username}, body = err)
        return
    
    """"
    with lock:
        if name in groups:
            send_response(connection, 409, {"To": username}, 
                          body = f"Group '{name}' already exists.")
            return
        groups[name] = {username}
    """
        
    send_response(connection, 201, {"To": username, "Group-ID": name})
    log("GROUP", f"'{username}' created group '{name}'")
    

def handle_join_group(connection, parsed, username):
    name = parsed["headers"].get("Group-ID", "").strip()
    if not name:
        send_response(connection, 400, {"To": username}, body = "Group-ID cannot be empty.")
        return
    
    ok, err = db.join_group(name, username)
    if not ok:
        code = 409 if "already" in err else 404
        send_response(connection, code, {"To": username}, body = err)
        return

    """
    with lock:
        if name not in groups:
            send_response(connection, 404, {"To": username}, 
                          body = f"Group '{name}' does not exists.")
            return
        
        if username in groups[name]:
            send_response(connection, 409, {"To": username}, 
                          body = f"You are already a member of '{name}'")
            return
        
        groups[name].add(username)
        members = list(groups[name])
    """    
    
    send_response(connection, 200, {"To": username, "Group-ID": name})
    
    members = db.get_members(name) or []
    with lock:
        for member in members:
            if member != username:
                sock = sessions.get(member)
                if sock:
                    try:
                        send_message(sock, "NOTIFY", "/server", 
                                     headers = {"From": "server", "To": member,
                                                "Group-ID": name},
                                     body = f"{username} joined the group.")
                    except Exception:
                        pass
    
    log("GROUP", f"'{username}' joined '{name}'")
    
    
def handle_leave_group(connection, parsed, username):
    name = parsed["headers"].get("Group-ID", "").strip()
    
    if not name:
        send_response(connection, 400, {"To": username}, body = "Group-ID cannot be empty.")
        return
    
    ok, err = db.leave_group(name, username)
    if not ok:
        code = 404 if "does not exist" in err else 401
        send_response(connection, code, {"To": username}, body = err)
        return
    
    """
    with lock:
        if name not in groups:
            send_response(connection, 404, {"To": username}, 
                          body = f"Group '{name}' does not exists.")
            return
        
        if username not in groups[name]:
            send_response(connection, 401, {"To": username},
                          body = f"You are not a member of '{name}'.")
            return
        
        groups[name].discard(username)
        if not groups[name]:
            del groups[name]
            log("GROUP", f"Group '{name}' deleted (no members left)")
    """
    
    send_response(connection, 200, {"To": username})
    log("GROUP", f"'{username}' left '{name}'")
    
def handle_list_users(connection, parsed, username):
    with lock:
        online = [u for u in sessions if u != username]
    send_response(connection, 200, 
                  {"To": username, "Content-Type": "text/plain"},
                  body = ",".join(online))
    log("LIST", f"'{username}' requested users ({len(online)} online)")

def handle_list_groups(connection, parsed, username):
    names = db.get_groups()
    send_response(connection, 200, 
                  {"To": username, "Content-Type": "text/plain"},
                  body = ",".join(names))
    log("LIST", f"'{username}' requested groups ({len(names)} groups)")
    
def handle_ping(connection, parsed, username):
    send_response(connection, 200, {"To": username})
    
    
HANDLERS = {
    "LOGOUT": handle_logout,
    "MSG": handle_msg,
    "FILE_SEND": handle_file_send,
    "CREATE_GROUP": handle_create_group,
    "JOIN_GROUP": handle_join_group,
    "LEAVE_GROUP": handle_leave_group,
    "LIST_USERS": handle_list_users,
    "LIST_GROUPS": handle_list_groups,
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
    db.initialise()
    #log("DB", f"Database ready: {db.PATH}")
    
    
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind((host, port))
    srv.listen(MAX)
    
    log("Server", f"LegxacyMessenger server listening on {host}:{port}")
    #log("Server", "Waiting for connections")
    
    try:
        while True:
            connection, address = srv.accept()
            t = threading.Thread(target=client_thread, args=(connection, address), daemon=True)
            t.start()
    except KeyboardInterrupt:
        log("SERVER", "Shutting down.")
    finally:
        srv.close()
        
if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    server(port = port)