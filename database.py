import sqlite3
import datetime
import threading
import os
import json

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "legxacy - Copy.db")

_local = threading.local()

def _conn():
    if not hasattr(_local, "conn") or _local.conn is None:
        _local.conn = sqlite3.connect(PATH)
        _local.conn.row = sqlite3.Row
        _local.conn.execute("PRAGMA journal_mode = WAL")
        _local.conn.execute("PRAGMA foreign_key = ON")
    
    return _local.conn

def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def initialise():
    _conn().executescript("""CREATE TABLE IF NOT EXISTS users (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            username   TEXT    NOT NULL UNIQUE COLLATE NOCASE,
            password   TEXT    NOT NULL,
            created_at TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS groups (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT    NOT NULL UNIQUE COLLATE NOCASE,
            created_by TEXT    NOT NULL,
            created_at TEXT    NOT NULL
        );

        CREATE TABLE IF NOT EXISTS group_members (
            group_name TEXT NOT NULL COLLATE NOCASE,
            username   TEXT NOT NULL COLLATE NOCASE,
            joined_at  TEXT NOT NULL,
            PRIMARY KEY (group_name, username)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            sender     TEXT NOT NULL,
            recipient  TEXT,
            group_name TEXT,
            body       TEXT NOT NULL,
            timestamp  TEXT NOT NULL
        );

        CREATE INDEX IF NOT EXISTS idx_messages_dm
            ON messages (sender, recipient);

        CREATE INDEX IF NOT EXISTS idx_messages_group
            ON messages (group_name);
            """)
    _conn().commit()
    

def user_exists(username):
    row = _conn().execute("SELECT 1 FROM users WHERE username = ? COLLATE NOCASE", 
                          (username,)).fetchone()
    return row is not None


def register_user(username, password):
    try:
        _conn().execute("INSERT INTO users (username, password, created_at) VALUES (?, ?, ?)", 
                        (username, password, now()))
        _conn().commit()
        return True, ""
    except sqlite3.IntegrityError:
        return False, "Username is taken."
    except Exception as e:
        return False, str(e)
    
    
def verify_user(username, password):
    row = _conn().execute("SELECT password FROM users WHERE username =? COLLATE NOCASE",
                          (username, )).fetchone()
    if not row:
        return False
    return row["password"] == password


def create_group(name, created_by):
    try:
        _conn().execute("INSERT INTO groups (name, created_by, created_at) VALUES (?, ?, ?)",
                      (name, created_by, now()))
        
        _conn().execute("INSERT INTO group_members (group_name, username, joined_at) VALUES (?, ?, ?)",
                        (name, created_by, now()))
        _conn().commit()
        return True, ""
    except sqlite3.IntegrityError:
        return False, f"Group '{name}' already exists."
    except Exception as e:
        return False, str(e)
    
    
def join_group(group, username):
    if not _conn().execute("SELECT 1 FROM groups WHERE name = ? COLLATE NOCASE", (group, )).fetchone():
        return False, f"Group {group}' does not exist."
    
    if _conn().execute("SELECT 1 FROM group_members WHERE group_name = ? AND username = ? COLLATE NOCASE",
                       (group, username)).fetchone():
        return False, f"You are already a member of '{group}'."
    
    try:
        _conn().execute("INSERT INTO group_members (group_name, username, joined_at) VALUES (?, ?, ?)", (group, username, now()))
        _conn().commit()
        return True, ""
    except Exception as e:
        return False, str(e)
    
    
def leave_group(group, username):
    if not _conn().execute("SELECT 1 FROM groups WHERE name = ? COLLATE NOCASE", (group, )).fetchone():
        return False, f"Group '{group}' does not exist."
    
    if not _conn().execute("SELECT 1 FROM group_members WHERE group_name = ? AND username = ? COLLATE NOCASE",
                       (group, username)).fetchone():
        return False, f"You are already a member of '{group}'."
    
    _conn().execute("DELETE FROM group_members WHERE group_name = ? AND username = ? COLLATE NOCASE",
                    (group, username))
    _conn().commit()
    return True, ""


def get_members(group):
    if not _conn().execute("SELECT 1 FROM groups WHERE name = ? COLLATE NOCASE", (group, )).fetchone():
        return None
    
    rows = _conn().execute("SELECT username FROM group_members WHERE group_name = ? COLLATE NOCASE", (group, )).fetchall()
    
    return [r["username"] for r in rows]


def is_member(group, username):
    row = _conn().execute("SELECT 1 FROM group_member WHERE group_name = ? AND username = ? COLLATE NOCASE", (group, username)).fetchone()
    
    return row is not None

def  get_groups():
    rows = _conn().execute("SELECT name FROM groups").fetchall()
    return [r["name"] for r in rows]


def store_message(sender, body, recipient = None, group = None, time = None):
    if time is None:
        time = now()
    
    _conn().execute("INSERT INTO messages (sender, recipient, group_name, body, timestamp) VALUES (?, ?, ?, ?, ?)",
                    (sender, recipient, group, body, time))
    _conn().commit()
    

def store_file(sender, filename, data, recipient = None, group = None, time = None):
    if time is None:
        time = now()
        
    payload = json.dumps({"_type": "file", "filename": filename, "data": data})
    
    _conn().execute("INSERT INTO messages (sender, recipient, group_name, body, timestamp) VALUES (?, ?, ?, ?, ?)",
          (sender, recipient, group, payload, time))
    _conn().commit()
    
def is_file_body(body):
    if not body or not body.startswith("{"):
        return False

    try:
        return json.loads(body).get("_type") == "file"
    except (json.JSONDecodeError, AttributeError):
        return False
    
def parse_file(body):
    try:
        if json.loads(body).get("_type") == "file":
            return json.loads(body)["filename"], json.loads(body)["data"]
    except Exception:
        pass
    return None, None
    
    
def get_pending(username):
    rows = _conn().execute("SELECT id, sender, body, timestamp FROM messages WHERE recipient = ? COLLATE NOCASE AND group_name IS NULL ORDER BY timestamp ASC",
                           (username, )).fetchall()
    return [dict(r) for r in rows]

def delivered(username):
    _conn().execute("UPDATE messages SET recipient = '__delivered__' WHERE recipient = ? COLLATE NOCASE AND group_name IS NULL", 
                    (username, ))
    _conn().commit()
    
    
def history(user1, user2, limit=50):
    rows = _conn().execute("""SELECT sender, body, timestamp 
                           FROM messages 
                           WHERE group_name IS NULL 
                           AND ((sender = ? COLLATE NOCASE AND recipient = ? COLLATE NOCASE) 
                           OR (sender = ? COLALTE NOCASE AND recipient = ? COLLATE NOCASE))
                           ORDER BY timestamp DESC
                           LIMIT ?""", (user1, user2, user2, user1, limit)).fetchall()
    return [dict(r) for r in reversed(rows)]

def group_history(group, limit = 50):
    rows = _conn().execute("""SELECT sender, body, timestamp 
                           FROM messages 
                           WHERE group_name = ? COLLATE NOCASE
                           ORDER BY timestamp DESC
                           LIMIT ?""", (group, limit)).fetchall()
    return [dict(r) for r in reversed(rows)]