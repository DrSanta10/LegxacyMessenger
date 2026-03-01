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
    200: "OK"
    201: "CREATED"
    400: "BAD REQUEST"
    401: "UNAUTHORIZED"
    404: "NOT FOUND"
    409: "CONFLICT"
    500: "SERVER ERROR"
}

def build_message(command, target, headers=None, body=""):
    if headers is None:
        headers = {}
        
    if isinstance(body, str):
        body_bytes = body.encode("utf-8")
    else:
        body_bytes = body
        
    if body_bytes:
        headers["Content-Length"] = str(len(body_bytes))
        
    header_lines = CRLF.join(f"{k}: {v}" for k, v in headers.items())
    
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
    header_lines = CRLF.join(f"{k}: {v}" for k, v in headers.items())
    header_block = first_line + CRLF + header_lines + HEADER_SEP
    
    return header_block.encode("utf-8") + body_bytes