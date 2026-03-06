"""
client_gui.py — LegxacyMessenger GUI Client
"""

import tkinter as tk
from tkinter import scrolledtext, filedialog, messagebox
import datetime
import os
from client import NetworkClient

BG_DEEP    = "#0A0E14"
BG_PANEL   = "#0F1923"
BG_INPUT   = "#1C2A3A"
BG_CARD    = "#162032"
ACCENT     = "#00C8FF"
ACCENT_DIM = "#0099CC"
GREEN      = "#00E676"
AMBER      = "#FFB300"
RED        = "#FF4444"
TEXT_PRI   = "#E8F1FA"
TEXT_SEC   = "#7A9BB5"
TEXT_DIM   = "#3D5A73"
DIVIDER    = "#1E3448"
FONT_BODY  = ("Courier New", 10)
FONT_SMALL = ("Courier New", 9)
FONT_INPUT = ("Courier New", 11)
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 5000


def make_button(parent, text, command, accent=True, small=False):
    return tk.Button(
        parent, text=text, command=command,
        bg=ACCENT if accent else BG_CARD,
        fg=BG_DEEP if accent else TEXT_PRI,
        activebackground=ACCENT_DIM, activeforeground=BG_DEEP,
        font=("Courier New", 9 if small else 10, "bold"),
        relief="flat", bd=0, cursor="hand2", padx=10, pady=4
    )

def make_entry(parent, show=None, width=None):
    kw = dict(bg=BG_INPUT, fg=TEXT_PRI, insertbackground=ACCENT,
              relief="flat", bd=0, font=FONT_INPUT)
    if show:  kw["show"]  = show
    if width: kw["width"] = width
    return tk.Entry(parent, **kw)


class InputDialog(tk.Toplevel):
    def __init__(self, parent, title, prompt):
        super().__init__(parent)
        self.result = None
        self.title(title)
        self.configure(bg=BG_PANEL)
        self.resizable(False, False)
        self.grab_set()
        tk.Label(self, text=prompt, bg=BG_PANEL, fg=TEXT_PRI,
                 font=FONT_BODY, pady=12, padx=20).pack()
        wrap = tk.Frame(self, bg=ACCENT, padx=1, pady=1)
        wrap.pack(padx=20, fill="x")
        self.entry = make_entry(wrap)
        self.entry.pack(fill="x")
        self.entry.focus()
        self.entry.bind("<Return>", lambda e: self._ok())
        row = tk.Frame(self, bg=BG_PANEL)
        row.pack(pady=12)
        make_button(row, "OK",     self._ok,     accent=True ).pack(side="left", padx=6)
        make_button(row, "Cancel", self.destroy, accent=False).pack(side="left")

    def _ok(self):
        self.result = self.entry.get().strip()
        self.destroy()


class LoginScreen(tk.Frame):
    def __init__(self, master, on_login):
        super().__init__(master, bg=BG_DEEP)
        self.on_login = on_login
        self._build()

    def _build(self):
        outer = tk.Frame(self, bg=BG_DEEP)
        outer.place(relx=0.5, rely=0.5, anchor="center")
        tk.Frame(outer, bg=ACCENT, height=3, width=400).pack(fill="x")
        card = tk.Frame(outer, bg=BG_PANEL, padx=44, pady=38)
        card.pack()
        tk.Label(card, text="LEGXACY", font=("Courier New", 30, "bold"),
                 bg=BG_PANEL, fg=ACCENT).pack()
        tk.Label(card, text="MESSENGER", font=("Courier New", 13),
                 bg=BG_PANEL, fg=TEXT_SEC).pack()
        tk.Frame(card, bg=DIVIDER, height=1, width=320).pack(pady=22)

        def field(label, show=None):
            row = tk.Frame(card, bg=BG_PANEL)
            row.pack(fill="x", pady=6)
            tk.Label(row, text=label, font=FONT_SMALL, bg=BG_PANEL, fg=TEXT_SEC,
                     width=12, anchor="w").pack(side="left")
            wrap = tk.Frame(row, bg=ACCENT, padx=1, pady=1)
            wrap.pack(side="left", fill="x", expand=True)
            e = make_entry(wrap, show=show, width=24)
            e.pack(fill="x")
            return e

        self.e_user = field("USERNAME")
        self.e_pass = field("PASSWORD", show="*")
        tk.Frame(card, bg=DIVIDER, height=1, width=320).pack(pady=(16, 4))

        srv = tk.Frame(card, bg=BG_PANEL)
        srv.pack(fill="x", pady=4)
        tk.Label(srv, text="SERVER", font=FONT_SMALL, bg=BG_PANEL, fg=TEXT_DIM,
                 width=12, anchor="w").pack(side="left")
        hw = tk.Frame(srv, bg=ACCENT, padx=1, pady=1)
        hw.pack(side="left")
        self.e_host = make_entry(hw, width=14)
        self.e_host.insert(0, DEFAULT_HOST)
        self.e_host.pack()
        tk.Label(srv, text=":", bg=BG_PANEL, fg=TEXT_SEC,
                 font=FONT_BODY).pack(side="left", padx=4)
        pw = tk.Frame(srv, bg=ACCENT, padx=1, pady=1)
        pw.pack(side="left")
        self.e_port = make_entry(pw, width=6)
        self.e_port.insert(0, str(DEFAULT_PORT))
        self.e_port.pack()

        self.status = tk.StringVar()
        tk.Label(card, textvariable=self.status, font=FONT_SMALL,
                 bg=BG_PANEL, fg=RED).pack(pady=(14, 2))
        make_button(card, "  CONNECT  ", self._login).pack(pady=8, ipadx=10)
        self.e_user.bind("<Return>", lambda e: self.e_pass.focus())
        self.e_pass.bind("<Return>", lambda e: self._login())
        tk.Frame(outer, bg=ACCENT_DIM, height=2, width=400).pack(fill="x")

    def _login(self):
        username = self.e_user.get().strip()
        password = self.e_pass.get().strip()
        host     = self.e_host.get().strip() or DEFAULT_HOST
        port_str = self.e_port.get().strip()
        if not username:
            self.status.set("  Username cannot be empty.")
            return
        if not password:
            self.status.set("  Password cannot be empty.")
            return
        try:
            port = int(port_str)
        except ValueError:
            self.status.set("  Port must be a number.")
            return
        self.status.set("Connecting...")
        self.after(100, lambda: self.on_login(username, password, host, port))


class ChatScreen(tk.Frame):
    def __init__(self, master, username, net=None):
        super().__init__(master, bg=BG_DEEP)
        self.username     = username
        self.net          = net
        self.current_chat = None
        self.current_type = None
        self.histories    = {}
        self._build()

    def _build(self):
        self._build_topbar()
        body = tk.Frame(self, bg=BG_DEEP)
        body.pack(fill="both", expand=True)
        self._build_sidebar(body)
        tk.Frame(body, bg=DIVIDER, width=1).pack(side="left", fill="y")
        self._build_chat_panel(body)

    def _build_topbar(self):
        bar = tk.Frame(self, bg=BG_PANEL, height=46)
        bar.pack(fill="x")
        bar.pack_propagate(False)
        tk.Label(bar, text="LEGXACY", font=("Courier New", 13, "bold"),
                 bg=BG_PANEL, fg=ACCENT).pack(side="left", padx=(16, 2), pady=12)
        tk.Label(bar, text="MESSENGER", font=("Courier New", 9),
                 bg=BG_PANEL, fg=TEXT_DIM).pack(side="left", pady=12)
        self.chat_title = tk.StringVar(value="  select a chat  ")
        tk.Label(bar, textvariable=self.chat_title,
                 font=("Courier New", 11, "bold"),
                 bg=BG_PANEL, fg=TEXT_PRI).pack(side="left", padx=28)
        tk.Label(bar, text=self.username, font=FONT_SMALL,
                 bg=BG_PANEL, fg=TEXT_SEC).pack(side="right", padx=(0, 8))
        tk.Label(bar, text="*", font=("Courier New", 14),
                 bg=BG_PANEL, fg=GREEN).pack(side="right", padx=(0, 10))
        tk.Frame(self, bg=ACCENT, height=2).pack(fill="x")

    def _build_sidebar(self, parent):
        side = tk.Frame(parent, bg=BG_PANEL, width=220)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)

        hdr = tk.Frame(side, bg=BG_PANEL)
        hdr.pack(fill="x", padx=12, pady=(16, 4))
        tk.Label(hdr, text="USERS ONLINE", font=FONT_SMALL,
                 bg=BG_PANEL, fg=TEXT_SEC).pack(side="left")
        make_button(hdr, "R", self._refresh_users,
                    accent=False, small=True).pack(side="right")

        wrap = tk.Frame(side, bg=BG_INPUT, padx=1, pady=1)
        wrap.pack(fill="x", padx=12)
        self.users_lb = tk.Listbox(wrap, bg=BG_INPUT, fg=TEXT_PRI,
                                   selectbackground=ACCENT, selectforeground=BG_DEEP,
                                   font=FONT_BODY, relief="flat", bd=0,
                                   height=7, activestyle="none")
        self.users_lb.pack(fill="x")
        self.users_lb.bind("<<ListboxSelect>>", self._on_user_click)

        tk.Frame(side, bg=DIVIDER, height=1).pack(fill="x", padx=12, pady=14)
        tk.Label(side, text="GROUPS", font=FONT_SMALL,
                 bg=BG_PANEL, fg=TEXT_SEC).pack(anchor="w", padx=12)

        btn_row = tk.Frame(side, bg=BG_PANEL)
        btn_row.pack(fill="x", padx=12, pady=(6, 6))
        make_button(btn_row, "+ CREATE", self._create_group,
                    accent=True,  small=True).pack(side="left", padx=(0, 6))
        make_button(btn_row, "> JOIN",   self._join_group,
                    accent=False, small=True).pack(side="left")

        wrap2 = tk.Frame(side, bg=BG_INPUT, padx=1, pady=1)
        wrap2.pack(fill="x", padx=12)
        self.groups_lb = tk.Listbox(wrap2, bg=BG_INPUT, fg=AMBER,
                                    selectbackground=ACCENT, selectforeground=BG_DEEP,
                                    font=FONT_BODY, relief="flat", bd=0,
                                    height=7, activestyle="none")
        self.groups_lb.pack(fill="x")
        self.groups_lb.bind("<<ListboxSelect>>", self._on_group_click)

        tk.Frame(side, bg=DIVIDER, height=1).pack(fill="x", padx=12, pady=14)
        make_button(side, "DISCONNECT", self._disconnect,
                    accent=False, small=True).pack(padx=12, anchor="w")

    def _build_chat_panel(self, parent):
        right = tk.Frame(parent, bg=BG_DEEP)
        right.pack(side="left", fill="both", expand=True)
        self.display = scrolledtext.ScrolledText(
            right, bg=BG_DEEP, fg=TEXT_PRI,
            font=FONT_BODY, relief="flat", bd=0,
            state="disabled", wrap="word", padx=12, pady=8
        )
        self.display.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        self.display.tag_config("self_name",
            foreground=ACCENT, font=("Courier New", 10, "bold"))
        self.display.tag_config("other_name",
            foreground=GREEN, font=("Courier New", 10, "bold"))
        self.display.tag_config("system_name",
            foreground=AMBER, font=("Courier New", 10, "bold"))
        self.display.tag_config("ts",  foreground=TEXT_DIM, font=("Courier New", 9))
        self.display.tag_config("msg", foreground=TEXT_PRI, font=FONT_BODY)
        tk.Frame(right, bg=DIVIDER, height=1).pack(fill="x", padx=10, pady=(8, 0))
        bar = tk.Frame(right, bg=BG_PANEL, pady=10)
        bar.pack(fill="x", padx=10, pady=(0, 10))
        make_button(bar, "[+]", self._attach,
                    accent=False, small=True).pack(side="left", padx=(0, 8))
        wrap = tk.Frame(bar, bg=ACCENT, padx=1, pady=1)
        wrap.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.msg_box = tk.Text(wrap, bg=BG_INPUT, fg=TEXT_PRI,
                               insertbackground=ACCENT, relief="flat", bd=0,
                               font=FONT_INPUT, height=2, wrap="word")
        self.msg_box.pack(fill="both")
        self.msg_box.bind("<Return>",       self._on_enter)
        self.msg_box.bind("<Shift-Return>", lambda e: None)
        make_button(bar, "SEND", self._send).pack(side="left")

    # ── Chat selection ────────────────────────────────────────────────────────

    def _on_user_click(self, event):
        sel = self.users_lb.curselection()
        if not sel:
            return
        name = self.users_lb.get(sel[0]).replace("* ", "").strip()
        self.groups_lb.selection_clear(0, "end")
        self._open_chat(name, "user")

    def _on_group_click(self, event):
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
        self.chat_title.set(f"[ {prefix}{name} ]")
        self._redraw()
        self.msg_box.focus()

    # ── Display ───────────────────────────────────────────────────────────────

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
        self.display.insert("end", f"\n{sender}", tag)
        self.display.insert("end", f"  {m.get('ts', '')}\n", "ts")
        self.display.insert("end", f"  {m['body']}\n", "msg")

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

    def show_system_message(self, text):
        if self.current_chat:
            self._add_message("system", text)

    def append_incoming(self, chat_name, sender, body, ts=""):
        """Called via after() from the receive thread when a MSG arrives."""
        entry = {"from": sender, "body": body,
                 "ts": ts or datetime.datetime.now().strftime("%H:%M")}
        self.histories.setdefault(chat_name, []).append(entry)

        # If this chat isn't open yet, open it automatically
        if self.current_chat != chat_name:
            self._add_to_users_if_new(sender)

        if self.current_chat == chat_name:
            self.display.config(state="normal")
            self._insert(entry)
            self.display.config(state="disabled")
            self.display.see("end")

    def _add_to_users_if_new(self, username):
        """Add a user to the sidebar list if they are not there yet."""
        existing = [self.users_lb.get(i) for i in range(self.users_lb.size())]
        label = f"* {username}"
        if label not in existing and username != self.username:
            self.users_lb.insert("end", label)

    # ── Send ──────────────────────────────────────────────────────────────────

    def _on_enter(self, event):
        if not (event.state & 0x1):
            self._send()
            return "break"

    def _send(self):
        if not self.current_chat:
            messagebox.showinfo("No chat", "Select a user or group first.")
            return
        text = self.msg_box.get("1.0", "end").strip()
        if not text:
            return
        self.msg_box.delete("1.0", "end")
        if self.net:
            if self.current_type == "group":
                self.net.group_msg(self.current_chat, text)
            else:
                self.net.send_msg(self.current_chat, text)
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
            self._add_message("system", f"[Attached: {os.path.basename(path)}]")

    # ── Sidebar actions ───────────────────────────────────────────────────────

    def update_users_list(self, names):
        """Repopulate the users list from a LIST_USERS response."""
        self.users_lb.delete(0, "end")
        for name in names:
            if name != self.username:
                self.users_lb.insert("end", f"* {name}")

    def _refresh_users(self):
        if self.net:
            self.net.list_users()

    def _create_group(self):
        d = InputDialog(self, "Create Group", "Group name:")
        self.wait_window(d)
        if d.result:
            if self.net:
                self.net.create_group(d.result)
            self._add_to_groups(d.result)
            self._open_chat(d.result, "group")
            self._add_message("system", f"Group '{d.result}' created.")

    def _join_group(self):
        d = InputDialog(self, "Join Group", "Group name:")
        self.wait_window(d)
        if d.result:
            if self.net:
                self.net.join_group(d.result)
            self._add_to_groups(d.result)
            self._open_chat(d.result, "group")
            self._add_message("system", f"Joined group '{d.result}'.")

    def _add_to_groups(self, name):
        existing = list(self.groups_lb.get(0, "end"))
        if f"# {name}" not in existing:
            self.groups_lb.insert("end", f"# {name}")

    def _disconnect(self):
        if messagebox.askyesno("Disconnect", "Return to login screen?"):
            if self.net:
                self.net.disconnect()
            self.master.show_login()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("LegxacyMessenger")
        self.geometry("900x620")
        self.minsize(750, 500)
        self.configure(bg=BG_DEEP)
        self.current = None
        self.show_login()

    def show_login(self):
        if self.current:
            self.current.destroy()
        self.current = LoginScreen(self, on_login=self._do_login)
        self.current.pack(fill="both", expand=True)

    def _do_login(self, username, password, host, port):
        chat = ChatScreen(self, username)

        def on_message(chat_name, sender, body, ts):
            chat.after(0, chat.append_incoming, chat_name, sender, body, ts)

        def on_notify(group_id, body):
            chat.after(0, chat.show_system_message, f"[{group_id}] {body}")

        def on_error(msg):
            chat.after(0, chat.show_system_message, f"  {msg}")

        def on_users(names):
            # Called when LIST_USERS or LIST_GROUPS response arrives
            chat.after(0, chat.update_users_list, names)

        net = NetworkClient(
            message=on_message,
            notify=on_notify,
            error=on_error,
            users=on_users
        )

        ok, err = net.connect(host, port, username, password)

        if ok:
            chat.net = net
            # Automatically fetch online users right after login
            net.list_users()
        else:
            # Preview mode
            for u in ["ethan", "samuel", "nikarlan"]:
                if u != username:
                    chat.users_lb.insert("end", f"* {u}")
            for g in ["team17", "csc3002f"]:
                chat.groups_lb.insert("end", f"# {g}")

        if self.current:
            self.current.destroy()
        self.current = chat
        self.current.pack(fill="both", expand=True)

        if not ok:
            chat._open_chat("server", "user")
            chat.show_system_message(f"Preview mode: {err}")


if __name__ == "__main__":
    App().mainloop()