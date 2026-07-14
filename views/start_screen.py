# views/start_screen.py
import tkinter as tk
from tkinter import ttk
import theme

try:
    from network.client import NetworkClient
    from network.protocol import DEFAULT_WS_URL
    ONLINE_AVAILABLE = True
except ImportError:
    ONLINE_AVAILABLE = False

class StartScreen(tk.Frame):
    """Setup screen — supports both Local and Online game modes."""

    def __init__(self, parent, on_start_callback):
        super().__init__(parent, bg=theme.BG_MAIN)
        self.parent = parent
        self.on_start = on_start_callback
        self.net_client = None
        self.mode_var = tk.StringVar(value="local")  # "local" or "online"

        self.create_widgets()

    # ─── Layout ───────────────────────────────────────────────────────────────

    def create_widgets(self):
        # Outer card
        card = tk.Frame(self, bg=theme.BG_CONTAINER,
                        highlightthickness=1, highlightbackground=theme.COLOR_GOLD)
        card.place(relx=0.5, rely=0.5, anchor="center", width=580, height=500)

        # Header
        hdr = tk.Frame(card, bg=theme.BG_HEADER, height=75)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="♔   C H E S S   ♚",
                 font=theme.FONT_TITLE, bg=theme.BG_HEADER,
                 fg=theme.COLOR_GOLD).pack(expand=True)

        # Mode toggle row
        toggle_row = tk.Frame(card, bg=theme.BG_CONTAINER)
        toggle_row.pack(fill="x", pady=(18, 0), padx=40)

        self.local_tab_btn = self._tab_btn(toggle_row, "🖥  Local Game",  "local")
        self.local_tab_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))

        self.online_tab_btn = self._tab_btn(toggle_row, "🌐  Online Game", "online")
        self.online_tab_btn.pack(side="left", expand=True, fill="x", padx=(4, 0))

        # Content frame (swapped per mode)
        self.content_frame = tk.Frame(card, bg=theme.BG_CONTAINER)
        self.content_frame.pack(fill="both", expand=True, padx=40, pady=15)

        self._show_local_panel()

    def _tab_btn(self, parent, text, mode):
        btn = tk.Button(parent, text=text,
                        font=theme.FONT_LABEL_BOLD,
                        bg=theme.COLOR_GOLD if mode == "local" else theme.BG_PANEL,
                        fg=theme.BG_CONTAINER if mode == "local" else theme.TEXT_MUTED,
                        activebackground=theme.COLOR_GOLD,
                        activeforeground=theme.BG_CONTAINER,
                        bd=0, pady=6, cursor="hand2",
                        command=lambda m=mode: self._switch_mode(m))
        return btn

    def _switch_mode(self, mode):
        self.mode_var.set(mode)
        # Update tab colours
        if mode == "local":
            self.local_tab_btn.configure(bg=theme.COLOR_GOLD, fg=theme.BG_CONTAINER)
            self.online_tab_btn.configure(bg=theme.BG_PANEL, fg=theme.TEXT_MUTED)
            self._show_local_panel()
        else:
            self.online_tab_btn.configure(bg=theme.COLOR_GOLD, fg=theme.BG_CONTAINER)
            self.local_tab_btn.configure(bg=theme.BG_PANEL, fg=theme.TEXT_MUTED)
            self._show_online_panel()

    # ─── Local Panel ──────────────────────────────────────────────────────────

    def _show_local_panel(self):
        for w in self.content_frame.winfo_children():
            w.destroy()

        f = self.content_frame
        lbl_cfg = dict(bg=theme.BG_CONTAINER, fg=theme.TEXT_LIGHT,
                       font=theme.FONT_LABEL_BOLD, anchor="w")
        ent_cfg = dict(bg=theme.BG_PANEL, fg=theme.TEXT_LIGHT,
                       insertbackground=theme.TEXT_LIGHT, bd=0,
                       highlightthickness=1, highlightbackground=theme.BG_PANEL,
                       highlightcolor=theme.COLOR_GOLD, font=theme.FONT_LABEL)

        tk.Label(f, text="Player 1 Name (White):", **lbl_cfg).grid(
            row=0, column=0, sticky="w", pady=(10, 8))
        self.p1_entry = tk.Entry(f, **ent_cfg)
        self.p1_entry.insert(0, "Aliha")
        self.p1_entry.grid(row=0, column=1, sticky="ew", pady=(10, 8), padx=(12, 0))

        tk.Label(f, text="Player 2 Name (Black):", **lbl_cfg).grid(
            row=1, column=0, sticky="w", pady=(0, 8))
        self.p2_entry = tk.Entry(f, **ent_cfg)
        self.p2_entry.insert(0, "Zoya")
        self.p2_entry.grid(row=1, column=1, sticky="ew", pady=(0, 8), padx=(12, 0))

        tk.Label(f, text="Game Timer Format:", **lbl_cfg).grid(
            row=2, column=0, sticky="w", pady=(0, 20))

        style = ttk.Style()
        style.theme_use("default")
        style.configure("TCombobox",
                         fieldbackground=theme.BG_PANEL,
                         background=theme.BG_PANEL,
                         foreground=theme.TEXT_LIGHT,
                         arrowcolor=theme.COLOR_GOLD)
        self.timer_choices = {
            "1 Minute (Bullet)": 60, "3 Minutes (Blitz)": 180,
            "5 Minutes (Blitz)": 300, "10 Minutes (Rapid)": 600,
            "30 Minutes (Classical)": 1800, "Casual (No Timer)": 0,
        }
        self.timer_combo = ttk.Combobox(
            f, values=list(self.timer_choices.keys()),
            font=theme.FONT_LABEL, state="readonly", style="TCombobox")
        self.timer_combo.set("5 Minutes (Blitz)")
        self.timer_combo.grid(row=2, column=1, sticky="ew", pady=(0, 20), padx=(12, 0))
        f.columnconfigure(1, weight=1)

        start_btn = tk.Button(f, text="START GAME",
                              font=theme.FONT_HEADER,
                              bg=theme.COLOR_GOLD, fg=theme.BG_CONTAINER,
                              activebackground="#e5c158",
                              activeforeground=theme.BG_CONTAINER,
                              bd=0, cursor="hand2", pady=10,
                              command=self._trigger_local_start)
        start_btn.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        start_btn.bind("<Enter>", lambda e: start_btn.configure(bg="#e5c158"))
        start_btn.bind("<Leave>", lambda e: start_btn.configure(bg=theme.COLOR_GOLD))

    def _trigger_local_start(self):
        p1 = self.p1_entry.get().strip() or "Aliha"
        p2 = self.p2_entry.get().strip() or "Zoya"
        seconds = self.timer_choices.get(self.timer_combo.get(), 300)
        self.on_start(p1, p2, seconds)

    # ─── Online Panel ─────────────────────────────────────────────────────────

    def _show_online_panel(self):
        for w in self.content_frame.winfo_children():
            w.destroy()

        if not ONLINE_AVAILABLE:
            tk.Label(self.content_frame,
                     text="❌  websockets library not installed.\n\nRun in terminal:\n pip install websockets\n\nthen restart the game.",
                     font=theme.FONT_LABEL_BOLD, bg=theme.BG_CONTAINER,
                     fg="#e74c3c", justify="center").pack(expand=True)
            return

        f = self.content_frame
        lbl_cfg = dict(bg=theme.BG_CONTAINER, fg=theme.TEXT_LIGHT,
                       font=theme.FONT_LABEL_BOLD, anchor="w")
        ent_cfg = dict(bg=theme.BG_PANEL, fg=theme.TEXT_LIGHT,
                       insertbackground=theme.TEXT_LIGHT, bd=0,
                       highlightthickness=1, highlightbackground=theme.BG_PANEL,
                       highlightcolor=theme.COLOR_GOLD, font=theme.FONT_LABEL)

        # Your name
        tk.Label(f, text="Your Name:", **lbl_cfg).grid(
            row=0, column=0, sticky="w", pady=(10, 8))
        self.online_name = tk.Entry(f, **ent_cfg)
        self.online_name.insert(0, "Player")
        self.online_name.grid(row=0, column=1, columnspan=2,
                              sticky="ew", pady=(10, 8), padx=(12, 0))

        # Timer row
        tk.Label(f, text="Timer Format:", **lbl_cfg).grid(
            row=1, column=0, sticky="w", pady=(0, 15))
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TCombobox",
                         fieldbackground=theme.BG_PANEL,
                         background=theme.BG_PANEL,
                         foreground=theme.TEXT_LIGHT,
                         arrowcolor=theme.COLOR_GOLD)
        self.online_timer_choices = {
            "1 Minute (Bullet)": 60, "3 Minutes (Blitz)": 180,
            "5 Minutes (Blitz)": 300, "10 Minutes (Rapid)": 600,
            "Casual (No Timer)": 0,
        }
        self.online_timer_combo = ttk.Combobox(
            f, values=list(self.online_timer_choices.keys()),
            font=theme.FONT_LABEL, state="readonly", style="TCombobox")
        self.online_timer_combo.set("5 Minutes (Blitz)")
        self.online_timer_combo.grid(row=1, column=1, columnspan=2,
                                     sticky="ew", pady=(0, 15), padx=(12, 0))

        # Server URL (small, collapsible)
        tk.Label(f, text="Server URL:", **lbl_cfg).grid(
            row=2, column=0, sticky="w", pady=(0, 12))
        self.server_url_entry = tk.Entry(f, **ent_cfg)
        self.server_url_entry.insert(0, DEFAULT_WS_URL)
        self.server_url_entry.grid(row=2, column=1, columnspan=2,
                                   sticky="ew", pady=(0, 12), padx=(12, 0))

        f.columnconfigure(1, weight=1)
        f.columnconfigure(2, weight=1)

        # ── HOST card ────────────────────────────────────────────────────
        host_card = tk.Frame(f, bg=theme.BG_PANEL,
                             highlightthickness=1, highlightbackground=theme.BG_PANEL)
        host_card.grid(row=3, column=0, columnspan=1, sticky="nsew",
                       pady=(5, 0), padx=(0, 6), ipady=10)
        f.rowconfigure(3, weight=1)

        tk.Label(host_card, text="HOST A GAME",
                 font=theme.FONT_LABEL_BOLD, bg=theme.BG_PANEL,
                 fg=theme.COLOR_GOLD).pack(pady=(12, 6))
        tk.Label(host_card,
                 text="You play as White.\nShare the code\nwith your opponent.",
                 font=("Segoe UI", 9), bg=theme.BG_PANEL,
                 fg=theme.TEXT_MUTED, justify="center").pack(pady=(0, 8))

        self.host_btn = tk.Button(host_card, text="Host Game",
                                  font=theme.FONT_LABEL_BOLD,
                                  bg=theme.COLOR_GOLD, fg=theme.BG_CONTAINER,
                                  activebackground="#e5c158",
                                  activeforeground=theme.BG_CONTAINER,
                                  bd=0, pady=6, cursor="hand2",
                                  command=self._trigger_host)
        self.host_btn.pack(fill="x", padx=12)
        self.host_btn.bind("<Enter>", lambda e: self.host_btn.configure(bg="#e5c158"))
        self.host_btn.bind("<Leave>", lambda e: self.host_btn.configure(bg=theme.COLOR_GOLD))

        # Code display (shown after host button pressed)
        self.code_display_frame = tk.Frame(host_card, bg=theme.BG_PANEL)
        self.code_display_frame.pack(fill="x", padx=12, pady=(8, 0))

        # ── JOIN card ────────────────────────────────────────────────────
        join_card = tk.Frame(f, bg=theme.BG_PANEL,
                             highlightthickness=1, highlightbackground=theme.BG_PANEL)
        join_card.grid(row=3, column=1, columnspan=2, sticky="nsew",
                       pady=(5, 0), padx=(6, 0), ipady=10)

        tk.Label(join_card, text="JOIN A GAME",
                 font=theme.FONT_LABEL_BOLD, bg=theme.BG_PANEL,
                 fg=theme.COLOR_GOLD).pack(pady=(12, 6))
        tk.Label(join_card, text="You play as Black.\nEnter the code\nyour host shared.",
                 font=("Segoe UI", 9), bg=theme.BG_PANEL,
                 fg=theme.TEXT_MUTED, justify="center").pack(pady=(0, 8))

        self.code_entry = tk.Entry(join_card,
                                   bg=theme.BG_CONTAINER, fg=theme.TEXT_LIGHT,
                                   insertbackground=theme.TEXT_LIGHT,
                                   font=("Consolas", 16, "bold"),
                                   highlightthickness=1,
                                   highlightbackground=theme.COLOR_GOLD,
                                   justify="center", bd=0)
        self.code_entry.pack(fill="x", padx=12, pady=(0, 8))
        self.code_entry.insert(0, "ENTER CODE")
        self.code_entry.bind("<FocusIn>", lambda e: (
            self.code_entry.delete(0, tk.END) if self.code_entry.get() == "ENTER CODE" else None))

        self.join_btn = tk.Button(join_card, text="Join Game",
                                  font=theme.FONT_LABEL_BOLD,
                                  bg=theme.BG_PANEL, fg=theme.TEXT_LIGHT,
                                  activebackground=theme.COLOR_GOLD,
                                  activeforeground=theme.BG_CONTAINER,
                                  highlightthickness=1,
                                  highlightbackground=theme.COLOR_GOLD,
                                  bd=0, pady=6, cursor="hand2",
                                  command=self._trigger_join)
        self.join_btn.pack(fill="x", padx=12)
        self.join_btn.bind("<Enter>", lambda e: self.join_btn.configure(bg=theme.COLOR_GOLD, fg=theme.BG_CONTAINER))
        self.join_btn.bind("<Leave>", lambda e: self.join_btn.configure(bg=theme.BG_PANEL, fg=theme.TEXT_LIGHT))

        # Shared status bar
        self.online_status_lbl = tk.Label(f, text="",
                                          font=theme.FONT_LABEL_BOLD,
                                          bg=theme.BG_CONTAINER,
                                          fg=theme.TEXT_MUTED)
        self.online_status_lbl.grid(row=4, column=0, columnspan=3, pady=(12, 0))

    # ─── Online Action Handlers ───────────────────────────────────────────────

    def _trigger_host(self):
        name = self.online_name.get().strip() or "Player"
        url  = self.server_url_entry.get().strip() or DEFAULT_WS_URL

        self.host_btn.configure(state="disabled", text="Connecting…")
        self.online_status_lbl.configure(text="Connecting to server…", fg=theme.TEXT_MUTED)

        self.net_client = NetworkClient(url)
        self.net_client.tk_root = self.parent
        self.net_client.on_room_created = self._on_room_created
        self.net_client.on_game_start   = lambda color, opp: self._on_game_start(color, opp, name)
        self.net_client.on_error        = self._on_network_error
        self.net_client.connect_and_host(name)

    def _trigger_join(self):
        name = self.online_name.get().strip() or "Player"
        code = self.code_entry.get().strip().upper()
        url  = self.server_url_entry.get().strip() or DEFAULT_WS_URL

        if not code or code == "ENTER CODE" or len(code) < 4:
            self.online_status_lbl.configure(
                text="Please enter a valid game code.", fg="#e74c3c")
            return

        self.join_btn.configure(state="disabled", text="Connecting…")
        self.online_status_lbl.configure(text=f"Joining room {code}…", fg=theme.TEXT_MUTED)

        self.net_client = NetworkClient(url)
        self.net_client.tk_root = self.parent
        self.net_client.on_game_start = lambda color, opp: self._on_game_start(color, opp, name)
        self.net_client.on_error      = self._on_network_error
        self.net_client.connect_and_join(name, code)

    # ─── Network Callbacks ───────────────────────────────────────────────────

    def _on_room_created(self, code: str):
        """Server assigned us a room code. Display it and wait for opponent."""
        # Clear previous code display
        for w in self.code_display_frame.winfo_children():
            w.destroy()

        # Code label (big, gold, copyable)
        code_lbl = tk.Label(self.code_display_frame, text=code,
                            font=("Consolas", 22, "bold"),
                            bg=theme.BG_PANEL, fg=theme.COLOR_GOLD)
        code_lbl.pack(side="left", padx=(0, 8))

        def copy_code():
            self.parent.clipboard_clear()
            self.parent.clipboard_append(code)
            copy_btn.configure(text="✓ Copied!")
            self.parent.after(1500, lambda: copy_btn.configure(text="📋 Copy"))

        copy_btn = tk.Button(self.code_display_frame, text="📋 Copy",
                             font=theme.FONT_LABEL,
                             bg=theme.BG_CONTAINER, fg=theme.TEXT_LIGHT,
                             activebackground=theme.COLOR_GOLD,
                             activeforeground=theme.BG_CONTAINER,
                             bd=0, padx=6, cursor="hand2",
                             command=copy_code)
        copy_btn.pack(side="left")

        self.host_btn.configure(text="Waiting…")
        self.online_status_lbl.configure(
            text="⏳  Waiting for opponent to join with this code…",
            fg=theme.TEXT_MUTED)

    def _on_game_start(self, my_color: str, opponent_name: str, my_name: str):
        """Both players are ready — transition to the game screen."""
        time_limit = self.online_timer_choices.get(
            self.online_timer_combo.get(), 300) if hasattr(self, "online_timer_combo") else 300

        white_name = my_name       if my_color == "white" else opponent_name
        black_name = opponent_name if my_color == "white" else my_name

        self.on_start(white_name, black_name, time_limit,
                      network_client=self.net_client, my_color=my_color)

    def _on_network_error(self, message: str):
        """Reset buttons and show error message."""
        # Re-enable buttons
        if hasattr(self, "host_btn"):
            self.host_btn.configure(state="normal", text="Host Game")
        if hasattr(self, "join_btn"):
            self.join_btn.configure(state="normal", text="Join Game")
        self.online_status_lbl.configure(text=f"❌  {message}", fg="#e74c3c")
