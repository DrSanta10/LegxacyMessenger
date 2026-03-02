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
    

class InputDialog(tk.TopLevel):
    
class NetworkClient:    

class LegxacyApp(tk.Tk):
    

if __name__ == "__main__":
    app = LegxacyApp()
    app.mainloop()