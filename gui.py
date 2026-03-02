import tkinter as tk
from tkinter import ttk, scrolledtext, fialedlog, messagebox
import threading
import socket
import os
import sys

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
FONT_MONO = ("Courier New", 10)
FONT_TITLE = ("Courier New", 22, "bold")
FONT_HEAD = ("Courier New", 12, "bold")
FONT_BODY = ("Courier New", 10)
FONT_SMALL = ("Courier New", 9)
FONT_INPUT = ("Courier New", 11)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000


def styled_button(parent, text, command, accent=True, small=False):
    fg = BG_DEEP if accent else TEXT_PRI
    bg = ACCENT if accent else BG_CARD
    size = 9 if small else 10
    btn = tk.Button(
        parent, text = text, command = command
        bg = bg, fg = fg, activebackground = ,
        activeforeground = ,
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
    
    
class LoginScreen(tk.Frame):
    def __init__(self, master, on_login):
        super().__init__(master, bg = BG_DEEP)
        self.on_login = on_login
        self.build()
        
    def _build(self):
        outer = tk.Frame(self, bg = BG_DEEP)
        outer.place(relx = 0.5, rely = 0.5, anchor = "center")
        
        bar = tk.Frame(outer, bg = ACCENT, height = 3, width = 400)
        bar.pack(fill = "x")
        
        card = tk.Frame(outer, bg = BG_PANEL, padx = 40, pady = 36)
        card.pack()
        
        tk.Label(card, text = "LEGXACY", font = ("Courier New", 28, "bold"), 
                 bg = BG_PANEL, fg = ACCENT).pack()
        
        tk.Label(card, text = "MESSENGER", font = ("Courier New", 14), 
                 bg = BG_PANEL, fg = TEXT_SEC, pady = 0).pack()
        
        tk.Frame(card, bg = DIVIDER, height = 1, width = 320).pack(pady = 20)
    
    
    def field(label_text, show = None):
        row = tk.Frame(card, bg = BG_PANEL)
        row.pack(fill = "x", pady = 5)
        tk.Label(row, text = label_text, font = FONT_SMALL, 
                 bg = BG_PANEL, fg = TEXT_SEC, width = 12, anchor = "w").pack(side = "left")
        
        entry_frame = tk.Frame(row, bg = ACCENT, padx = 1, pady = 1)
        entry_frame.pack(side = "left", fill = "x", expand = True)
        e = styled_entry(entry_frame, show = show, width = 22)
        e.pack(fill = "x")
        return e
    
    self.entry_user = field("USERNAME")
    self.entry_pass = field("PASSWORD", show = "*")
    
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
    
    self.entry_pass.bind("<Return>", lambda e: self._attempt_login())
    self.entry_pass.bind("<Return>", lambda e: self.entry_pass.focus())
    
    tk.Frame(outer, bg = ACCENT_DIM, height = 2, width = 400).pack(fill = "x")
    
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
    
    
class ChatScreen(tk.Frame):
    def __init__(self, master, username, network_client = None):
        super().__init__(master, bg = BG_DEEP)
        self.username = username
        self.net = network_client
        self.current_chat = None
        self.current_type = None
        self.chat_hisotires = {}
        self._build()
        
    def _build(self):
        self._build_top_bar()
        
        body = tk.Frame(self, bg = BG_DEEP)
        body.pack(fill = "both", expand = True)
        
        self._build_left_panel(body)
        self._build_chat_area(body)
        
    def _build_top_bar(self):
        bar = tk.Frame(self, bg =BG_PANEL, height = 44)
        bar.pack(fill = "x")
        bar.pack_propagate(False)
        
        tk.Label(bar, text = "LEGXACY", font = ("Courier New", 13, "bold"), 
                 bg = BG_PANEL, fg = ACCENT).pack(side = "left", padx = (16, 2), pady = 10)
        tk.Label(bar, text = "MESSENGER", font = ("Courier New", 9), 
                 bg = BG_PANEL, fg = TEXT_DIM).pack(side = "left", pady = 10)
        
        self.char_title_var = tk.StringVar(value = "no chat selected")
        tk.Label(bar, textvariable = self.char_title_var, 
                 font = ("Courier New", 11, "bold"), 
                 bg = BG_PANEL, fg = TEXT_PRI).pack(side = "left", padx = 30)
        
        tk.Label(bar, text = f"{self.username} ", font = FONT_SMALL,
                 bg = BG_PANEL, fg = TEXT_SEC).pack(side = "right", padx = (0, 4))
        
        self.status_dot = tk.Label(bar, text = "•", font = ("Courier New", 14), bg = BG_PANEL, fg = GREEN)
        self.status_dot.pack(side = "right", padx = (0, 12))
        
        tk.Frame(self, bg = ACCENT, height = 2).pack(fill = "x")
        
    def _build_left_panel(self, parent):
        panel = tk.Frame(parent, bg = BG_PANEL, width = 220)
        panel.pack(side = "left", fill = "y")
        panel.pack_propagate(False)
    
        users_header = tk.Frame(panel, bg = BG_PANEL)
        users_header.pack(fill = "x", padx = 10, pady = (14, 4))
        tk.Label(users_header, text = "USERS ONLINE", font = FONT_SMALL,
                 bg = BG_PANEL, fg = TEXT_SEC).pack(side = "left")
        styled_button(users_header, "<=>", self._refresh_users, 
                      accent = False, small = True).pack(side = "right")
        
        user_frame = tk.Frame(panel, bg = BG_INPUT, padx = 1, pady = 1)
        user_frame.pack(fill = "x", padx = 10)
        self.users_list = tk.Listbox(
            user_frame, bg = BG_INPUT, fg=TEXT_PRI, selectbackground = ACCENT,
            selectforeground = BG_DEEP, font = FONT_BODY, relief = "flat", 
            bd = 0, height = 7, activestyle = "none"
        )
        
        self.users_list.pack(fill = "x")
        self.users_list.bind("<<ListboxSelect>>", self._on_user_select)
        
        tk.Frame(panel, bg = DIVIDER, height = 1).pack(fill = "x", padx = 10, pady = 12)
        
        grp_header = tk.Frame(panel, bg = BG_PANEL)
        grp_header.pack(fill = "x", padx = 10, pady = (0, 4))
        tk.Label(grp_header, text = "GROUPS", font = FONT_SMALL, 
                 bg = BG_PANEL, fg = TEXT_SEC).pack(side = "left")
        
        grp_buttons = tk.Frame(panel, bg = BG_PANEL)
        grp_buttons.pack(fill = "x", padx = 10, pady = (0, 6))
        styled_button(grp_buttons, "+ CREATE", self._create_group, 
                      accent = True, small = True).pack(side = "left", padx = (0, 4))
        styled_button(grp_buttons, "-> JOIN", self._join_group, 
                      accent = False, small = True).pack(side = "left")
        
        group_frame = tk.Frame(panel, bg = BG_INPUT, padx = 1, pady = 1)
        group_frame.pack(fill = "x", padx = 10)
        self.groups_list = tk.Listbox(
            group_frame, bg = BG_INPUT, fg = AMBER
            selectbackground = ACCENT, selectforeground = BG_DEEP,
            font = FONT_BODY, relief = "flat", bd = 0,
            height = 7, activestyle = "none"
        )
        
        self.groups_list.pack(fill = "x")
        self.groups_list.bind("<<ListboxSelect>>", self._on_group_select)
        
        tk.Frame(panel, bg = DIVIDER, height = 1).pack(fill = "x", padx = 10, pady = 12)
        
        styled_button(panel, "DISCONNECT", self._disconnect, accent = False, small = True).pack(padx = 10, anchor = "w")
        
        tk.Frame(parent, bg = DIVIDER, width = 1).pack(side = "left", fill = "y")
        
    def _build_chat_area(self, parent):
        right = tk.Frame(parent, bg = BG_DEEP)
        right.pack(side = "left", fill = "both", expand = True)
        
        history_frame = tk.Frame(right, bg = BG_DEEP)
        history_frame.pack(fill = "both", expand = True, padx = 12, pady = (10, 0))
        
        self.chat_display = scrolledtext.ScrolledText(
            history_frame,
            bg = BG_DEEP, fg = TEXT_PRI,
            font = FONT_BODY, relief = "flat", bd = 0,
            state = "disabled", wrap = "word",
            insertbackground = ACCENT
        )
        
        self.chat_display.pack(fill = "both", expand = True)
        
        self.chat_display.tag_config("sender_self", 
                                     foreground = ACCENT,
                                     font = ("Courier New", 10, "bold"))
        self.chat_display.tag_config("sender_other", 
                                     foreground = GREEN,
                                     font = ("Courier New", 10, "bold"))
        self.chat_display.tag_config("sender_system", 
                                     foreground = AMBER,
                                     font = ("Courier New", 10, "bold"))
        self.chat_display.tag_config("timestamp", 
                                     foreground = TEXT_DIM,
                                     font = ("Courier New", 9))
        self.chat_display.tag_config("body_text", 
                                     foreground = TEXT_PRI,
                                     font = FONT_BODY)
        self.chat_display.tag_config("error_text", 
                                     foreground = RED,
                                     font = FONT_SMALL)
        
        tk.Frame(right, bg = DIVIDER, height = 1).pack(fill = "x", padx = 12, pady = (8, 0))
        
        input_bar = tk.Frame(right, bg = BG_PANEL, pady = 10)
        input_bar.pack(fill = "x", padx = 12, pady = (0, 10))
        
        styled_button(input_bar, "/", self._attach_file, 
                      accent = False, small = True).pack(side = "left", padx = (0, 6))
        
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
        
        styled_button(input_bar, "SEND >", self._send_message).pack(side = "left")
        
#event handlers
    def _on_return_key(self, event):
        
    def _on_user_select(self, event):
        
    def _on_group_select(self, event):
        

class InputDialog(tk.TopLevel):
    
class NetworkClient:    

class LegxacyApp(tk.Tk):
    

if __name__ == "__main__":
    app = LegxacyApp()
    app.mainloop()