import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
import datetime
import os

#try:
#    from protocol import send_message, receive_message, build_message, PROTOCOL_NAME
#    PROTOCOL_AVAILABLE = True
#except ImportError:
#    PROTOCOL_AVAILABLE = False
    

#Constants
BG_DEEP = "#0A0E14"
BG_PANEL = "#0F1923"
BG_CARD = "#162032"
BG_INPUT = "#1C2A3A"
TEXT_PRI = "#E8F1FA"
TEXT_SEC = "#7A9BB5"
TEXT_DIM = "#3D5A73"
ACCENT = "#00C8FF"
ACCENT_DIM = "#0099CC"
GREEN = "#00E676"
AMBER = "#FFB300"
RED = "#FF4444"
DIVIDER = "#1E3448"

FONT_MONO = ("Comfortaa", 10)
FONT_TITLE = ("Comfortaa", 22, "bold")
FONT_HEAD = ("Comfortaa", 12, "bold")
FONT_BODY = ("Comfortaa", 10)
FONT_SMALL = ("Comfortaa", 9)
FONT_INPUT = ("Comfortaa", 11)

#DEFAULT_HOST = "127.0.0.1"
#DEFAULT_PORT = 5000


def make_button(parent, text, command, accent = True, small = False):
    return tk.Button(
        parent, text = text, command = command,
        bg = ACCENT if accent else BG_CARD,
        fg = BG_DEEP if accent else TEXT_PRI,
        activebackground = ACCENT_DIM, activeforeground = BG_DEEP,
        font = ("Comfortaa", 9 if small else 10, "bold"),
        relief = "flat", bd = 0, cursor = "hand2",
        padx = 10, pady = 4
    )
    
def make_entry(parent, show = None, width = None):
    kwargs = dict(bg = BG_INPUT, fg = TEXT_PRI, insertbackground = ACCENT,
                  relief = "flat", bd = 0, font = FONT_INPUT)
    if show: kwargs["show"] = show
    if width: kwargs["width"] = width
    return tk.Entry(parent, **kwargs)

"""
def styled_button(parent, text, command, accent=True, small=False):
    fg = BG_DEEP if accent else TEXT_PRI
    bg = ACCENT if accent else BG_CARD
    size = 9 if small else 10
    btn = tk.Button(
        parent, text = text, command = command,
        bg = bg, fg = fg, activebackground = ACCENT_DIM,
        activeforeground = BG_DEEP,
        font = ("Courier New", size, "bold"),
        relief = "flat", bd = 0, cursor = "hand2", 
        padx = 10, pady = 4
    ) 
    return btn

def styled_entry(parent, **kwargs):
    return tk.Entry(
        parent, bg = BG_INPUT, fg = TEXT_PRI,
        insertbackground = ACCENT,
        relief = "flat", bd = 0,
        font = FONT_INPUT,
        **kwargs
    )
    
""" 

class InputDialog(tk.Toplevel):
    def __init__(self, parent, title, prompt):
        super().__init__(parent)
        self.result = None
        self.title(title)
        self.configure(bg = BG_PANEL)
        self.resizable(False, False)
        self.grab_set()
        
        tk.Label(self, text = prompt, bg = BG_PANEL, fg = TEXT_PRI,
                 font = FONT_BODY, pady = 12, padx = 20).pack()
        
        wrap = tk.Frame(self, bg = ACCENT, padx = 1, pady = 1)
        wrap.pack(padx = 20, fill = "x")
        self.entry = make_entry(wrap)
        self.entry.pack(fill = "x")
        self.entry.focus()
        self.entry.bind("<Return>", lambda e: self._ok())

        row = tk.Frame(self, bg = BG_PANEL)
        row.pack(pady = 12)
        make_button(row, "OK", self._ok, accent = True).pack(side = "left", padx = 6)
        make_button(row, "Cancel", self.destroy, accent = False).pack(side = "left")
        
    def _ok(self):
        self.result = self.entry.get().strip()
        self.destroy()

   
class LoginScreen(tk.Frame):
    def __init__(self, master, on_login):
        super().__init__(master, bg = BG_DEEP)
        self.on_login = on_login
        self._build()
        
    def _build(self):
        outer = tk.Frame(self, bg = BG_DEEP)
        outer.place(relx = 0.5, rely = 0.5, anchor = "center")
        
        tk.Frame(outer, bg = ACCENT, height = 3, width = 400).pack(fill = "x")
        
        card = tk.Frame(outer, bg = BG_PANEL, padx = 44, pady = 38)
        card.pack()
        
        tk.Label(card, text = "LEGXACY", 
                 font = ("Courier New", 30, "bold"), 
                 bg = BG_PANEL, fg = ACCENT).pack()
        
        tk.Label(card, text = "MESSENGER", 
                 font = ("Courier New", 13), 
                 bg = BG_PANEL, fg = TEXT_SEC).pack()
        
        tk.Frame(card, bg = DIVIDER, height = 1, width = 320).pack(pady = 22)
    
    
        def field(label, show = None):
            row = tk.Frame(card, bg = BG_PANEL)
            row.pack(fill = "x", pady = 6)
            tk.Label(row, text = label, font = FONT_SMALL, 
                     bg = BG_PANEL, fg = TEXT_SEC, 
                     width = 12, anchor = "w").pack(side = "left")
        
            wrap = tk.Frame(row, bg = ACCENT, padx = 1, pady = 1)
            wrap.pack(side = "left", fill = "x", expand = True)
            e = make_entry(wrap, show = show, width = 24)
            e.pack(fill = "x")
            return e
    
        self.entry_user = field("USERNAME")
        self.entry_pass = field("PASSWORD", show = "*")
    
        self.status = tk.StringVar()
        tk.Label(card, textvariable = self.status,
                 font = FONT_SMALL, bg = BG_PANEL, fg = RED).pack(pady = (14, 2))
    
        make_button(card, " CONNECT ", self._login).pack(pady = 8, ipadx = 10)
        
        self.entry_pass.bind("<Return>", lambda e: self._login())
        self.entry_pass.bind("<Return>", lambda e: self.entry_pass.focus())
    
        tk.Frame(outer, bg = ACCENT_DIM, height = 2, width = 400).pack(fill = "x")
    
    def _login(self):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()
        if not username:
            self.status.set("Username cannot be empty.")
            return
        if not password:
            self.status.set("Password cannot be empty.")
            return
        self.on_login(username)
    
    """    
    tk.Frame(card, bg = DIVIDER, height = 1, width = 320).pack(pady = 14)
    
    srv_row = tk.Frame(card, bg = BG_PANEL)
    srv_row.pack(fill = "x", pady = 5)
    tk.Label(srv_row, text = "SERVER", font = FONT_SMALL,
             bg = BG_PANEL, fg = TEXT_DIM, width = 12, anchor = "w").pack(side = "left")
    
    host_frame = tk.Frame(srv_row, bg = ACCENT, padx = 1, pady = 1)
    host_frame.pack(side = "left")
    self.entry_host = styled_entry(host_frame, width = 14)
    self.entry_host.insert(0, DEFAULT_HOST)
    self.entry_host.pack()
    
    tk.Label(srv_row, text = ":", bg = BG_PANEL, fg = TEXT_SEC,
             font = FONT_BODY).pack(side = "left", padx = 4)
    
    port_frame = tk.Frame(srv_row, bg = ACCENT, padx = 1, pady = 1)
    port_frame.pack(side = "left")
    self.entry_port = styled_entry(port_frame, width = 6)
    self.entry_port.insert(0, str(DEFAULT_PORT))
    self.entry_port.pack()
    
    
    self.status_var = tk.StringVar(value = "")
    tk.Label(card, textvariable = self.status_var, font = FONT_SMALL,
             bg = BG_PANEL, fg = RED).pack(pady = (14, 4))
    
    btn = styled_button(card, " CONNECT ", self._attempt_login)
    btn.pack(pady = 8, ipadx = 10)
    """
    
    """
def _attempt_login(self):
    username = self.entry_user.get().strip()
    password = self.entry_pass.get().strip()
    host = self.entry_host.get().strip() or DEFAULT_HOST
    port_str = self.entry_port.get().strip()
    
    if not username:
        self.status_var.set("Username cannot be empty!")
        return    
        
    if not password:
        self.status_var.set("Password cannot be empty!")
        return
    
    try:
        port = int(port_str)
    except ValueError:
        self.status_var.set("Port must be a number.")
        return
    
    self.status_var.set("Connecting...")
    self.after(100, lambda: self.on_login(username, password, host, port))
    
    """
    
class ChatScreen(tk.Frame):
    def __init__(self, master, username, network_client = None):
        super().__init__(master, bg = BG_DEEP)
        self.username = username
        #self.net = network_client
        self.current_chat = None
        self.current_type = None
        self.chat_hisotires = {}
        self._build()
        self._load_demo_data()
        
    def _build(self):
        self._build_topbar()
        
        body = tk.Frame(self, bg = BG_DEEP)
        body.pack(fill = "both", expand = True)
        
        self._build_sidebar(body)
        tk.Frame(body, bg = DIVIDER, width = 1).pack(side = "left", fill = "y")
        
        self._build_chat_area(body)
        
    def _build_topbar(self):
        bar = tk.Frame(self, bg =BG_PANEL, height = 46)
        bar.pack(fill = "x")
        bar.pack_propagate(False)
        
        tk.Label(bar, text = "LEGXACY", 
                font = ("Comfortaa", 13, "bold"), 
                bg = BG_PANEL, fg = ACCENT).pack(side = "left", padx = (16, 2), pady = 12)
        tk.Label(bar, text = "MESSENGER", 
                font = ("Comfortaa", 9), 
                bg = BG_PANEL, fg = TEXT_DIM).pack(side = "left", pady = 12)
        
        self.chat_title = tk.StringVar(value = "select a chat")
        tk.Label(bar, textvariable = self.chat_title, 
                font = ("Comfortaa", 11, "bold"), 
                bg = BG_PANEL, fg = TEXT_PRI).pack(side = "left", padx = 28)
        
        tk.Label(bar, text = f"{self.username} ", font = FONT_SMALL,
                bg = BG_PANEL, fg = TEXT_SEC).pack(side = "right", padx = (0, 8))
        tk.Label(bar, text = "•", 
                font = ("Comfortaa", 14), 
                bg = BG_PANEL, fg = GREEN).pack(side = "right", padx = (0, 10))
        
        tk.Frame(self, bg = ACCENT, height = 2).pack(fill = "x")
        
    def _build_sidebar(self, parent):
        side = tk.Frame(parent, bg = BG_PANEL, width = 220)
        side.pack(side = "left", fill = "y")
        side.pack_propagate(False)
    
        tk.Label(side, text = "USERS ONLINE", font = FONT_SMALL,
                     bg = BG_PANEL, fg = TEXT_SEC).pack(anchor = "w", padx = 12, pady = (16, 4))
        
        wrap = tk.Frame(side, bg = BG_INPUT, padx = 1, pady = 1)
        wrap.pack(fill = "x", padx = 12)
        self.users_list = tk.Listbox(
                wrap, bg = BG_INPUT, fg=TEXT_PRI, 
                selectbackground = ACCENT, selectforeground = BG_DEEP, 
                font = FONT_BODY, relief = "flat", 
                bd = 0, height = 7, activestyle = "none"
        )
        
        self.users_list.pack(fill = "x")
        self.users_list.bind("<<ListboxSelect>>", self._on_user_select)
        
        tk.Frame(side, bg = DIVIDER, height = 1).pack(fill = "x", padx = 12, pady = 14)
        
        tk.Label(side, text = "GROUPS", font = FONT_SMALL, 
                     bg = BG_PANEL, fg = TEXT_SEC).pack(anchor = "w", padx = 12)
        
        grp_buttons = tk.Frame(side, bg = BG_PANEL)
        grp_buttons.pack(fill = "x", padx = 12, pady = (6, 6))
        make_button(grp_buttons, "+ CREATE", self._create_group, 
                          accent = True, small = True).pack(side = "left", padx = (0, 6))
        make_button(grp_buttons, "> JOIN", self._join_group, 
                          accent = False, small = True).pack(side = "left")
        
        wrap2 = tk.Frame(side, bg = BG_INPUT, padx = 1, pady = 1)
        wrap2.pack(fill = "x", padx = 12)
        self.groups_list = tk.Listbox(
                wrap2, bg = BG_INPUT, fg = AMBER,
                selectbackground = ACCENT, selectforeground = BG_DEEP,
                font = FONT_BODY, relief = "flat", bd = 0,
                height = 7, activestyle = "none"
            )
        
        self.groups_list.pack(fill = "x")
        self.groups_list.bind("<<ListboxSelect>>", self._on_group_select)
        
        tk.Frame(side, bg = DIVIDER, height = 1).pack(fill = "x", padx = 12, pady = 14)
        
        make_button(side, "DISCONNECT", self._disconnect, 
                    accent = False, small = True).pack(padx = 12, anchor = "w")
        
        #tk.Frame(parent, bg = DIVIDER, width = 1).pack(side = "left", fill = "y")
        
    def _build_chat_area(self, parent):
        right = tk.Frame(parent, bg = BG_DEEP)
        right.pack(side = "left", fill = "both", expand = True)
        
        #history_frame = tk.Frame(right, bg = BG_DEEP)
        #history_frame.pack(fill = "both", expand = True, padx = 12, pady = (10, 0))
        
        self.chat_display = scrolledtext.ScrolledText(
            right, bg = BG_DEEP, fg = TEXT_PRI,
            font = FONT_BODY, relief = "flat", bd = 0,
            state = "disabled", wrap = "word",
            padx = 12, pady = 8
        )
        
        self.chat_display.pack(fill = "both", expand = True, padx = 10, pady = (10, 0))
        
        self.chat_display.tag_config("sender_self", 
                                     foreground = ACCENT,
                                     font = ("Comfortaa", 10, "bold"))
        self.chat_display.tag_config("sender_other", 
                                     foreground = GREEN,
                                     font = ("Comfortaa", 10, "bold"))
        self.chat_display.tag_config("sender_system", 
                                     foreground = AMBER,
                                     font = ("Comfortaa", 10, "bold"))
        self.chat_display.tag_config("timestamp", 
                                     foreground = TEXT_DIM,
                                     font = ("Comfortaa", 9))
        self.chat_display.tag_config("body_text", 
                                     foreground = TEXT_PRI,
                                     font = FONT_BODY)
        self.chat_display.tag_config("error_text", 
                                     foreground = RED,
                                     font = FONT_SMALL)
        
        tk.Frame(right, bg = DIVIDER, height = 1).pack(fill = "x", padx = 10, pady = (8, 0))
        
        input_bar = tk.Frame(right, bg = BG_PANEL, pady = 10)
        input_bar.pack(fill = "x", padx = 10, pady = (0, 10))
        
        make_button(input_bar, "/", self._attach, 
                      accent = False, small = True).pack(side = "left", padx = (0, 8))
        
        entry_wrap = tk.Frame(input_bar, bg = ACCENT, padx = 1, pady = 1)
        entry_wrap.pack(side = "left", fill = "x", expand = True, padx = (0, 8))
        self.msg_entry = tk.Text(
                entry_wrap, bg = BG_INPUT, fg = TEXT_PRI,
                insertbackground = ACCENT, relief = "flat", bd = 0,
                font = FONT_INPUT, height = 2, wrap = "word"
        )
        
        self.msg_entry.pack(fill = "both")
        self.msg_entry.bind("<Return>", self._on_return_key)
        self.msg_entry.bind("<Shift-Return>", lambda e: None)
    
        make_button(input_bar, "SEND", self._send).pack(side = "left")
        
        
    
        
#event handlers
    def _on_return_key(self, event):
        if not (event.state & 0x1):
            self._send()
            return "break"
    
    def _on_user_select(self, event):
        sel = self.users_lb.curselection()
        if not sel:
            return
        name = self.users_lb.get(sel[0]).replace("* ", "").strip()
        self.groups_lb.selection_clear(0, "end")
        self._open_chat(name, "user")
        
    def _on_group_select(self, event):
        sel = self.groups_lb.curselection()
        if not sel:
            return
        name = self.groups_lb.get(sel[0]).replace("# ", "").strip()
        self.users_lb.selection_clear(0, "end")
        self._open_chat(name, "group")
        
    def _open_chat(self, name, chat_type):
        self.current_chat = name
        self.current_type = chat_type
        prefix = "#" if chat_type == "group" else "@"
        self.chat_title.set("[ " + prefix + name + " ]")
        self._redraw()
        self.msg_box.focus()
        
    
    def _redraw(self):
        self.display.config(state="normal")
        self.display.delete("1.0", "end")
        for m in self.histories.get(self.current_chat, []):
            self._insert(m)
        self.display.config(state="disabled")
        self.display.see("end")

    def _insert(self, m):
        sender = m["from"]
        if sender == self.username:
            tag = "self_name"
        elif sender == "system":
            tag = "system_name"
        else:
            tag = "other_name"
        self.display.insert("end", "\n" + sender, tag)
        self.display.insert("end", "  " + m.get("ts", "") + "\n", "ts")
        self.display.insert("end", "  " + m["body"] + "\n", "msg")

    def _add_message(self, sender, body):
        if not self.current_chat:
            return
        ts    = datetime.datetime.now().strftime("%H:%M")
        entry = {"from": sender, "body": body, "ts": ts}
        self.histories.setdefault(self.current_chat, []).append(entry)
        self.display.config(state="normal")
        self._insert(entry)
        self.display.config(state="disabled")
        self.display.see("end")

    def _send(self):
        if not self.current_chat:
            messagebox.showinfo("No chat", "Select a user or group first.")
            return
        text = self.msg_box.get("1.0", "end").strip()
        if not text:
            return
        self.msg_box.delete("1.0", "end")
        self._add_message(self.username, text)

    def _attach(self):
        path = filedialog.askopenfilename(
            title="Attach file",
            filetypes=[("Images", "*.png *.jpg *.jpeg"),
                       ("Audio",  "*.mp3 *.wav"),
                       ("Video",  "*.mp4"),
                       ("All",    "*.*")]
        )
        if path:
            self._add_message("system", "[Attached: " + os.path.basename(path) + "]")

    def _create_group(self):
        d = InputDialog(self, "Create Group", "Group name:")
        self.wait_window(d)
        if d.result:
            self._add_to_groups(d.result)
            self._open_chat(d.result, "group")
            self._add_message("system", "Group '" + d.result + "' created.")

    def _join_group(self):
        d = InputDialog(self, "Join Group", "Group name:")
        self.wait_window(d)
        if d.result:
            self._add_to_groups(d.result)
            self._open_chat(d.result, "group")
            self._add_message("system", "Joined group '" + d.result + "'.")

    def _add_to_groups(self, name):
        existing = list(self.groups_lb.get(0, "end"))
        if "# " + name not in existing:
            self.groups_lb.insert("end", "# " + name)

    def _disconnect(self):
        if messagebox.askyesno("Disconnect", "Return to login screen?"):
            self.master.show_login()

#class InputDialog(tk.TopLevel):
    
#class NetworkClient:    

"""
class LegxacyApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LegxacyMessenger")
        self.geometry("900x620")
        self.minsize(750, 520)
        self.configure(bg = BG_DEEP)
        #self._set_icon()
        self.current_frame = None
        self.show_login()
        
    def show_login(self):
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = LoginScreen(self, on_login = self._handle_login)
        self.current_frame.pack(fill = "both", expand = True)
    
    def _handle_login(self, username, password, host, port):
        if PROTOCOL_AVAIABLE:
            self._connect_and_login(username, password, host, port)
        else:
            self._open_chat_screen(username, network_client = None)
            
    def _connect_and_login(self, username, password, host, port):
        def _connect():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(5)
                sock.connect((host, port))
                sock.settimeout(None)
                
                send_message(sock, "LOGIN", "/server", 
                             headers = {"From": username, "Password": password})
                resp = receive_message(sock)
                
                if resp["status_code"] == 200:
                    self.after(0, self._open_chat_screen, username, sock)
                elif resp["status_code"] == 409:
                    self.after(0, self._login_error, "Username already in use. Choose another.")
                    sock.close()
                else:
                    body = resp.get("body", "Login failed.")
                    self.after(0, self._login_error, body)
                    sock.close()
                    
            except ConnectionRefusedError:
                self.after(0, self._login_error, 
                           f"Cannot connect to {host}:{port}")
            except socket.timeout:
                self.after(0, self._login_error, "Connection timed out.")
            except Exception as e:
                self.after(0, self._login_error, str(e))
        
        threading.Thread(target = _connect, daemon = True).start()

"""

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LegxacyMessenger")
        self.geometry("900x620")
        self.minsize(750, 500)
        self.configure(bg = BG_DEEP)
        self.current = None
        self.show_login()

    def show_login(self):
        if self.current:
            self.current.destroy()
        self.current = LoginScreen(self, on_login = self._do_login)
        self.current.pack(fill = "both", expand = True)

    def _do_login(self, username):
        if self.current:
            self.current.destroy()
        self.current = ChatScreen(self, username)
        self.current.pack(fill = "both", expand = True)

if __name__ == "__main__":
    App().mainloop()