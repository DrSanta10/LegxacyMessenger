# Constants
PROTOCOL_NAME = "LegxacyMessenger"
CRLF = "\r\n"
HEADER_SEP = CRLF + CRLF
BUFFER_SIZE = 4096

COMMAND_TYPES = {"LOGIN", "LOGOUT", "CREATE_GROUP", "JOIN_GROUP", 
                 "LEAVE_GROUP", "LIST_USERS", "LIST_GROUPS", "P2P_REQUEST", "P2P_OFFER"}

CONTROL_TYPES = {"ACK", "ERROR", "PING", "PONG", "NOTIFY"}

DATA_TYPES = {"MSG", "MEDIA_INIT", "MEDIA_DATA", "MEDIA_ACK", "MEDIA_END", "FILE_SEND"}

ALL_TYPES = COMMAND_TYPES | CONTROL_TYPES | DATA_TYPES


STATUS = {
    200: "OK",
    201: "CREATED",
    400: "BAD REQUEST",
    401: "UNAUTHORIZED",
    404: "NOT FOUND",
    409: "CONFLICT",
    500: "SERVER ERROR"
}

MAX_FILE = 50 * 1024 * 1024

def build_message(command, target, headers=None, body=""):
    if headers is None:
        headers = {}
        
    if isinstance(body, str):
        body_bytes = body.encode("utf-8")
    else:
        body_bytes = body
        
    if body_bytes:
        headers["Content-Length"] = str(len(body_bytes))
        
    first_line = f"{command} {target} {PROTOCOL_NAME}"
    
    header_lines = CRLF.join(f"{key}: {value}" for key, value in headers.items())
    
    header_block = first_line + CRLF + header_lines + HEADER_SEP
    
    return header_block.encode("utf-8") + body_bytes

def build_response(status_code, headers=None, body=""):
    if headers is None:
        headers={}
        
    status_text = STATUS.get(status_code, "UNKNOWN")
    
    if isinstance(body, str):
        body_bytes = body.encode("utf-8")
    else:
        body_bytes = body
        
    if body_bytes:
        headers["Content-Length"] = str(len(body_bytes))
        
    first_line = f"{status_code} {status_text} {PROTOCOL_NAME}"
    header_lines = CRLF.join(f"{key}: {value}" for key, value in headers.items())
    header_block = first_line + CRLF + header_lines + HEADER_SEP
    
    return header_block.encode("utf-8") + body_bytes

class ParseError(Exception):
    pass

def parse_message(raw):
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors = "replace")
        
    if HEADER_SEP not in raw:
        raise ParseError("Missing blank line between the header and body.")
    
    header_block, body = raw.split(HEADER_SEP, 1)
    lines  = header_block.split(CRLF)
    
    if not lines:
        raise ParseError("Empty header block.")
    
    #first_line = lines[0].strip()
    parts = lines[0].strip().split(" ", 2)
    
    if len(parts) < 2:
        raise ParseError(f"Malformed first line: '{lines[0]}'")
    
    result = {}
    if parts[0].isdigit():
        result["type"] = "response"
        result["status_code"] = int(parts[0])
        result["status_text"] = parts[1] if len(parts) > 1 else ""
        result["command"] = None
        result["target"] = None
    else:
        result["type"] = "request"
        result["command"] = parts[0].upper()
        result["target"] = parts[1] if len(parts) > 1 else ""
        result["status_code"] = None
        result["status_text"] = None
        
    headers = {}
    
    for line in lines[1:]:
        line = line.strip()
        if not line:
            continue
        if ":" not in line:
            raise ParseError(f"Malformed header line: '{line}'")
        key, _, value = line.partition(":")
        headers[key.strip()] = value.strip()
        
    result["headers"] = headers
    result["body"] = body.strip()
    
    return result


def send_message(sock, command, target, headers = None, body = ""):
    data = build_message(command, target, headers, body)
    sock.sendall(data)
    
def send_response(sock, status, headers = None, body = ""):
    data = build_response(status, headers, body)
    sock.sendall(data)
    
def receive_message(sock):
    raw = b""
    
    while HEADER_SEP.encode("utf-8") not in raw:
        chunk = sock.recv(BUFFER_SIZE)
        
        if not chunk:
            raise ConnectionError("Socket closed before full message was received.")
        raw += chunk
    
    bytes = HEADER_SEP.encode("utf-8")
    header_part, _, body = raw.partition(bytes)
    
    first = header_part.decode("utf-8", errors = "replace")
    templine = first.split(CRLF)
    headers_dict = {}
    
    for line in templine[1:]:
        if ":" in line:
            key, _, value = line.partition(":")
            headers_dict[key.strip()] = value.strip()
            
    content = int(headers_dict.get("Content-Length", 0))
    
    while len(body) < content:
        needed = content - len(body)
        chunk = sock.recv(min(needed, BUFFER_SIZE))
        if not chunk:
            raise ConnectionError("Socket closed mid-body.")
        body += chunk
        
    body = body[:content]
        
    full = header_part + bytes + body
    return parse_message(full)

def validate(parsed):
    if parsed["type"] == "request":
        command = parsed.get("command", "")
        headers = parsed.get("headers", {})
        
        if command not in ALL_TYPES:
            return False, f"Unkown command: {command}"
        
        if "From" not in headers:
            return False, "Missing header: From"
        
        if command in {"MSG", "FILE_SEND"} and "To" not in headers and "Group-ID" not in headers:
            return False, "MSG requires either a To or Group-ID header"
        
        if command in {"MSG", "FILE_SEND", "MEDIA_DATA"} and "Content-Length" not in headers:
            return False, f"{command} with a body requires Content-Length"
        
        if command == "FILE_SEND" and "Filename" not in headers:
            return False, "FILE_SEND requires a Filename header"
        
    return True, ""