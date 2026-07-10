#!/usr/bin/env python3

import sys
import os
import gzip
import concurrent.futures
import urllib.request
import urllib.error
import json
import io
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
from datetime import datetime
import webbrowser
import queue
import time
import ssl
import socket
import http.client
from urllib.parse import urlparse
import struct

try:
    from tkinterweb import HtmlFrame
except ImportError:
    HtmlFrame = None

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class OTAProberGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OTA Prober")
        self.root.geometry("1000x900")
        self.root.configure(bg='#f0f0f0')

        self.setup_styles()
        self.create_widgets()
        self.query_thread = None
        self.keyscan_thread = None

        self._setup_layout_independent_shortcuts()

        # Для брутфорсу
        self._brute_log_buffer = []
        self._brute_log_window = None
        self._brute_log_text = None

    def _setup_layout_independent_shortcuts(self):
        """
        Робить Ctrl+C / Ctrl+V / Ctrl+X / Ctrl+A робочими незалежно від
        поточної розкладки клавіатури (укр., рос., будь-яка інша).

        Стандартні tkinter-біндинги спрацьовують по keysym (символу),
        а символ 'c' існує лише в латинській розкладці, тому Control-c
        не збігається, коли розкладка не англійська.

        Тут натомість перевіряємо event.char: коли затиснутий Ctrl,
        ОС генерує ASCII control-char (Ctrl+C -> '\\x03', Ctrl+V -> '\\x16',
        Ctrl+X -> '\\x18', Ctrl+A -> '\\x01') незалежно від розкладки,
        бо це визначається позицією клавіші, а не її символом.
        """
        CTRL_CHARS = {
            'copy':  '\x03',
            'paste': '\x16',
            'cut':   '\x18',
            'all':   '\x01',
        }
        KEYSYMS = {
            'copy':  {'c', 'C'},
            'paste': {'v', 'V'},
            'cut':   {'x', 'X'},
            'all':   {'a', 'A'},
        }

        def get_focused_text_widget():
            w = self.root.focus_get()
            if isinstance(w, (tk.Entry, ttk.Entry, tk.Text, scrolledtext.ScrolledText)):
                return w
            return None

        def do_copy(event):
            w = get_focused_text_widget()
            if w is None:
                return
            try:
                if isinstance(w, (tk.Entry, ttk.Entry)):
                    if w.selection_present():
                        text = w.selection_get()
                    else:
                        return
                else:
                    text = w.get(tk.SEL_FIRST, tk.SEL_LAST)
                self.root.clipboard_clear()
                self.root.clipboard_append(text)
            except tk.TclError:
                pass
            return "break"

        def do_paste(event):
            w = get_focused_text_widget()
            if w is None:
                return
            try:
                clip = self.root.clipboard_get()
            except tk.TclError:
                return "break"
            try:
                if isinstance(w, (tk.Entry, ttk.Entry)):
                    if w.selection_present():
                        w.delete(tk.SEL_FIRST, tk.SEL_LAST)
                    w.insert(tk.INSERT, clip)
                else:
                    if w.tag_ranges(tk.SEL):
                        w.delete(tk.SEL_FIRST, tk.SEL_LAST)
                    w.insert(tk.INSERT, clip)
            except tk.TclError:
                pass
            return "break"

        def do_cut(event):
            w = get_focused_text_widget()
            if w is None:
                return
            try:
                if isinstance(w, (tk.Entry, ttk.Entry)):
                    if not w.selection_present():
                        return "break"
                    text = w.selection_get()
                    self.root.clipboard_clear()
                    self.root.clipboard_append(text)
                    w.delete(tk.SEL_FIRST, tk.SEL_LAST)
                else:
                    if not w.tag_ranges(tk.SEL):
                        return "break"
                    text = w.get(tk.SEL_FIRST, tk.SEL_LAST)
                    self.root.clipboard_clear()
                    self.root.clipboard_append(text)
                    w.delete(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                pass
            return "break"

        def do_select_all(event):
            w = get_focused_text_widget()
            if w is None:
                return
            try:
                if isinstance(w, (tk.Entry, ttk.Entry)):
                    w.selection_range(0, tk.END)
                else:
                    w.tag_add(tk.SEL, '1.0', tk.END)
            except tk.TclError:
                pass
            return "break"

        def matches(event, action):
            if event.char == CTRL_CHARS[action]:
                return True
            ks = event.keysym
            if (event.state & 0x4) and ks in KEYSYMS[action]:
                return True
            return False

        def on_key(event):
            if matches(event, 'copy'):
                return do_copy(event)
            if matches(event, 'paste'):
                return do_paste(event)
            if matches(event, 'cut'):
                return do_cut(event)
            if matches(event, 'all'):
                return do_select_all(event)

        # ВАЖЛИВО: без add='+', щоб цей обробник ПОВНІСТЮ замінював
        # стандартну поведінку tkinter, а не додавався до неї.
        # Інакше при англійській розкладці спрацьовують ОБИДВА обробники
        # (і стандартний <<Paste>>, і наш) -> текст вставляється двічі.
        self.root.bind_all('<Key>', on_key)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        style.configure('Header.TLabel', font=('Arial', 12, 'bold'), background='#f0f0f0')
        style.configure('Normal.TLabel', font=('Arial', 10), background='#f0f0f0')
        style.configure('Title.TLabel', font=('Arial', 14, 'bold'), background='#f0f0f0')

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        title = ttk.Label(main_frame, text="Android OTA Prober", style='Title.TLabel')
        title.bind('<Button-1>', lambda e: messagebox.showinfo("RYuh", "hold on, im licking some bilds..."))
        title.grid(row=0, column=0, columnspan=3, pady=(0, 20), sticky=tk.W)

        input_frame = ttk.LabelFrame(main_frame, text="Device Fingerprint", padding="10")
        input_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))

        ttk.Label(input_frame, text="Enter fingerprint:", style='Normal.TLabel').grid(row=0, column=0, sticky=tk.W, pady=5)

        self.fingerprint_var = tk.StringVar()
        self.fingerprint_entry = ttk.Entry(input_frame, textvariable=self.fingerprint_var, width=70, font=('Courier', 10))
        self.fingerprint_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        self.fingerprint_entry.insert(0, "google/shamu/shamu:5.1/LYZ28E/1858530:user/release-keys")

        ttk.Label(input_frame, text="Format: oem/product/device:api/build_tag/incremental:build_type/key_type",
                  style='Normal.TLabel', foreground='#666666').grid(row=2, column=0, sticky=tk.W)

        input_frame.columnconfigure(0, weight=1)

        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))

        self.json_var = tk.BooleanVar(value=False)
        self.json_check = ttk.Checkbutton(options_frame, text="Output as JSON", variable=self.json_var)
        self.json_check.grid(row=0, column=0, sticky=tk.W, padx=5)

        self.save_var = tk.BooleanVar(value=False)
        self.save_check = ttk.Checkbutton(options_frame, text="Save to file", variable=self.save_var)
        self.save_check.grid(row=0, column=1, sticky=tk.W, padx=5)

        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))

        self.query_button = ttk.Button(button_frame, text="Query Device", command=self.on_query_click)
        self.query_button.pack(side=tk.LEFT, padx=5)

        self.keyscan_button = ttk.Button(button_frame, text="Scan Key Types", command=self.on_keyscan_click)
        self.keyscan_button.pack(side=tk.LEFT, padx=5)

        self.clear_button = ttk.Button(button_frame, text="Clear Output", command=self.on_clear_click)
        self.clear_button.pack(side=tk.LEFT, padx=5)

        self.copy_button = ttk.Button(button_frame, text="Copy to Clipboard", command=self.on_copy_click)
        self.copy_button.pack(side=tk.LEFT, padx=5)

        self.status_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, foreground='#0066cc', style='Normal.TLabel')
        self.status_label.grid(row=4, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))

        output_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        output_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 0))

        header_frame = ttk.Frame(output_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        self.status_icon_var = tk.StringVar(value="")
        self.status_icon_label = ttk.Label(header_frame, textvariable=self.status_icon_var, font=('Arial', 16))
        self.status_icon_label.pack(side=tk.LEFT, padx=(0, 10))

        self.ota_link_label = ttk.Label(header_frame, text="", font=('Courier', 10))
        self.ota_link_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.ota_link_label.bind('<Button-1>', self.on_header_link_click)

        self.notebook = ttk.Notebook(output_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        self.desc_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.desc_frame, text="Description")

        if HtmlFrame:
            self.html_frame = HtmlFrame(self.desc_frame)
            self.html_frame.pack(fill=tk.BOTH, expand=True)
            self.desc_text = None
        else:
            self.desc_text = scrolledtext.ScrolledText(
                self.desc_frame,
                wrap=tk.WORD,
                width=120,
                height=20,
                font=('Arial', 10),
                bg='white',
                fg='#333333'
            )
            self.desc_text.pack(fill=tk.BOTH, expand=True)
            self.html_frame = None

        self.log_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.log_frame, text="Full Log")

        self.output_text = scrolledtext.ScrolledText(
            self.log_frame,
            wrap=tk.WORD,
            width=120,
            height=20,
            font=('Courier', 9),
            bg='white',
            fg='#333333'
        )
        self.output_text.pack(fill=tk.BOTH, expand=True)

        self.output_text.tag_configure('header', foreground='#0066cc', font=('Courier', 10, 'bold'))
        self.output_text.tag_configure('success', foreground='#006600', font=('Courier', 9, 'bold'))
        self.output_text.tag_configure('error', foreground='#cc0000', font=('Courier', 9, 'bold'))
        self.output_text.tag_configure('info', foreground='#666666', font=('Courier', 9))
        self.output_text.tag_configure('link', foreground='#0066cc', font=('Courier', 9, 'underline'))
        self.output_text.tag_configure('section', foreground='#004499', font=('Courier', 10, 'bold'))

        self.output_text.tag_bind('link', '<Button-1>', self.on_link_click)
        self.output_text.tag_bind('link', '<Enter>', lambda e: self.output_text.config(cursor='hand2'))
        self.output_text.tag_bind('link', '<Leave>', lambda e: self.output_text.config(cursor='xterm'))

        self.url_map = {}
        self.current_ota_link = None

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(5, weight=1)

        # --- Raw Response tab ---
        self.raw_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.raw_frame, text="Raw Response")
        self._build_raw_tab()

        # --- HTTP INFO TAB ---
        self.httpinfo_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.httpinfo_frame, text="HTTP Info")
        self._build_httpinfo_tab()

        # --- BRUTEFORCE TAB ---
        self.brute_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.brute_frame, text="Bruteforce")
        self._build_bruteforce_tab()

    # ── Raw Response tab ───────────────────────────────────────────────────
    def _build_raw_tab(self):
        wrapper = ttk.Frame(self.raw_frame, padding="4")
        wrapper.pack(fill=tk.BOTH, expand=True)

        toolbar = ttk.Frame(wrapper)
        toolbar.pack(fill=tk.X, pady=(0, 4))

        self.raw_view_var = tk.StringVar(value="human")

        ttk.Radiobutton(toolbar, text="Human-readable",
                        variable=self.raw_view_var, value="human",
                        command=self._raw_switch_view).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Radiobutton(toolbar, text="Hex dump",
                        variable=self.raw_view_var, value="hex",
                        command=self._raw_switch_view).pack(side=tk.LEFT, padx=(0, 16))

        ttk.Button(toolbar, text="💾  Save Human",
                   command=lambda: self._raw_save("human")).pack(side=tk.LEFT, padx=(0, 4))
        ttk.Button(toolbar, text="💾  Save Hex",
                   command=lambda: self._raw_save("hex")).pack(side=tk.LEFT)

        self.raw_text = scrolledtext.ScrolledText(
            wrapper,
            wrap=tk.NONE,
            font=('Courier', 9),
            bg='white',
            fg='#333333'
        )
        self.raw_text.pack(fill=tk.BOTH, expand=True)

        self._raw_human = ""
        self._raw_hex = ""

    def _raw_populate(self, human: str, hex_: str):
        self._raw_human = human
        self._raw_hex = hex_
        self._raw_switch_view()

    def _raw_switch_view(self):
        content = self._raw_human if self.raw_view_var.get() == "human" else self._raw_hex
        self.raw_text.config(state=tk.NORMAL)
        self.raw_text.delete(1.0, tk.END)
        self.raw_text.insert(tk.END, content)
        self.raw_text.see("1.0")

    def _raw_save(self, mode: str):
        content = self._raw_human if mode == "human" else self._raw_hex
        if not content:
            messagebox.showinfo("Raw Response", "No data to save yet.")
            return
        ext = "_human.txt" if mode == "human" else "_hex.txt"
        script_dir = os.path.dirname(os.path.abspath(__file__))
        path = filedialog.asksaveasfilename(
            initialdir=script_dir,
            initialfile=f"raw_response{ext}",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.update_status(f"Saved to {path}", 'success')

    # ── Auto-populate URL ──────────────────────────────────────────────────
    def _meta_autofill_url(self, url: str):
        self.httpinfo_url_var.set(url)

    # ── HTTP Info tab ──────────────────────────────────────────────────────
    def _build_httpinfo_tab(self):
        wrapper = ttk.Frame(self.httpinfo_frame, padding="8")
        wrapper.pack(fill=tk.BOTH, expand=True)

        url_lf = ttk.LabelFrame(wrapper, text="OTA URL", padding="6")
        url_lf.pack(fill=tk.X, pady=(0, 6))
        self.httpinfo_url_var = tk.StringVar()
        ttk.Entry(url_lf, textvariable=self.httpinfo_url_var,
                  font=('Courier', 9)).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.httpinfo_fetch_btn = ttk.Button(url_lf, text="▶  Fetch",
                                             command=self._httpinfo_start)
        self.httpinfo_fetch_btn.pack(side=tk.LEFT)

        self.httpinfo_status_var = tk.StringVar(value="Enter an OTA URL and press Fetch")
        ttk.Label(wrapper, textvariable=self.httpinfo_status_var,
                  foreground='#0066cc').pack(anchor=tk.W, pady=(0, 4))
        self.httpinfo_progress = ttk.Progressbar(wrapper, mode='indeterminate')
        self.httpinfo_progress.pack(fill=tk.X, pady=(0, 6))

        self.httpinfo_nb = ttk.Notebook(wrapper)
        self.httpinfo_nb.pack(fill=tk.BOTH, expand=True)

        def _make_tree(parent, col1="Field", col2="Value"):
            f = ttk.Frame(parent)
            cols = ("field", "value")
            tv = ttk.Treeview(f, columns=cols, show="headings")
            tv.heading("field", text=col1)
            tv.heading("value", text=col2)
            tv.column("field", width=260, stretch=False)
            tv.column("value", width=560, stretch=True)
            sb = ttk.Scrollbar(f, orient=tk.VERTICAL, command=tv.yview)
            tv.configure(yscrollcommand=sb.set)
            tv.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            sb.pack(side=tk.RIGHT, fill=tk.Y)

            def _copy_value(event):
                sel = tv.selection()
                if not sel:
                    return
                value = tv.item(sel[0], 'values')[1]
                self.root.clipboard_clear()
                self.root.clipboard_append(value)
                self.httpinfo_status_var.set(f"Copied: {value[:80]}{'…' if len(value) > 80 else ''}")

            def _copy_row(event):
                sel = tv.selection()
                if not sel:
                    return
                k, v = tv.item(sel[0], 'values')
                self.root.clipboard_clear()
                self.root.clipboard_append(f"{k}: {v}")
                self.httpinfo_status_var.set(f"Copied row: {k}")

            tv.bind('<ButtonRelease-1>', _copy_value)
            tv.bind('<Double-ButtonRelease-1>', _copy_row)
            return f, tv

        gen_f, self.hi_tree_general = _make_tree(self.httpinfo_nb, "Property", "Value")
        self.httpinfo_nb.add(gen_f, text="General")

        hdr_f, self.hi_tree_headers = _make_tree(self.httpinfo_nb, "Header", "Value")
        self.httpinfo_nb.add(hdr_f, text="Response Headers")

        redir_f, self.hi_tree_redirects = _make_tree(self.httpinfo_nb, "#", "URL")
        self.httpinfo_nb.add(redir_f, text="Redirect Chain")

        sec_f, self.hi_tree_security = _make_tree(self.httpinfo_nb, "Property", "Value")
        self.httpinfo_nb.add(sec_f, text="Security / TLS")

        tim_f, self.hi_tree_timing = _make_tree(self.httpinfo_nb, "Phase", "ms")
        self.httpinfo_nb.add(tim_f, text="Timing")

    def _httpinfo_start(self):
        url = self.httpinfo_url_var.get().strip()
        if not url:
            messagebox.showerror("HTTP Info", "Please enter an OTA URL first.")
            return
        self.httpinfo_fetch_btn.config(state=tk.DISABLED)
        self.httpinfo_progress.start(12)
        self.httpinfo_status_var.set("Probing…")
        threading.Thread(target=self._httpinfo_worker, args=(url,), daemon=True).start()

    def _httpinfo_worker(self, url):
        try:
            result = probe_ota_url(url, status_cb=lambda m: self.root.after(
                0, self.httpinfo_status_var.set, m))
            self.root.after(0, self._httpinfo_display, result)
        except Exception as exc:
            self.root.after(0, self.httpinfo_status_var.set, f"Error: {exc}")
        finally:
            self.root.after(0, self._httpinfo_done)

    def _httpinfo_done(self):
        self.httpinfo_progress.stop()
        self.httpinfo_fetch_btn.config(state=tk.NORMAL)

    def _httpinfo_display(self, r: dict):
        def _fill(tree, rows):
            for ch in tree.get_children():
                tree.delete(ch)
            for k, v in rows:
                tree.insert("", tk.END, values=(k, v))

        _fill(self.hi_tree_general, r.get('general', []))
        _fill(self.hi_tree_headers, r.get('headers', []))
        _fill(self.hi_tree_redirects,
              [(str(i+1), u) for i, u in enumerate(r.get('redirects', []))])
        _fill(self.hi_tree_security, r.get('security', []))
        _fill(self.hi_tree_timing, r.get('timing', []))

        summary = r.get('summary', '')
        self.httpinfo_status_var.set(summary)

    # ── Bruteforce tab ─────────────────────────────────────────────────────
    def _build_bruteforce_tab(self):
        wrapper = ttk.Frame(self.brute_frame, padding="8")
        wrapper.pack(fill=tk.BOTH, expand=True)

        btn_row = ttk.Frame(wrapper)
        btn_row.pack(fill=tk.X, pady=(0, 4))
        self.brute_start_btn = ttk.Button(btn_row, text="▶  Start Bruteforce", command=self._brute_start)
        self.brute_pause_btn = ttk.Button(btn_row, text="⏸  Pause", command=self._brute_pause, state=tk.DISABLED)
        self.brute_continue_btn = ttk.Button(btn_row, text="⏩  Continue", command=self._brute_continue, state=tk.DISABLED)
        self.brute_stop_btn = ttk.Button(btn_row, text="⏹  Stop", command=self._brute_stop, state=tk.DISABLED)
        self.brute_clear_log_btn = ttk.Button(btn_row, text="🗑  Clear Log", command=self._brute_clear_log)
        self.brute_open_log_btn = ttk.Button(btn_row, text="📋  Open Log Window", command=self._open_brute_log_window)
        for btn in (self.brute_start_btn, self.brute_pause_btn, self.brute_continue_btn,
                    self.brute_stop_btn, self.brute_clear_log_btn, self.brute_open_log_btn):
            btn.pack(side=tk.LEFT, padx=3)
        self.brute_status_var = tk.StringVar(value="Idle — fill in settings below, then press Start Bruteforce")
        ttk.Label(btn_row, textvariable=self.brute_status_var, foreground='#0066cc').pack(side=tk.LEFT, padx=10)

        self.brute_progress = ttk.Progressbar(wrapper, mode='determinate')
        self.brute_progress.pack(fill=tk.X, pady=(0, 6))

        fp_lf = ttk.LabelFrame(wrapper, text="Fingerprint Template", padding="6")
        fp_lf.pack(fill=tk.X, pady=(0, 6))
        ttk.Label(fp_lf, text="Use {BUILD}, {INC} and {KEY} as placeholders:").pack(anchor=tk.W)
        self.brute_fp_var = tk.StringVar(
            value="google/baracus/baracus:6.0/{BUILD}/{INC}:{KEY}"
        )
        ttk.Entry(fp_lf, textvariable=self.brute_fp_var, font=('Courier', 9)).pack(fill=tk.X, pady=3)
        ttk.Label(fp_lf, text="{BUILD} = build ID   {INC} = incremental   {KEY} = key type",
                  foreground='#666666').pack(anchor=tk.W)

        # Three columns: Build Tags | Key Types | Incremental Range
        mid = ttk.Frame(wrapper)
        mid.pack(fill=tk.X, pady=(0, 6))
        mid.columnconfigure(0, weight=3)
        mid.columnconfigure(1, weight=2)
        mid.columnconfigure(2, weight=1)

        # --- Build Tags (колонка 0) ---
        bt_lf = ttk.LabelFrame(mid, text="Build Tags  (one per line)", padding="6")
        bt_lf.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 6))
        self.brute_tags_text = tk.Text(bt_lf, height=4, font=('Courier', 9))
        self.brute_tags_text.pack(fill=tk.BOTH, expand=True)
        self.brute_tags_text.insert(tk.END, "MRTA.181211.008")

        # --- Key Types (колонка 1) ---
        kt_lf = ttk.LabelFrame(mid, text="Key Types  (one per line)", padding="6")
        kt_lf.grid(row=0, column=1, sticky=tk.NSEW, padx=(0, 6))
        self.brute_keys_text = tk.Text(kt_lf, height=4, font=('Courier', 9))
        self.brute_keys_text.pack(fill=tk.BOTH, expand=True)
        self.brute_keys_text.insert(tk.END,
            "user/release-keys\nuser/test-keys")

        # --- Incremental Range (колонка 2) ---
        inc_lf = ttk.LabelFrame(mid, text="Incremental Range", padding="6")
        inc_lf.grid(row=0, column=2, sticky=tk.NSEW)
        inc_lf.columnconfigure(1, weight=1)
        self.brute_inc_start_var = tk.StringVar(value="370000")
        self.brute_inc_end_var = tk.StringVar(value="400000")
        self.brute_inc_step_var = tk.StringVar(value="1")
        for row_i, (lbl, var) in enumerate(zip(
                ["Start:", "End:", "Step:"],
                [self.brute_inc_start_var, self.brute_inc_end_var, self.brute_inc_step_var])):
            ttk.Label(inc_lf, text=lbl).grid(row=row_i, column=0, sticky=tk.W, pady=3)
            ttk.Entry(inc_lf, textvariable=var, width=12).grid(row=row_i, column=1, sticky=tk.EW, padx=(6, 0), pady=3)

        opt_lf = ttk.LabelFrame(wrapper, text="Options", padding="6")
        opt_lf.pack(fill=tk.X, pady=(0, 6))
        self.brute_stop_on_find_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_lf, text="Pause on find (press Continue to resume)",
                        variable=self.brute_stop_on_find_var).pack(side=tk.LEFT, padx=8)
        self.brute_skip_dupes_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(opt_lf, text="Skip duplicate OTA URLs",
                        variable=self.brute_skip_dupes_var).pack(side=tk.LEFT, padx=8)
        self.brute_save_otas_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(opt_lf, text="Save OTAs.txt",
                        variable=self.brute_save_otas_var).pack(side=tk.LEFT, padx=8)
        ttk.Label(opt_lf, text="Parallel workers:").pack(side=tk.LEFT, padx=(16, 4))
        self.brute_workers_var = tk.StringVar(value="10")
        ttk.Spinbox(opt_lf, from_=1, to=1000, textvariable=self.brute_workers_var, width=5).pack(side=tk.LEFT)

        # Internal state
        self._brute_stop_flag = False
        self._brute_pause_event = threading.Event()
        self._brute_found_data = {}
        self._brute_found_count = 0
        self._brute_queue = None
        self._brute_producer_thread = None
        self._brute_worker_threads = []
        self._brute_progress_lock = threading.Lock()
        self._brute_processed = 0
        self._brute_total = 0
        self._brute_running = False

        # Очищаємо буфер логу
        self._brute_log_buffer = []

    # ── Bruteforce log window ─────────────────────────────────────────────
    def _open_brute_log_window(self):
        if self._brute_log_window is not None and self._brute_log_window.winfo_exists():
            self._brute_log_window.lift()
            self._brute_log_window.focus_force()
            return

        win = tk.Toplevel(self.root)
        win.title("Bruteforce Log")
        win.geometry("900x600")
        win.protocol("WM_DELETE_WINDOW", self._close_brute_log_window)

        frame = ttk.Frame(win, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        text = scrolledtext.ScrolledText(frame, wrap=tk.WORD, font=('Courier', 9), bg='white', fg='#333')
        text.pack(fill=tk.BOTH, expand=True)

        # Налаштування тегів (таких самих як у головному лозі)
        text.tag_configure('found', foreground='#006600', font=('Courier', 9, 'bold'))
        text.tag_configure('skip', foreground='#aaaaaa')
        text.tag_configure('error', foreground='#cc0000')
        text.tag_configure('header', foreground='#004499', font=('Courier', 9, 'bold'))
        text.tag_configure('info', foreground='#333333')
        text.tag_configure('changed', foreground='#cc6600', font=('Courier', 9, 'bold'))

        # Вставляємо вже накопичений буфер
        for line, tag in self._brute_log_buffer:
            text.insert(tk.END, line + '\n', tag)
        text.see(tk.END)

        # Зберігаємо посилання
        self._brute_log_window = win
        self._brute_log_text = text

    def _close_brute_log_window(self):
        if self._brute_log_window:
            self._brute_log_window.destroy()
            self._brute_log_window = None
            self._brute_log_text = None

    # ── Bruteforce log helpers ────────────────────────────────────────────
    def _brute_log(self, msg, tag='info'):
        # Зберігаємо в буфер
        self._brute_log_buffer.append((msg, tag))
        # Якщо вікно відкрите – вставляємо
        if self._brute_log_text and self._brute_log_window and self._brute_log_window.winfo_exists():
            self._brute_log_text.insert(tk.END, msg + '\n', tag)
            self._brute_log_text.see(tk.END)

    def _brute_clear_log(self):
        """Clear the log buffer and the log window if open."""
        self._brute_log_buffer.clear()
        if self._brute_log_text and self._brute_log_window and self._brute_log_window.winfo_exists():
            self._brute_log_text.delete(1.0, tk.END)

    # ── Bruteforce control ────────────────────────────────────────────────
    def _brute_pause(self):
        if not self._brute_running:
            return
        self._brute_pause_event.clear()
        self.brute_pause_btn.config(state=tk.DISABLED)
        self.brute_continue_btn.config(state=tk.NORMAL)
        self.brute_stop_btn.config(state=tk.NORMAL)
        self.brute_status_var.set("⏸ Paused — press Continue to resume")

    def _brute_continue(self):
        if not self._brute_running:
            return
        self._brute_pause_event.set()
        self.brute_continue_btn.config(state=tk.DISABLED)
        self.brute_pause_btn.config(state=tk.NORMAL)
        self.brute_stop_btn.config(state=tk.NORMAL)
        self.brute_status_var.set("Resuming...")

    def _brute_stop(self):
        if not self._brute_running:
            return
        self._brute_stop_flag = True
        self._brute_pause_event.set()
        self.brute_status_var.set("Stopping...")
        self.brute_stop_btn.config(state=tk.DISABLED)
        self.brute_pause_btn.config(state=tk.DISABLED)
        self.brute_continue_btn.config(state=tk.DISABLED)

    def _brute_start(self):
        if self._brute_running:
            self._brute_stop()
            time.sleep(0.2)

        template = self.brute_fp_var.get().strip()
        use_build = '{BUILD}' in template
        use_inc = '{INC}' in template
        use_key = '{KEY}' in template

        raw_tags = self.brute_tags_text.get("1.0", tk.END).strip()
        build_tags = [t.strip() for t in raw_tags.splitlines() if t.strip()]
        if not build_tags:
            if use_build:
                build_tags = ["DEFAULT"]
            else:
                build_tags = [""]

        raw_keys = self.brute_keys_text.get("1.0", tk.END).strip()
        key_types = [k.strip() for k in raw_keys.splitlines() if k.strip()]
        if not key_types:
            if use_key:
                key_types = ["user/release-keys"]
            else:
                key_types = [""]

        try:
            inc_start_str = self.brute_inc_start_var.get().strip()
            inc_end_str = self.brute_inc_end_var.get().strip()
            inc_step_str = self.brute_inc_step_var.get().strip()
            if inc_start_str and inc_end_str and use_inc:
                inc_start = int(inc_start_str)
                inc_end = int(inc_end_str)
                inc_step = int(inc_step_str) if inc_step_str else 1
                if inc_step <= 0:
                    inc_step = 1
            else:
                inc_start, inc_end, inc_step = 0, 0, 1
        except ValueError:
            inc_start, inc_end, inc_step = 0, 0, 1

        if use_inc:
            inc_count = (inc_end - inc_start) // inc_step + 1
        else:
            inc_count = 1
        build_count = len(build_tags) if use_build else 1
        key_count = len(key_types) if use_key else 1
        total = build_count * key_count * inc_count
        if total == 0:
            total = 1

        self._brute_stop_flag = False
        self._brute_pause_event.set()
        self._brute_found_data.clear()
        self._brute_found_count = 0
        self._brute_processed = 0
        self._brute_total = total

        # Clear log
        self._brute_clear_log()

        self.brute_start_btn.config(state=tk.DISABLED)
        self.brute_pause_btn.config(state=tk.NORMAL)
        self.brute_continue_btn.config(state=tk.DISABLED)
        self.brute_stop_btn.config(state=tk.NORMAL)
        self.brute_progress['maximum'] = total
        self.brute_progress['value'] = 0

        self._brute_log(f"Starting bruteforce: {total} combinations", 'header')
        self._brute_log(f"Template: {template}", 'header')
        self._brute_log("=" * 70, 'header')

        try:
            n_workers = max(1, min(1000, int(self.brute_workers_var.get())))
        except ValueError:
            n_workers = 10

        self._brute_queue = queue.Queue(maxsize=n_workers * 2)

        self._brute_producer_thread = threading.Thread(
            target=self._brute_producer,
            args=(build_tags, key_types, inc_start, inc_end, inc_step, template, n_workers,
                  use_build, use_inc, use_key),
            daemon=True
        )
        self._brute_producer_thread.start()

        self._brute_worker_threads = []
        for _ in range(n_workers):
            t = threading.Thread(target=self._brute_worker, daemon=True)
            t.start()
            self._brute_worker_threads.append(t)

        self._brute_running = True
        self.root.after(500, self._brute_monitor)

    def _brute_producer(self, build_tags, key_types, inc_start, inc_end, inc_step, template, n_workers,
                        use_build, use_inc, use_key):
        try:
            builds = build_tags if use_build else [""]
            keys = key_types if use_key else [""]
            if use_inc:
                inc_values = range(inc_start, inc_end + 1, inc_step)
            else:
                inc_values = [0]

            for bt in builds:
                for inc in inc_values:
                    for kt in keys:
                        if self._brute_stop_flag:
                            break
                        self._brute_queue.put((bt, kt, str(inc) if use_inc else "", template), block=True)
                    if self._brute_stop_flag:
                        break
                if self._brute_stop_flag:
                    break
        finally:
            for _ in range(n_workers):
                self._brute_queue.put(None)

    def _brute_worker(self):
        while True:
            self._brute_pause_event.wait()
            if self._brute_stop_flag:
                break
            try:
                item = self._brute_queue.get(timeout=0.5)
            except queue.Empty:
                continue
            if item is None:
                break
            build_tag, key_type, inc, template = item
            fp = template
            if '{BUILD}' in template:
                fp = fp.replace('{BUILD}', build_tag)
            if '{INC}' in template:
                fp = fp.replace('{INC}', inc)
            if '{KEY}' in template:
                fp = fp.replace('{KEY}', key_type)

            max_retries = 3
            for attempt in range(max_retries):
                if self._brute_stop_flag:
                    break
                self._brute_pause_event.wait()
                if self._brute_stop_flag:
                    break
                try:
                    settings, _raw = perform_checkin(fp)
                    if not settings:
                        if attempt == max_retries - 1:
                            self._brute_log(f"  BUILD={build_tag} KEY={key_type} INC={inc} → no response (after {max_retries} retries)", 'skip')
                            self._brute_increment_progress()
                        else:
                            time.sleep(1)
                        continue
                    ota = find_ota_link(settings)
                    self._brute_process_result(fp, build_tag, key_type, inc, ota)
                    self._brute_increment_progress()
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        self._brute_log(f"  BUILD={build_tag} KEY={key_type} INC={inc} → ERROR: {e} (after {max_retries} retries)", 'error')
                        self._brute_increment_progress()
                    else:
                        time.sleep(1)

    def _brute_increment_progress(self):
        with self._brute_progress_lock:
            self._brute_processed += 1
            self.brute_progress['value'] = self._brute_processed
            self.brute_status_var.set(
                f"[{self._brute_processed}/{self._brute_total}]  "
                f"found={self._brute_found_count} keys, unique={len(self._brute_found_data)}"
            )

    def _brute_process_result(self, fp, build_tag, key_type, inc, ota):
        skip_dupes = self.brute_skip_dupes_var.get()
        pause_on_find = self.brute_stop_on_find_var.get()
        save_otas = self.brute_save_otas_var.get()

        if ota is None:
            self._brute_log(f"  BUILD={build_tag} KEY={key_type} INC={inc} → no OTA", 'skip')
            return
        url = ota.get('url')
        if not url:
            self._brute_log(f"  BUILD={build_tag} KEY={key_type} INC={inc} → no OTA URL", 'skip')
            return

        title = ota.get('title', '')
        desc = ota.get('description', '')
        size = ota.get('size', '')
        meta = (title, desc, size)

        with self._brute_progress_lock:
            self._brute_found_count += 1

        with self._brute_progress_lock:
            old_meta = self._brute_found_data.get(url)
            is_new = old_meta is None
            is_changed = False if is_new else (meta != old_meta)
            if is_new:
                self._brute_found_data[url] = meta
            elif is_changed:
                self._brute_found_data[url] = meta
            else:
                if skip_dupes:
                    self._brute_log(f"  BUILD={build_tag} KEY={key_type} INC={inc} → OTA found (duplicate URL, skipped from unique)", 'found')
                else:
                    self._brute_log(f"  BUILD={build_tag} KEY={key_type} INC={inc} → OTA found (duplicate URL, but metadata same)", 'found')
                return

        if is_new:
            local_count = len(self._brute_found_data)
            self._brute_log(f"", 'found')
            self._brute_log(f"  ★ NEW #{local_count}  BUILD={build_tag}  KEY={key_type}  INC={inc}", 'found')
            self._brute_log(f"    Fingerprint : {fp}", 'found')
            self._brute_log(f"    URL         : {url}", 'found')
            if title:
                self._brute_log(f"    Title       : {title}", 'found')
            if desc:
                self._brute_log(f"    Description : {desc[:80]}{'...' if len(desc)>80 else ''}", 'found')
            if size:
                self._brute_log(f"    Size        : {size}", 'found')
            self._brute_log(f"", 'found')
        elif is_changed:
            old_title, old_desc, old_size = old_meta
            local_count = len(self._brute_found_data)
            self._brute_log(f"", 'changed')
            self._brute_log(f"  ⚡ UPDATED #{local_count}  BUILD={build_tag}  KEY={key_type}  INC={inc}", 'changed')
            self._brute_log(f"    Fingerprint : {fp}", 'changed')
            self._brute_log(f"    URL         : {url}", 'changed')
            if old_title != title:
                self._brute_log(f"    Title (old) : {old_title}", 'changed')
                self._brute_log(f"    Title (new) : {title}", 'changed')
            if old_desc != desc:
                self._brute_log(f"    Description (old): {old_desc[:80]}{'...' if len(old_desc)>80 else ''}", 'changed')
                self._brute_log(f"    Description (new): {desc[:80]}{'...' if len(desc)>80 else ''}", 'changed')
            if old_size != size:
                self._brute_log(f"    Size (old)  : {old_size}", 'changed')
                self._brute_log(f"    Size (new)  : {size}", 'changed')
            self._brute_log(f"", 'changed')

        # Зберігаємо в OTAs.txt тільки якщо ввімкнено
        if save_otas:
            try:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                otas_path = os.path.join(script_dir, "OTAs.txt")
                with open(otas_path, 'a', encoding='utf-8') as f:
                    f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
                    if is_changed:
                        f.write(" [UPDATED]")
                    f.write("\n")
                    f.write(f"  Fingerprint : {fp}\n")
                    f.write(f"  URL         : {url}\n")
                    if title:
                        f.write(f"  Title       : {title}\n")
                    if desc:
                        f.write(f"  Description : {desc}\n")
                    if size:
                        f.write(f"  Size        : {size}\n")
                    f.write("\n")
                self._brute_log(f"    Saved to OTAs.txt", 'info')
            except Exception as e:
                self._brute_log(f"    Could not save to OTAs.txt: {e}", 'error')

        if pause_on_find:
            self._brute_pause_event.clear()
            self.brute_pause_btn.config(state=tk.DISABLED)
            self.brute_continue_btn.config(state=tk.NORMAL)
            self.brute_stop_btn.config(state=tk.NORMAL)
            self.brute_status_var.set(f"⏸ Paused after {'new' if is_new else 'metadata'} find #{local_count} — press Continue")

    def _brute_monitor(self):
        if self._brute_stop_flag:
            self._brute_finish(stop=True)
            return
        if self._brute_producer_thread and self._brute_producer_thread.is_alive():
            self.root.after(500, self._brute_monitor)
            return
        alive = any(t.is_alive() for t in self._brute_worker_threads)
        if alive:
            self.root.after(500, self._brute_monitor)
            return
        self._brute_finish(stop=False)

    def _brute_finish(self, stop=False):
        if stop:
            self._brute_log("=" * 70, 'header')
            self._brute_log("Bruteforce stopped by user.", 'header')
            self.brute_status_var.set("Stopped by user.")
        else:
            self._brute_log("=" * 70, 'header')
            self._brute_log(f"Bruteforce finished. Found {self._brute_found_count} OTA(s) for different keys, unique URLs: {len(self._brute_found_data)}.", 'header')
            self.brute_status_var.set(f"Done — {self._brute_found_count} keys with OTA, {len(self._brute_found_data)} unique.")
        self.brute_start_btn.config(state=tk.NORMAL)
        self.brute_pause_btn.config(state=tk.DISABLED)
        self.brute_continue_btn.config(state=tk.DISABLED)
        self.brute_stop_btn.config(state=tk.DISABLED)
        self._brute_running = False

    # ── Query / Key scan core ─────────────────────────────────────────────
    def update_status(self, message, status_type='info'):
        self.status_var.set(message)
        if status_type == 'error':
            self.status_label.configure(foreground='#cc0000')
        elif status_type == 'success':
            self.status_label.configure(foreground='#006600')
        else:
            self.status_label.configure(foreground='#0066cc')
        self.root.update()

    def log_output(self, text, tag='info'):
        self.output_text.insert(tk.END, text + '\n', tag)
        self.output_text.see(tk.END)
        self.root.update()

    def log_link(self, display_text, url):
        link_id = f"link_{len(self.url_map)}"
        self.url_map[link_id] = url
        self.output_text.insert(tk.END, display_text, (link_id, 'link'))
        self.output_text.see(tk.END)
        self.root.update()

    def on_link_click(self, event):
        try:
            index = self.output_text.index(f"@{event.x},{event.y}")
            tags = self.output_text.tag_names(index)
            for tag in tags:
                if tag in self.url_map:
                    url = self.url_map[tag]
                    webbrowser.open(url)
                    return
        except:
            pass

    def on_header_link_click(self, event):
        if self.current_ota_link:
            webbrowser.open(self.current_ota_link)

    def on_clear_click(self):
        self.output_text.delete(1.0, tk.END)
        if self.html_frame:
            self.html_frame.load_html("")
        elif self.desc_text:
            self.desc_text.delete(1.0, tk.END)
        self.raw_text.delete(1.0, tk.END)
        self._raw_human = ""
        self._raw_hex = ""
        self.status_icon_var.set("")
        self.ota_link_label.config(text="")
        self.current_ota_link = None
        self.update_status("Output cleared")

    def on_copy_click(self):
        try:
            content = self.output_text.get(1.0, tk.END)
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.update_status("Copied to clipboard", 'success')
        except Exception as e:
            self.update_status(f"Failed to copy: {e}", 'error')

    def on_query_click(self):
        fingerprint = self.fingerprint_var.get().strip()
        if not fingerprint:
            messagebox.showerror("Error", "Please enter a fingerprint")
            return
        if '/' not in fingerprint:
            messagebox.showerror("Error", "Invalid fingerprint format")
            return

        self.query_button.config(state=tk.DISABLED)
        self.keyscan_button.config(state=tk.DISABLED)
        self.clear_button.config(state=tk.DISABLED)
        self.fingerprint_entry.config(state=tk.DISABLED)

        self.query_thread = threading.Thread(target=self.perform_query, args=(fingerprint,), daemon=True)
        self.query_thread.start()

    def perform_query(self, fingerprint):
        try:
            self.output_text.delete(1.0, tk.END)
            self.raw_text.delete(1.0, tk.END)
            if self.html_frame:
                self.html_frame.load_html("")
            elif self.desc_text:
                self.desc_text.delete(1.0, tk.END)
            self.url_map.clear()
            self.current_ota_link = None
            self.update_status("Parsing fingerprint...")

            parsed = parse_fingerprint(fingerprint)
            self.update_status("Sending check-in request...")

            settings, raw_bytes = perform_checkin(fingerprint)

            if not settings:
                self.log_output("ERROR: Check-in failed - No response from server", 'error')
                self.status_icon_var.set("❌")
                self.update_status("Query failed", 'error')
            else:
                if raw_bytes:
                    human_dump, hex_dump = format_raw_response(raw_bytes)
                else:
                    fallback = json.dumps(settings, indent=2, sort_keys=True)
                    human_dump, hex_dump = fallback, fallback
                self._raw_populate(human_dump, hex_dump)

                build_info = extract_build_details(fingerprint, settings)
                ota_link = find_ota_link(settings)

                if self.json_var.get():
                    json_data = {
                        'fingerprint': fingerprint,
                        'build_info': build_info,
                        'ota_link': ota_link,
                        'total_settings': len(settings),
                    }
                    output_str = json.dumps(json_data, indent=2)
                    self.log_output(output_str)
                    if self.html_frame:
                        html_content = f"<pre>{output_str}</pre>"
                        self.html_frame.load_html(html_content)
                    elif self.desc_text:
                        self.desc_text.insert(tk.END, output_str)
                else:
                    self.format_and_log_output(fingerprint, settings, build_info, ota_link)

                if self.save_var.get():
                    if self.json_var.get():
                        output_str = json.dumps({
                            'fingerprint': fingerprint,
                            'build_info': build_info,
                            'ota_link': ota_link,
                            'total_settings': len(settings),
                        }, indent=2)
                    else:
                        output_str = self.output_text.get(1.0, tk.END)
                    self.save_output(output_str, fingerprint)

                self.update_status("Query completed successfully", 'success')

        except ValueError as e:
            self.log_output(f"ERROR: {e}", 'error')
            self.status_icon_var.set("❌")
            self.update_status("Invalid fingerprint format", 'error')
        except Exception as e:
            self.log_output(f"ERROR: {e}", 'error')
            self.status_icon_var.set("❌")
            self.update_status(f"Error: {e}", 'error')
        finally:
            self.query_button.config(state=tk.NORMAL)
            self.keyscan_button.config(state=tk.NORMAL)
            self.clear_button.config(state=tk.NORMAL)
            self.fingerprint_entry.config(state=tk.NORMAL)

    def save_output(self, content, fingerprint):
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"ota_report_{timestamp}.txt"

            file_path = filedialog.asksaveasfilename(
                defaultextension=".txt",
                initialfile=default_name,
                filetypes=[("Text files", "*.txt"), ("JSON files", "*.json"), ("All files", "*.*")]
            )

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                self.update_status(f"Saved to {file_path}", 'success')
        except Exception as e:
            self.update_status(f"Save failed: {e}", 'error')

    def format_and_log_output(self, fingerprint, settings, build_info, ota_link):
        self.log_output("=" * 75, 'header')
        self.log_output("DEVICE & BUILD INFORMATION", 'header')
        self.log_output("=" * 75, 'header')

        self.log_output("\n[INPUT]", 'section')
        self.log_output(f"  Device Codename:   {build_info['device_codename']}", 'info')
        self.log_output(f"  Android Version:   {build_info['android_version']}", 'info')
        self.log_output(f"  Build Tag:         {build_info['build_tag']}", 'info')
        self.log_output(f"  Build Number:      {build_info['build_number']}", 'info')
        self.log_output(f"  Build Flavor:      {build_info['build_flavor']}", 'info')
        self.log_output(f"  Security Keys:     {build_info['security_keys']}", 'info')

        self.log_output("\n[SERVER RESPONSE]", 'section')
        self.log_output(f"  Total Settings:    {len(settings)}", 'info')
        self.log_output(f"  Android ID:        {build_info['android_id']}", 'info')
        self.log_output(f"  Device Country:    {build_info['device_country']}", 'info')

        self.log_output("\n[OTA UPDATE]", 'section')
        if ota_link:
            self.status_icon_var.set("✓")
            self.status_icon_label.config(foreground='#006600')

            self.output_text.insert(tk.END, f"  Status:            ", 'info')
            self.output_text.insert(tk.END, "[OK] Update Available\n", 'success')

            if ota_link.get('title'):
                self.log_output(f"  Title:             {ota_link['title']}", 'info')

            self.log_output(f"\n  Target URL:", 'info')
            self.output_text.insert(tk.END, "    ", 'info')
            self.log_link(ota_link['url'], ota_link['url'])
            self.output_text.insert(tk.END, '\n', 'info')

            if ota_link.get('size'):
                self.log_output(f"  Size:              {ota_link['size']}", 'info')

            self.current_ota_link = ota_link['url']
            header_text = f"🔗 {ota_link['url']}"
            self.ota_link_label.config(text=header_text, foreground='#0066cc')
            self._meta_autofill_url(ota_link['url'])

            desc_parts = []
            if ota_link.get('title'):
                desc_parts.append(f"<strong>Title:</strong> {ota_link['title']}<br>")
            if ota_link.get('description'):
                desc_parts.append(ota_link['description'])
            if ota_link.get('size'):
                desc_parts.append(f"<br><strong>Size:</strong> {ota_link['size']}")
            desc_html = "".join(desc_parts) if desc_parts else "(No description available)"

            if self.html_frame:
                html_content = f"""
                <html>
                <head>
                    <style>
                        body {{ font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }}
                        strong {{ color: #333; }}
                        a {{ color: #0066cc; text-decoration: none; }}
                        a:hover {{ text-decoration: underline; }}
                        p {{ margin: 10px 0; }}
                        br {{ margin: 5px 0; }}
                    </style>
                </head>
                <body>
                {desc_html}
                </body>
                </html>
                """
                self.html_frame.load_html(html_content)
            elif self.desc_text:
                desc_plain = desc_html.replace('<br>', '\n').replace('<p>', '').replace('</p>', '').replace('<strong>', '').replace('</strong>', '').replace('<a href="', '').replace('">', '').replace('</a>', '')
                self.desc_text.insert(tk.END, desc_plain)

            self.log_output(f"\n  Description:", 'info')
            if ota_link.get('title'):
                self.log_output(f"    Title: {ota_link['title']}", 'info')
            if ota_link.get('description'):
                desc_plain = ota_link['description'].replace('<br>', '\n').replace('<p>', '').replace('</p>', '').replace('<strong>', '').replace('</strong>', '').replace('<a href="', '').replace('">', '').replace('</a>', '')
                if len(desc_plain) > 70:
                    words = desc_plain.split()
                    lines = []
                    current_line = []
                    for word in words:
                        if len(' '.join(current_line + [word])) <= 70:
                            current_line.append(word)
                        else:
                            if current_line:
                                lines.append('    ' + ' '.join(current_line))
                            current_line = [word]
                    if current_line:
                        lines.append('    ' + ' '.join(current_line))
                    for line in lines:
                        self.log_output(line, 'info')
                else:
                    self.log_output(f"    {desc_plain}", 'info')
            if ota_link.get('size'):
                self.log_output(f"    Size: {ota_link['size']}", 'info')

            if ota_link.get('precondition'):
                self.log_output(f"\n  Precondition:", 'info')
                self.log_output(f"    {ota_link['precondition']}", 'info')

            if ota_link.get('postcondition'):
                self.log_output(f"\n  Postcondition:", 'info')
                self.log_output(f"    {ota_link['postcondition']}", 'info')
        else:
            self.status_icon_var.set("❌")
            self.status_icon_label.config(foreground='#cc0000')
            self.output_text.insert(tk.END, f"  Status:            ", 'info')
            self.output_text.insert(tk.END, "[NONE] No Update Available\n", 'error')
            if self.html_frame:
                self.html_frame.load_html("<p>No OTA update available for this device.</p>")
            elif self.desc_text:
                self.desc_text.insert(tk.END, "No OTA update available for this device.")

        self.log_output("\n" + "=" * 75, 'header')

    # ── Scan Key Types ─────────────────────────────────────────────────────
    def on_keyscan_click(self):
        fingerprint = self.fingerprint_var.get().strip()
        if not fingerprint:
            messagebox.showerror("Error", "Please enter a fingerprint")
            return
        if '/' not in fingerprint:
            messagebox.showerror("Error", "Invalid fingerprint format")
            return

        self.query_button.config(state=tk.DISABLED)
        self.keyscan_button.config(state=tk.DISABLED)
        self.clear_button.config(state=tk.DISABLED)
        self.fingerprint_entry.config(state=tk.DISABLED)

        self.keyscan_thread = threading.Thread(target=self.perform_keyscan, args=(fingerprint,), daemon=True)
        self.keyscan_thread.start()

    def perform_keyscan(self, fingerprint):
        try:
            self.output_text.delete(1.0, tk.END)
            self.raw_text.delete(1.0, tk.END)
            if self.html_frame:
                self.html_frame.load_html("")
            elif self.desc_text:
                self.desc_text.delete(1.0, tk.END)
            self.url_map.clear()
            self.current_ota_link = None
            self.status_icon_var.set("")
            self.ota_link_label.config(text="")

            if ':' not in fingerprint:
                raise ValueError("Fingerprint must contain at least one ':' separator")
            prefix, original_key = fingerprint.rsplit(':', 1)

            key_types = [
                "user/release-keys",
                "userdebug/release-keys",
                "eng/release-keys",
                "user/dev-keys",
                "user/test-keys",
                "userdebug/dev-keys",
                "userdebug/test-keys",
                "eng/dev-keys",
                "eng/test-keys"
            ]

            self.log_output("=" * 75, 'header')
            self.log_output("KEY TYPE SCAN RESULTS", 'header')
            self.log_output("=" * 75, 'header')
            self.log_output(f"Fingerprint base: {prefix}:", 'info')
            self.log_output("")

            found_links = []
            total = len(key_types)

            for i, key in enumerate(key_types, 1):
                test_fp = f"{prefix}:{key}"
                self.log_output(f"[{i}/{total}] {key}", 'section')
                self.log_output(f"  Fingerprint: {test_fp}", 'info')
                self.update_status(f"Scanning {key} ({i}/{total})...")

                try:
                    settings, raw_bytes = perform_checkin(test_fp)
                    if not settings:
                        self.log_output("  Status: ❌ No response from server", 'error')
                        continue

                    ota = find_ota_link(settings)
                    if ota and ota.get('url'):
                        self.log_output("  Status: ✅ OTA found", 'success')
                        self.log_output(f"  URL: {ota['url']}", 'success')
                        if ota.get('title'):
                            self.log_output(f"  Title: {ota['title']}", 'info')
                        if ota.get('size'):
                            self.log_output(f"  Size: {ota['size']}", 'info')
                        found_links.append((key, ota['url'], ota.get('title', ''), ota.get('size', '')))
                    else:
                        self.log_output("  Status: ❌ No OTA", 'error')
                except Exception as e:
                    self.log_output(f"  Status: ❌ Error: {e}", 'error')

                self.log_output("", 'info')

            self.log_output("=" * 75, 'header')
            if found_links:
                self.log_output(f"SUMMARY: Found {len(found_links)} OTA link(s)", 'success')
                for key, url, title, size in found_links:
                    self.log_output(f"  - {key} → {url}", 'success')
                    if title:
                        self.log_output(f"      Title: {title}", 'info')
                    if size:
                        self.log_output(f"      Size: {size}", 'info')
            else:
                self.log_output("SUMMARY: No OTA links found for any key type", 'error')
            self.log_output("=" * 75, 'header')

            self.update_status(f"Key scan completed – {len(found_links)} OTA(s) found", 'success' if found_links else 'error')
            self.status_icon_var.set("✓" if found_links else "❌")

        except ValueError as e:
            self.log_output(f"ERROR: {e}", 'error')
            self.update_status("Invalid fingerprint format", 'error')
        except Exception as e:
            self.log_output(f"ERROR: {e}", 'error')
            self.update_status(f"Error: {e}", 'error')
        finally:
            self.query_button.config(state=tk.NORMAL)
            self.keyscan_button.config(state=tk.NORMAL)
            self.clear_button.config(state=tk.NORMAL)
            self.fingerprint_entry.config(state=tk.NORMAL)


# ── Helper functions ──────────────────────────────────────────────────────

def parse_fingerprint(fingerprint):
    parts = fingerprint.split('/')
    if len(parts) != 6:
        raise ValueError(f"Invalid fingerprint format. Expected 6 parts.\n"
                         f"Format: oem/product/device:api/build_tag/incremental:build_type/key_type\n"
                         f"Got {len(parts)} parts: {parts}")

    oem = parts[0]
    product = parts[1]

    device_api = parts[2].split(':')
    if len(device_api) != 2:
        raise ValueError(f"Invalid device:api format in part 3: {parts[2]}")
    device = device_api[0]
    api_level = device_api[1]

    build_tag = parts[3]

    incremental_type = parts[4].split(':')
    if len(incremental_type) != 2:
        raise ValueError(f"Invalid incremental:build_type format in part 5: {parts[4]}")
    incremental = incremental_type[0]
    build_type = incremental_type[1]

    key_type = parts[5]

    return {
        'fingerprint': fingerprint,
        'oem': oem,
        'product': product,
        'device': device,
        'api_level': api_level,
        'build_tag': build_tag,
        'incremental': incremental,
        'build_type': build_type,
        'key_type': key_type,
    }


def encode_varint(value):
    parts = []
    while value > 0x7f:
        parts.append((value & 0x7f) | 0x80)
        value >>= 7
    parts.append(value & 0x7f)
    return bytes(parts)


def encode_string(field_number, value):
    if isinstance(value, str):
        value = value.encode('utf-8')
    tag = (field_number << 3) | 2
    return encode_varint(tag) + encode_varint(len(value)) + value


def encode_int64(field_number, value):
    tag = (field_number << 3) | 0
    return encode_varint(tag) + encode_varint(value & 0xffffffffffffffff)


def encode_bool(field_number, value):
    tag = (field_number << 3) | 0
    return encode_varint(tag) + bytes([1 if value else 0])


def decode_varint(data, offset):
    result = 0
    shift = 0
    while True:
        byte = data[offset]
        result |= (byte & 0x7f) << shift
        offset += 1
        if byte < 0x80:
            break
        shift += 7
    return result, offset


def decode_string(data, offset, length):
    return data[offset:offset+length].decode('utf-8', errors='ignore'), offset + length


def parse_protobuf_response(data):
    settings = {}
    offset = 0

    while offset < len(data):
        tag, offset = decode_varint(data, offset)
        field_number = tag >> 3
        wire_type = tag & 0x07

        if field_number == 5 and wire_type == 2:
            length, offset = decode_varint(data, offset)
            end = offset + length
            name = None
            value = None

            while offset < end:
                inner_tag, offset = decode_varint(data, offset)
                inner_field = inner_tag >> 3
                inner_wire = inner_tag & 0x07

                if inner_wire == 2:
                    str_len, offset = decode_varint(data, offset)
                    if inner_field == 1:
                        name, offset = decode_string(data, offset, str_len)
                    elif inner_field == 2:
                        value, offset = decode_string(data, offset, str_len)
                else:
                    offset += 1

            if name and value:
                settings[name] = value
        else:
            if wire_type == 0:
                _, offset = decode_varint(data, offset)
            elif wire_type == 2:
                length, offset = decode_varint(data, offset)
                offset += length
            elif wire_type == 5:
                offset += 4
            elif wire_type == 1:
                offset += 8

    return settings


_CHECKIN_RESPONSE_FIELDS = {
    1: 'android_id',
    2: 'security_token',
    3: 'time_msec',
    4: 'settings_diff',
    5: 'setting',
    6: 'digest',
    7: 'android_id_alt',
    8: 'market_ok',
    9: 'gservices_digest',
    10: 'checkin_interval_msec',
    11: 'checkin',
    12: 'min_checkin_interval_msec',
    13: 'intent',
    14: 'account',
    15: 'gcm_response',
    16: 'device_data_version',
    17: 'last_checkin_msec',
    18: 'deleted_setting',
    19: 'new_device_cookie',
    20: 'device_checkin_consistency_token',
}

_SETTING_FIELDS = {
    1: 'name',
    2: 'value',
}


def _is_valid_protobuf(data):
    offset = 0
    count = 0
    try:
        while offset < len(data):
            tag, offset = decode_varint(data, offset)
            wire_type = tag & 0x07
            if wire_type in (3, 4, 6, 7):
                return False
            if wire_type == 0:
                _, offset = decode_varint(data, offset)
            elif wire_type == 1:
                if offset + 8 > len(data):
                    return False
                offset += 8
            elif wire_type == 2:
                length, offset = decode_varint(data, offset)
                if offset + length > len(data):
                    return False
                offset += length
            elif wire_type == 5:
                if offset + 4 > len(data):
                    return False
                offset += 4
            else:
                return False
            count += 1
        return count > 0 and offset == len(data)
    except Exception:
        return False


def parse_protobuf_full(data, indent=0, field_names=None):
    if field_names is None:
        field_names = _CHECKIN_RESPONSE_FIELDS

    lines = []
    offset = 0
    pad = '  ' * indent

    while offset < len(data):
        try:
            tag, offset = decode_varint(data, offset)
        except Exception:
            lines.append(f"{pad}[parse error at offset {offset}/{len(data)}]")
            break

        field_number = tag >> 3
        wire_type = tag & 0x07
        field_label = field_names.get(field_number, f'field_{field_number}')

        try:
            if wire_type == 0:
                val, offset = decode_varint(data, offset)
                lines.append(f"{pad}[{field_number}] {field_label}  =  {val}")

            elif wire_type == 1:
                raw8 = data[offset:offset+8]
                offset += 8
                val = struct.unpack_from('<q', raw8)[0]
                lines.append(f"{pad}[{field_number}] {field_label}  =  {val}  (64-bit LE)")

            elif wire_type == 2:
                length, offset = decode_varint(data, offset)
                raw = data[offset:offset+length]
                offset += length

                if field_number == 5 and field_names is _CHECKIN_RESPONSE_FIELDS:
                    child_names = _SETTING_FIELDS
                else:
                    child_names = {}

                if length > 0 and _is_valid_protobuf(raw):
                    nested = parse_protobuf_full(raw, indent + 1, child_names)
                    lines.append(f"{pad}[{field_number}] {field_label}  {{")
                    lines.extend(nested)
                    lines.append(f"{pad}}}")
                else:
                    try:
                        txt = raw.decode('utf-8')
                        txt_repr = repr(txt)[1:-1]
                        lines.append(f"{pad}[{field_number}] {field_label}  =  \"{txt_repr}\"")
                    except Exception:
                        hex_str = raw.hex()
                        if len(hex_str) > 120:
                            hex_str = hex_str[:120] + f' ... ({length} bytes total)'
                        lines.append(f"{pad}[{field_number}] {field_label}  =  <bytes> {hex_str}")

            elif wire_type == 5:
                raw4 = data[offset:offset+4]
                offset += 4
                val = struct.unpack_from('<I', raw4)[0]
                lines.append(f"{pad}[{field_number}] {field_label}  =  {val}  (32-bit LE)")

            else:
                lines.append(f"{pad}[{field_number}] unknown wire_type={wire_type}, stopping parse")
                break

        except Exception as e:
            lines.append(f"{pad}[{field_number}] parse error: {e}")
            break

    return lines


def format_raw_response(raw_bytes):
    n = len(raw_bytes)
    header = f"=== RAW PROTOBUF RESPONSE  ({n} bytes) ===\n"

    human_lines = [header, "--- FIELD TREE ---"]
    try:
        tree = parse_protobuf_full(raw_bytes, indent=0)
        human_lines.extend(tree)
    except Exception as e:
        human_lines.append(f"[parser error: {e}]")
    human_str = '\n'.join(human_lines)

    hex_lines = [header, "--- HEX DUMP ---"]
    for i in range(0, n, 16):
        chunk = raw_bytes[i:i+16]
        hex_part = ' '.join(f'{b:02x}' for b in chunk)
        asc_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in chunk)
        hex_lines.append(f"  {i:06x}  {hex_part:<47}  {asc_part}")
    hex_str = '\n'.join(hex_lines)

    return human_str, hex_str


def build_checkin_request(fingerprint):
    try:
        parsed = parse_fingerprint(fingerprint)
    except ValueError as e:
        raise ValueError(f"Failed to parse fingerprint: {e}")

    device = parsed['device']

    build = b''
    build += encode_string(1, fingerprint)
    build += encode_int64(7, 0)
    build += encode_string(9, device)

    checkin = b''
    tag = (1 << 3) | 2
    checkin += encode_varint(tag) + encode_varint(len(build)) + build
    checkin += encode_int64(2, 0)
    checkin += encode_string(8, "WIFI::")
    checkin += encode_int64(9, 0)
    checkin += encode_int64(14, 2)
    checkin += encode_bool(18, False)
    checkin += encode_string(19, "WIFI")

    request = b''
    tag = (4 << 3) | 2
    request += encode_varint(tag) + encode_varint(len(checkin)) + checkin
    request += encode_int64(2, 0)
    request += encode_string(3, "1-0000000000000000000000000000000000000000")
    request += encode_string(6, "en-US")
    request += encode_string(12, "America/New_York")
    request += encode_int64(14, 3)
    request += encode_int64(20, 0)
    request += encode_int64(22, 0)

    return request


def perform_checkin(fingerprint):
    try:
        parsed = parse_fingerprint(fingerprint)
        request_data = build_checkin_request(fingerprint)
        compressed = gzip.compress(request_data)

        url = 'https://android.googleapis.com/checkin'
        device = parsed['device']
        version = parsed['api_level']
        build = parsed['build_tag']

        headers = {
            'Accept-Encoding': 'gzip, deflate',
            'Content-Encoding': 'gzip',
            'Content-Type': 'application/x-protobuffer',
            'User-Agent': f'Dalvik/2.1.0 (Linux; U; Android {version}; {device} Build/{build})'
        }

        req = urllib.request.Request(url, data=compressed, headers=headers, method='POST')

        with urllib.request.urlopen(req, timeout=10) as response:
            response_data = response.read()
            try:
                response_data = gzip.decompress(response_data)
            except:
                pass

            settings = parse_protobuf_response(response_data)
            return settings, response_data

    except urllib.error.URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        return None, None
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None, None


def get_android_version(api_level):
    try:
        api_str = str(api_level)

        if api_str.upper() == 'KKWT':
            return 'KKWT (API 19)'

        if '.' in api_str:
            version_to_api = {
                '1.0': 1, '1.1': 2, '1.5': 3, '1.6': 4, '2.0': 5, '2.0.1': 6, '2.1': 7,
                '2.2': 8, '2.3': 9, '2.3.3': 10, '3.0': 11, '3.1': 12, '3.2': 13, '4.0': 14,
                '4.0.2': 15, '4.1': 16, '4.1.1': 16, '4.2': 17, '4.3': 18, '4.4': 19, '4.4W': 20, '4.4W.1': 20, '4.4W.2': 20,
                '5.0': 21, '5.0.1': 21, '5.1': 22, '5.1.1': 22, '6.0': 23, '6.0.1': 23, '7.0': 24, '7.0.1': 24,
                '7.1': 25, '7.1.1': 25, '8.0': 26, '8.0.1': 26, '8.1': 27, '8.1.1': 27, '9.0': 28,
                '10.0': 29, '11.0': 30, '12.0': 31, '12L': 32, '13.0': 33, '14.0': 34, '15.0': 35, '16.0': 36, '17.0': 37
            }
            if api_str in version_to_api:
                api_num = version_to_api[api_str]
                return f'{api_str} (API {api_num})'
            else:
                return f'Android {api_str}'

        level = int(api_level)

        if level >= 15 and level <= 20:
            return f'Android {level} (API {level})'

        historical = {
            11: '3.0', 12: '3.1', 13: '3.2', 14: '4.0', 15: '4.0.2', 16: '4.1', 17: '4.2',
            18: '4.3', 19: '4.4', 20: '4.4W', 20: '4.4W.1', 20: '4.4W.2', 21: '5.0', 22: '5.1', 23: '6.0', 24: '7.0',
            25: '7.1', 26: '8.0', 27: '8.1', 28: '9.0', 29: '10.0', 30: '11.0', 31: '12.0',
            32: '12L', 33: '13.0', 34: '14.0', 35: '15.0', 36: '16.0', 37: '17.0'
        }

        if level in historical:
            return f'{historical[level]} (API {level})'
        elif level > 37:
            return f'Android {level} (API {level})'
        elif level >= 1:
            return f'API {level}'
        else:
            return f'Unknown'
    except:
        return f'Android {api_level}'


def extract_build_date(build_tag):
    try:
        parts = build_tag.split('.')
        if len(parts) < 2:
            return "Unknown"

        date_str = parts[1]

        if len(date_str) < 6 or not date_str[:6].isdigit():
            return "Unknown"

        yy = int(date_str[0:2])
        mm = int(date_str[2:4])
        dd = int(date_str[4:6])

        if not (1 <= mm <= 12 and 1 <= dd <= 31):
            return "Unknown"

        months = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        month_name = months[mm]
        year = 2000 + yy

        return f"{month_name} {dd}, {year}"
    except:
        return "Unknown"


def extract_build_details(fingerprint, settings):
    parsed = parse_fingerprint(fingerprint)

    build_info = {
        'fingerprint': fingerprint,
        'device_codename': parsed['device'],
        'android_version': get_android_version(parsed['api_level']),
        'api_level': parsed['api_level'],
        'build_date': extract_build_date(parsed['build_tag']),
        'build_tag': parsed['build_tag'],
        'build_number': parsed['incremental'],
        'build_flavor': parsed['build_type'],
        'security_keys': parsed['key_type'],
        'android_id': settings.get('android_id', 'Not assigned'),
        'device_country': settings.get('device_country', 'Unknown'),
    }

    return build_info


def find_ota_link(settings):
    if 'update_url' not in settings:
        return None

    return {
        'url': settings['update_url'],
        'title': settings.get('update_title', ''),
        'description': settings.get('update_description', ''),
        'precondition': settings.get('update_precondition', ''),
        'postcondition': settings.get('update_postcondition', ''),
        'size': settings.get('update_size', ''),
    }


def get_service_summary(settings):
    return len(settings)


def format_output(fingerprint, settings, build_info, ota_link):
    output = []
    output.append("=" * 63)
    output.append("DEVICE & BUILD INFORMATION")
    output.append("=" * 63)

    output.append("\n[INPUT]")
    output.append(f"  Device Codename:   {build_info['device_codename']}")
    output.append(f"  Android Version:   {build_info['android_version']}")
    output.append(f"  Build Tag:         {build_info['build_tag']}")
    output.append(f"  Build Number:      {build_info['build_number']}")
    output.append(f"  Build Flavor:      {build_info['build_flavor']}")
    output.append(f"  Security Keys:     {build_info['security_keys']}")

    output.append("\n[SERVER RESPONSE]")
    output.append(f"  Total Settings:    {len(settings)}")
    output.append(f"  Android ID:        {build_info['android_id']}")
    output.append(f"  Device Country:    {build_info['device_country']}")

    output.append("\n[OTA UPDATE]")
    if ota_link:
        output.append(f"  Status:            [OK] Update Available")
        if ota_link.get('title'):
            output.append(f"  Title:             {ota_link['title']}")
        output.append(f"\n  Target URL:")
        output.append(f"    {ota_link['url']}")
        if ota_link.get('size'):
            output.append(f"  Size:              {ota_link['size']}")

        if ota_link.get('description'):
            output.append(f"\n  Description:")
            desc = ota_link['description']
            if len(desc) > 70:
                words = desc.split()
                lines = []
                current_line = []
                for word in words:
                    if len(' '.join(current_line + [word])) <= 70:
                        current_line.append(word)
                    else:
                        if current_line:
                            lines.append('    ' + ' '.join(current_line))
                        current_line = [word]
                if current_line:
                    lines.append('    ' + ' '.join(current_line))
                output.extend(lines)
            else:
                output.append(f"    {desc}")

        if ota_link.get('precondition'):
            output.append(f"\n  Precondition:")
            output.append(f"    {ota_link['precondition']}")

        if ota_link.get('postcondition'):
            output.append(f"\n  Postcondition:")
            output.append(f"    {ota_link['postcondition']}")
    else:
        output.append(f"  Status:            [NONE] No Update Available")

    output.append("\n" + "=" * 63)

    return "\n".join(output)


# ── HTTP Info prober ──────────────────────────────────────────────────────

def probe_ota_url(url: str, status_cb=None, timeout: int = 15) -> dict:
    def _s(msg):
        if status_cb:
            status_cb(msg)

    result = {
        'general': [],
        'headers': [],
        'redirects': [],
        'security': [],
        'timing': [],
        'summary': '',
    }

    redirect_chain = []
    current_url = url
    max_redirects = 12
    final_hdrs = {}
    final_status = None
    size_human = ''

    t_start = time.perf_counter()
    t_connect = None
    t_ttfb = None
    tls_done = False

    for hop in range(max_redirects):
        parsed = urlparse(current_url)
        is_https = parsed.scheme == 'https'
        host = parsed.netloc
        path = (parsed.path or '/') + (('?' + parsed.query) if parsed.query else '')

        _s(f"HEAD hop {hop+1}: {host}{path[:60]}...")

        try:
            t0 = time.perf_counter()
            ctx = ssl.create_default_context() if is_https else None

            if is_https:
                conn = http.client.HTTPSConnection(host, timeout=timeout, context=ctx)
            else:
                conn = http.client.HTTPConnection(host, timeout=timeout)

            conn.connect()
            t_connect = (time.perf_counter() - t0) * 1000

            if is_https and not tls_done:
                try:
                    sock = conn.sock
                    cipher_name, proto, bits = sock.cipher()
                    peer_cert = sock.getpeercert()
                    result['security'].append(('Protocol', proto or 'unknown'))
                    result['security'].append(('Cipher Suite', cipher_name or 'unknown'))
                    result['security'].append(('Key Bits', str(bits) if bits else 'unknown'))
                    if peer_cert:
                        subj = dict(x[0] for x in peer_cert.get('subject', []))
                        issuer = dict(x[0] for x in peer_cert.get('issuer', []))
                        result['security'].append(('Cert CN', subj.get('commonName', '—')))
                        result['security'].append(('Cert Org', subj.get('organizationName', '—')))
                        result['security'].append(('Issuer', issuer.get('organizationName', '—')))
                        result['security'].append(('Not Before', peer_cert.get('notBefore', '—')))
                        result['security'].append(('Not After', peer_cert.get('notAfter', '—')))
                        sans = peer_cert.get('subjectAltName', [])
                        if sans:
                            result['security'].append(('SAN', ', '.join(v for _, v in sans)))
                    tls_done = True
                except Exception as tls_err:
                    result['security'].append(('TLS error', str(tls_err)))
            elif not is_https and not tls_done:
                result['security'].append(('Protocol', 'HTTP (no TLS)'))
                tls_done = True

            conn.request('HEAD', path, headers={
                'User-Agent': 'OTA-Prober/2.0',
                'Accept-Encoding': 'identity',
                'Connection': 'close',
            })
            resp = conn.getresponse()
            t_ttfb = (time.perf_counter() - t0) * 1000

            status = resp.status
            hdrs = {k.lower(): v for k, v in resp.getheaders()}
            conn.close()

            redirect_chain.append((current_url, status))
            final_hdrs = hdrs
            final_status = status

            if status in (301, 302, 303, 307, 308):
                loc = hdrs.get('location', '')
                if not loc:
                    break
                if loc.startswith('/'):
                    loc = f"{parsed.scheme}://{parsed.netloc}{loc}"
                elif not loc.startswith('http'):
                    loc = f"{parsed.scheme}://{parsed.netloc}/{loc}"
                current_url = loc
                tls_done = False
                continue
            else:
                break

        except Exception as exc:
            result['summary'] = f"Error on hop {hop+1}: {exc}"
            return result

    t_total = (time.perf_counter() - t_start) * 1000

    result['redirects'] = [f"[{code}] {u}" for u, code in redirect_chain]

    final_url = redirect_chain[-1][0] if redirect_chain else url
    gen = result['general']
    gen.append(('Original URL', url))
    gen.append(('Final URL', final_url))
    gen.append(('HTTP Status', f"{final_status} {http.client.responses.get(final_status, '')}"))
    gen.append(('Redirect Hops', str(len(redirect_chain) - 1)))

    cl = final_hdrs.get('content-length', '')
    if cl:
        try:
            sb = int(cl)
            if sb >= 1_073_741_824:
                size_human = f"{sb/1_073_741_824:.2f} GiB"
            elif sb >= 1_048_576:
                size_human = f"{sb/1_048_576:.2f} MiB"
            else:
                size_human = f"{sb/1024:.1f} KiB"
            gen.append(('File Size', f"{size_human}  ({sb:,} bytes)"))
        except ValueError:
            gen.append(('File Size', cl))

    for label, key in [
        ('Content-Type', 'content-type'),
        ('Server', 'server'),
        ('Via', 'via'),
        ('ETag', 'etag'),
        ('Last-Modified', 'last-modified'),
        ('Accept-Ranges', 'accept-ranges'),
        ('Cache-Control', 'cache-control'),
        ('Expires', 'expires'),
        ('Age', 'age'),
    ]:
        v = final_hdrs.get(key)
        if v:
            gen.append((label, v))

    for cdn_key in ('x-cache', 'cf-cache-status', 'x-served-by',
                    'x-cache-hits', 'x-amz-cf-pop', 'x-amz-cf-id'):
        if cdn_key in final_hdrs:
            gen.append((cdn_key, final_hdrs[cdn_key]))

    for dkey in ('content-md5', 'digest', 'x-goog-hash',
                 'x-amz-checksum-sha256', 'x-amz-checksum-crc32'):
        if dkey in final_hdrs:
            gen.append((dkey, final_hdrs[dkey]))

    for gkey in ('x-goog-generation', 'x-goog-metageneration',
                 'x-goog-stored-content-encoding',
                 'x-goog-stored-content-length',
                 'x-goog-storage-class', 'x-goog-expiration',
                 'x-guploader-uploadid', 'x-robots-tag',
                 'x-goog-download-filename'):
        if gkey in final_hdrs:
            gen.append((gkey, final_hdrs[gkey]))

    gen_val = final_hdrs.get('x-goog-generation', '')
    if gen_val:
        try:
            import datetime
            ts_sec = int(gen_val) / 1_000_000
            dt = datetime.datetime.utcfromtimestamp(ts_sec)
            gen.append(('Created (from generation)', dt.strftime('%Y-%m-%d %H:%M:%S UTC')))
        except Exception:
            pass

    for skey in ('strict-transport-security', 'access-control-allow-origin',
                 'x-content-type-options', 'x-frame-options',
                 'content-security-policy', 'permissions-policy',
                 'cross-origin-resource-policy'):
        if skey in final_hdrs:
            gen.append((skey, final_hdrs[skey]))

    result['headers'] = sorted(final_hdrs.items())

    tim = result['timing']
    if t_connect is not None:
        tim.append(('TCP + TLS handshake', f"{t_connect:.1f} ms"))
    if t_ttfb is not None:
        tim.append(('Time to first byte', f"{t_ttfb:.1f} ms"))
    tim.append(('Total probe time', f"{t_total:.1f} ms"))

    nhops = len(redirect_chain) - 1
    result['summary'] = (
        f"Done - HTTP {final_status}, {nhops} redirect(s), "
        f"{len(final_hdrs)} response headers"
        + (f", {size_human}" if size_human else "")
    )
    return result


def main():
    root = tk.Tk()
    app = OTAProberGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
