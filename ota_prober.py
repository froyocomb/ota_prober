#!/usr/bin/env python3

# GOTA Prober, held under The MIT License, Copyright 2026 Lucas Puntillo
# Bruteforce additions added by @RYuhMine! Thank you!

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
import zlib

try:
    from tkinterweb import HtmlFrame
except ImportError:
    HtmlFrame = None

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# ── Locale → Timezone mapping ────────────────────────────────────────────
LOCALE_TZ_MAP = {
    'af-ZA': 'Africa/Johannesburg',
    'am-ET': 'Africa/Addis_Ababa',
    'ar-AE': 'Asia/Dubai',
    'ar-BH': 'Asia/Bahrain',
    'ar-DZ': 'Africa/Algiers',
    'ar-EG': 'Africa/Cairo',
    'ar-IQ': 'Asia/Baghdad',
    'ar-JO': 'Asia/Amman',
    'ar-KW': 'Asia/Kuwait',
    'ar-LB': 'Asia/Beirut',
    'ar-LY': 'Africa/Tripoli',
    'ar-MA': 'Africa/Casablanca',
    'ar-OM': 'Asia/Muscat',
    'ar-PS': 'Asia/Gaza',
    'ar-QA': 'Asia/Qatar',
    'ar-SA': 'Asia/Riyadh',
    'ar-SO': 'Africa/Mogadishu',
    'ar-SY': 'Asia/Damascus',
    'ar-TN': 'Africa/Tunis',
    'ar-YE': 'Asia/Aden',
    'as-IN': 'Asia/Kolkata',
    'az-AZ': 'Asia/Baku',
    'be-BY': 'Europe/Minsk',
    'bg-BG': 'Europe/Sofia',
    'bn-BD': 'Asia/Dhaka',
    'bn-IN': 'Asia/Kolkata',
    'bs-BA': 'Europe/Sarajevo',
    'ca-AD': 'Europe/Andorra',
    'ca-ES': 'Europe/Madrid',
    'cs-CZ': 'Europe/Prague',
    'cy-GB': 'Europe/London',
    'da-DK': 'Europe/Copenhagen',
    'de-AT': 'Europe/Vienna',
    'de-BE': 'Europe/Brussels',
    'de-CH': 'Europe/Zurich',
    'de-DE': 'Europe/Berlin',
    'de-LI': 'Europe/Vaduz',
    'de-LU': 'Europe/Luxembourg',
    'el-CY': 'Asia/Nicosia',
    'el-GR': 'Europe/Athens',
    'en-AG': 'America/Antigua',
    'en-AU': 'Australia/Sydney',
    'en-BB': 'America/Barbados',
    'en-BS': 'America/Nassau',
    'en-BZ': 'America/Belize',
    'en-CA': 'America/Toronto',
    'en-DM': 'America/Dominica',
    'en-FJ': 'Pacific/Fiji',
    'en-GB': 'Europe/London',
    'en-GD': 'America/Grenada',
    'en-GH': 'Africa/Accra',
    'en-GY': 'America/Guyana',
    'en-IE': 'Europe/Dublin',
    'en-IN': 'Asia/Kolkata',
    'en-JM': 'America/Jamaica',
    'en-KE': 'Africa/Nairobi',
    'en-KN': 'America/St_Kitts',
    'en-LC': 'America/St_Lucia',
    'en-MT': 'Europe/Malta',
    'en-NG': 'Africa/Lagos',
    'en-NZ': 'Pacific/Auckland',
    'en-PG': 'Pacific/Port_Moresby',
    'en-PH': 'Asia/Manila',
    'en-PK': 'Asia/Karachi',
    'en-SB': 'Pacific/Guadalcanal',
    'en-SG': 'Asia/Singapore',
    'en-TT': 'America/Port_of_Spain',
    'en-TZ': 'Africa/Dar_es_Salaam',
    'en-UG': 'Africa/Kampala',
    'en-US': 'America/New_York',
    'en-VC': 'America/St_Vincent',
    'en-VU': 'Pacific/Efate',
    'en-WS': 'Pacific/Apia',
    'en-ZA': 'Africa/Johannesburg',
    'en-ZW': 'Africa/Harare',
    'es-AR': 'America/Argentina/Buenos_Aires',
    'es-BO': 'America/La_Paz',
    'es-CL': 'America/Santiago',
    'es-CO': 'America/Bogota',
    'es-CR': 'America/Costa_Rica',
    'es-CU': 'America/Havana',
    'es-DO': 'America/Santo_Domingo',
    'es-EC': 'America/Guayaquil',
    'es-ES': 'Europe/Madrid',
    'es-GQ': 'Africa/Malabo',
    'es-GT': 'America/Guatemala',
    'es-HN': 'America/Tegucigalpa',
    'es-MX': 'America/Mexico_City',
    'es-NI': 'America/Managua',
    'es-PA': 'America/Panama',
    'es-PE': 'America/Lima',
    'es-PH': 'Asia/Manila',
    'es-PR': 'America/Puerto_Rico',
    'es-PY': 'America/Asuncion',
    'es-SV': 'America/El_Salvador',
    'es-US': 'America/New_York',
    'es-UY': 'America/Montevideo',
    'es-VE': 'America/Caracas',
    'et-EE': 'Europe/Tallinn',
    'eu-ES': 'Europe/Madrid',
    'fa-IR': 'Asia/Tehran',
    'fi-FI': 'Europe/Helsinki',
    'fil-PH': 'Asia/Manila',
    'fr-BE': 'Europe/Brussels',
    'fr-BF': 'Africa/Ouagadougou',
    'fr-BJ': 'Africa/Porto-Novo',
    'fr-CA': 'America/Montreal',
    'fr-CD': 'Africa/Kinshasa',
    'fr-CF': 'Africa/Bangui',
    'fr-CH': 'Europe/Zurich',
    'fr-CI': 'Africa/Abidjan',
    'fr-CM': 'Africa/Douala',
    'fr-DZ': 'Africa/Algiers',
    'fr-FR': 'Europe/Paris',
    'fr-GF': 'America/Cayenne',
    'fr-GP': 'America/Guadeloupe',
    'fr-HT': 'America/Port-au-Prince',
    'fr-LU': 'Europe/Luxembourg',
    'fr-MA': 'Africa/Casablanca',
    'fr-MC': 'Europe/Monaco',
    'fr-MG': 'Indian/Antananarivo',
    'fr-ML': 'Africa/Bamako',
    'fr-MQ': 'America/Martinique',
    'fr-MU': 'Indian/Mauritius',
    'fr-NE': 'Africa/Niamey',
    'fr-PM': 'America/Miquelon',
    'fr-RE': 'Indian/Reunion',
    'fr-SC': 'Indian/Mahe',
    'fr-SN': 'Africa/Dakar',
    'fr-TG': 'Africa/Lome',
    'fr-TN': 'Africa/Tunis',
    'ga-IE': 'Europe/Dublin',
    'gd-GB': 'Europe/London',
    'gl-ES': 'Europe/Madrid',
    'gu-IN': 'Asia/Kolkata',
    'ha-NG': 'Africa/Lagos',
    'he-IL': 'Asia/Jerusalem',
    'hi-IN': 'Asia/Kolkata',
    'hr-HR': 'Europe/Zagreb',
    'hu-HU': 'Europe/Budapest',
    'hy-AM': 'Asia/Yerevan',
    'id-ID': 'Asia/Jakarta',
    'ig-NG': 'Africa/Lagos',
    'is-IS': 'Atlantic/Reykjavik',
    'it-CH': 'Europe/Zurich',
    'it-IT': 'Europe/Rome',
    'it-SM': 'Europe/Rome',
    'ja-JP': 'Asia/Tokyo',
    'jv-ID': 'Asia/Jakarta',
    'ka-GE': 'Asia/Tbilisi',
    'kk-KZ': 'Asia/Almaty',
    'km-KH': 'Asia/Phnom_Penh',
    'kn-IN': 'Asia/Kolkata',
    'ko-KR': 'Asia/Seoul',
    'ku-IQ': 'Asia/Baghdad',
    'ky-KG': 'Asia/Bishkek',
    'lo-LA': 'Asia/Vientiane',
    'lt-LT': 'Europe/Vilnius',
    'lv-LV': 'Europe/Riga',
    'mg-MG': 'Indian/Antananarivo',
    'mi-NZ': 'Pacific/Auckland',
    'mk-MK': 'Europe/Skopje',
    'ml-IN': 'Asia/Kolkata',
    'mn-MN': 'Asia/Ulaanbaatar',
    'mr-IN': 'Asia/Kolkata',
    'ms-BN': 'Asia/Brunei',
    'ms-MY': 'Asia/Kuala_Lumpur',
    'mt-MT': 'Europe/Malta',
    'my-MM': 'Asia/Yangon',
    'nb-NO': 'Europe/Oslo',
    'ne-NP': 'Asia/Kathmandu',
    'nl-AW': 'America/Aruba',
    'nl-BE': 'Europe/Brussels',
    'nl-CW': 'America/Curacao',
    'nl-NL': 'Europe/Amsterdam',
    'nl-SR': 'America/Paramaribo',
    'nl-SX': 'America/Lower_Princes',
    'nn-NO': 'Europe/Oslo',
    'no-NO': 'Europe/Oslo',
    'or-IN': 'Asia/Kolkata',
    'pa-IN': 'Asia/Kolkata',
    'pa-PK': 'Asia/Karachi',
    'pl-PL': 'Europe/Warsaw',
    'ps-AF': 'Asia/Kabul',
    'pt-AO': 'Africa/Luanda',
    'pt-BR': 'America/Sao_Paulo',
    'pt-CV': 'Atlantic/Cape_Verde',
    'pt-GW': 'Africa/Bissau',
    'pt-MZ': 'Africa/Maputo',
    'pt-PT': 'Europe/Lisbon',
    'pt-ST': 'Africa/Sao_Tome',
    'rm-CH': 'Europe/Zurich',
    'ro-RO': 'Europe/Bucharest',
    'ru-RU': 'Europe/Moscow',
    'si-LK': 'Asia/Colombo',
    'sk-SK': 'Europe/Bratislava',
    'sl-SI': 'Europe/Ljubljana',
    'so-SO': 'Africa/Mogadishu',
    'sq-AL': 'Europe/Tirane',
    'sr-BA': 'Europe/Belgrade',
    'sr-RS': 'Europe/Belgrade',
    'su-ID': 'Asia/Jakarta',
    'sv-FI': 'Europe/Helsinki',
    'sv-SE': 'Europe/Stockholm',
    'sw-KE': 'Africa/Nairobi',
    'sw-TZ': 'Africa/Dar_es_Salaam',
    'sw-UG': 'Africa/Kampala',
    'ta-IN': 'Asia/Kolkata',
    'ta-LK': 'Asia/Colombo',
    'ta-SG': 'Asia/Singapore',
    'te-IN': 'Asia/Kolkata',
    'tg-TJ': 'Asia/Dushanbe',
    'th-TH': 'Asia/Bangkok',
    'tk-TM': 'Asia/Ashgabat',
    'tl-PH': 'Asia/Manila',
    'tr-CY': 'Asia/Nicosia',
    'tr-TR': 'Europe/Istanbul',
    'ug-CN': 'Asia/Urumqi',
    'uk-UA': 'Europe/Kiev',
    'ur-IN': 'Asia/Kolkata',
    'ur-PK': 'Asia/Karachi',
    'uz-UZ': 'Asia/Tashkent',
    'vi-VN': 'Asia/Ho_Chi_Minh',
    'yi-IL': 'Asia/Jerusalem',
    'yo-NG': 'Africa/Lagos',
    'zh-CN': 'Asia/Shanghai',
    'zh-HK': 'Asia/Hong_Kong',
    'zh-MO': 'Asia/Macau',
    'zh-SG': 'Asia/Singapore',
    'zh-TW': 'Asia/Taipei',
    'zu-ZA': 'Africa/Johannesburg',
}
EXTRA_TZ = ['UTC', 'America/Los_Angeles', 'America/Chicago', 'America/Denver', 'Europe/London', 'Europe/Kiev', 'Europe/Moscow']

class OTAProberGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OTA Prober")
        self.root.geometry("1000x950")
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

        # Підписка на зміну вкладки для приховування параметрів
        self.notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)

    def _setup_layout_independent_shortcuts(self):
        """
        Робить Ctrl+C / Ctrl+V / Ctrl+X / Ctrl+A робочими незалежно від
        поточної розкладки клавіатури (укр., рос., будь-яка інша).
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
            # Якщо це Ctrl-комбінація, яку ми обробляємо на bind_class
            if event.state & 0x4 and event.keysym.lower() in ('c', 'v', 'x', 'a'):
                return "break"

        for widget_class in ('Entry', 'Text', 'TEntry', 'TCombobox'):
            self.root.bind_class(widget_class, '<Control-c>', on_key)
            self.root.bind_class(widget_class, '<Control-C>', on_key)
            self.root.bind_class(widget_class, '<Control-v>', on_key)
            self.root.bind_class(widget_class, '<Control-V>', on_key)
            self.root.bind_class(widget_class, '<Control-x>', on_key)
            self.root.bind_class(widget_class, '<Control-X>', on_key)
            self.root.bind_class(widget_class, '<Control-a>', on_key)
            self.root.bind_class(widget_class, '<Control-A>', on_key)

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

        # ── Input Fingerprint ──────────────────────────────────────────────
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

        # ── Request Parameters (Locale & Timezone) ──────────────────────
        self.params_frame = ttk.LabelFrame(main_frame, text="Request Parameters", padding="10")
        self.params_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))

        ttk.Label(self.params_frame, text="Locale:", style='Normal.TLabel').grid(row=0, column=0, sticky=tk.W, padx=5)
        self.locale_var = tk.StringVar(value="en-US")
        self.locale_combo = ttk.Combobox(self.params_frame, textvariable=self.locale_var, width=20)
        locale_list = sorted(LOCALE_TZ_MAP.keys())
        self.locale_combo['values'] = locale_list
        self.locale_combo.grid(row=0, column=1, sticky=tk.W, padx=5)
        self.locale_combo.bind('<<ComboboxSelected>>', self._on_locale_selected)
        self.locale_combo.bind('<KeyRelease>', self._on_locale_typed)

        ttk.Label(self.params_frame, text="Timezone:", style='Normal.TLabel').grid(row=0, column=2, sticky=tk.W, padx=5)
        self.timezone_var = tk.StringVar(value="America/New_York")
        tz_combo = ttk.Combobox(self.params_frame, textvariable=self.timezone_var, width=24)
        tz_combo['values'] = sorted(set(LOCALE_TZ_MAP.values()) | set(EXTRA_TZ))
        tz_combo.grid(row=0, column=3, sticky=tk.W, padx=5)

        ttk.Button(self.params_frame, text="Set Default", command=self.reset_params).grid(row=0, column=4, padx=10)

        # ── Options ────────────────────────────────────────────────────────
        options_frame = ttk.LabelFrame(main_frame, text="Options", padding="10")
        options_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))

        self.json_var = tk.BooleanVar(value=False)
        self.json_check = ttk.Checkbutton(options_frame, text="Output as JSON", variable=self.json_var)
        self.json_check.grid(row=0, column=0, sticky=tk.W, padx=5)

        self.save_var = tk.BooleanVar(value=False)
        self.save_check = ttk.Checkbutton(options_frame, text="Save to file", variable=self.save_var)
        self.save_check.grid(row=0, column=1, sticky=tk.W, padx=5)

        # ── Scan Locales (для сканування ключів) ─────────────────────────
        ttk.Label(options_frame, text="Scan Locales (comma/space separated):", style='Normal.TLabel').grid(row=0, column=2, sticky=tk.W, padx=(20,5))
        self.scan_locales_var = tk.StringVar(value="en-US,uk-UA,zh-CN")
        scan_locales_entry = ttk.Entry(options_frame, textvariable=self.scan_locales_var, width=30)
        scan_locales_entry.grid(row=0, column=3, sticky=tk.W, padx=5)

        # ── Buttons ──────────────────────────────────────────────────────
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 15))

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
        self.status_label.grid(row=5, column=0, columnspan=3, sticky=tk.W, pady=(0, 10))

        # ── Results Notebook ──────────────────────────────────────────────
        output_frame = ttk.LabelFrame(main_frame, text="Results", padding="10")
        output_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 0))

        header_frame = ttk.Frame(output_frame)
        header_frame.pack(fill=tk.X, pady=(0, 10))

        self.status_icon_var = tk.StringVar(value="")
        self.status_icon_label = ttk.Label(header_frame, textvariable=self.status_icon_var, font=('Arial', 16))
        self.status_icon_label.pack(side=tk.LEFT, padx=(0, 10))

        self.ota_link_label = ttk.Label(header_frame, text="", font=('Courier', 10))
        self.ota_link_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.ota_link_label.bind('<Button-1>', self.on_header_link_click)

        self.copy_link_button = ttk.Button(header_frame, text="Copy link", command=self.on_copy_link_click, state=tk.DISABLED)
        self.copy_link_button.pack(side=tk.RIGHT, padx=(10, 0))

        self.notebook = ttk.Notebook(output_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Description tab
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

        # Full Log tab
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
        self.current_ota_precondition = ''
        self.current_ota_postcondition = ''

        # Raw Response tab
        self.raw_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.raw_frame, text="Raw Response")
        self._build_raw_tab()

        # HTTP Info tab
        self.httpinfo_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.httpinfo_frame, text="HTTP Info")
        self._build_httpinfo_tab()

        # Bruteforce tab
        self.brute_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.brute_frame, text="Bruteforce")
        self._build_bruteforce_tab()

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(6, weight=1)

    # ── Обробник зміни вкладки (приховування/показ параметрів) ──────────
    def _on_tab_changed(self, event):
        current = self.notebook.index(self.notebook.select())
        tab_text = self.notebook.tab(current, "text")
        if tab_text == "Bruteforce":
            self.params_frame.grid_remove()   # ховаємо
        else:
            self.params_frame.grid()          # показуємо

    # ── Locale ↔ Timezone auto-fill ──────────────────────────────────────
    def _on_locale_selected(self, event):
        loc = self.locale_var.get().strip()
        if loc in LOCALE_TZ_MAP:
            self.timezone_var.set(LOCALE_TZ_MAP[loc])

    def _on_locale_typed(self, event):
        if event.keysym == 'Return':
            loc = self.locale_var.get().strip()
            if loc in LOCALE_TZ_MAP:
                self.timezone_var.set(LOCALE_TZ_MAP[loc])

    def reset_params(self):
        self.locale_var.set("en-US")
        self.timezone_var.set("America/New_York")
        self.update_status("Parameters reset to default", 'success')

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

            def _copy_value(event=None):
                sel = tv.selection()
                if not sel:
                    return
                value = tv.item(sel[0], 'values')[1]
                self.root.clipboard_clear()
                self.root.clipboard_append(value)
                self.httpinfo_status_var.set(f"Copied: {value[:80]}{'…' if len(value) > 80 else ''}")

            def _copy_row(event=None):
                sel = tv.selection()
                if not sel:
                    return
                k, v = tv.item(sel[0], 'values')
                self.root.clipboard_clear()
                self.root.clipboard_append(f"{k}: {v}")
                self.httpinfo_status_var.set(f"Copied row: {k}")

            tv.bind('<<TreeviewSelect>>', _copy_value)
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

        meta_f = ttk.Frame(self.httpinfo_nb)
        self.httpinfo_nb.add(meta_f, text="Payload Metadata")

        meta_tree_wrap = ttk.Frame(meta_f)
        meta_tree_wrap.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        cols = ("field", "value")
        self.hi_tree_metadata = ttk.Treeview(meta_tree_wrap, columns=cols, show="headings")
        self.hi_tree_metadata.heading("field", text="Field")
        self.hi_tree_metadata.heading("value", text="Value")
        self.hi_tree_metadata.column("field", width=260, stretch=False)
        self.hi_tree_metadata.column("value", width=560, stretch=True)
        meta_sb = ttk.Scrollbar(meta_tree_wrap, orient=tk.VERTICAL, command=self.hi_tree_metadata.yview)
        self.hi_tree_metadata.configure(yscrollcommand=meta_sb.set)
        self.hi_tree_metadata.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        meta_sb.pack(side=tk.RIGHT, fill=tk.Y)

        def _copy_meta_value(event=None):
            sel = self.hi_tree_metadata.selection()
            if not sel:
                return
            value = self.hi_tree_metadata.item(sel[0], 'values')[1]
            self.root.clipboard_clear()
            self.root.clipboard_append(value)

        def _copy_meta_row(event=None):
            sel = self.hi_tree_metadata.selection()
            if not sel:
                return
            k, v = self.hi_tree_metadata.item(sel[0], 'values')
            self.root.clipboard_clear()
            self.root.clipboard_append(f"{k}: {v}")

        self.hi_tree_metadata.bind('<<TreeviewSelect>>', _copy_meta_value)
        self.hi_tree_metadata.bind('<Double-ButtonRelease-1>', _copy_meta_row)

        meta_side = ttk.Frame(meta_f, padding=(8, 6), width=270)
        meta_side.pack(side=tk.RIGHT, fill=tk.Y)
        meta_side.pack_propagate(False)
        ttk.Label(meta_side, text="Status", font=('TkDefaultFont', 9, 'bold')).pack(anchor=tk.N, pady=(0, 4))
        self.hi_metadata_status_var = tk.StringVar(value="")
        ttk.Label(meta_side, textvariable=self.hi_metadata_status_var, wraplength=220,
                  justify=tk.LEFT, foreground='#666666').pack(anchor=tk.N, fill=tk.X)

        alt_f = ttk.Frame(self.httpinfo_nb)
        self.httpinfo_nb.add(alt_f, text="Alternative Filenames")

        alt_wrap = ttk.Frame(alt_f)
        alt_wrap.pack(fill=tk.BOTH, expand=True)
        self.hi_list_altnames = tk.Listbox(alt_wrap, font=('Courier', 9), activestyle='none',
                                            exportselection=False)
        alt_sb = ttk.Scrollbar(alt_wrap, orient=tk.VERTICAL, command=self.hi_list_altnames.yview)
        self.hi_list_altnames.configure(yscrollcommand=alt_sb.set)
        self.hi_list_altnames.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        alt_sb.pack(side=tk.RIGHT, fill=tk.Y)

        def _copy_alt_selection(event=None):
            sel = self.hi_list_altnames.curselection()
            if not sel:
                return
            value = self.hi_list_altnames.get(sel[0])
            self.root.clipboard_clear()
            self.root.clipboard_append(value)

        self.hi_list_altnames.bind('<<ListboxSelect>>', _copy_alt_selection)

        self._httpinfo_last_result = None
        self._httpinfo_metadata_loaded = False
        self._httpinfo_altnames_loaded = False
        self._httpinfo_pending_jobs = 0

    def _httpinfo_start(self):
        url = self.httpinfo_url_var.get().strip()
        if not url:
            messagebox.showerror("HTTP Info", "Please enter an OTA URL first.")
            return

        try:
            current_tab_text = self.httpinfo_nb.tab(self.httpinfo_nb.select(), 'text')
        except Exception:
            current_tab_text = None

        self.httpinfo_fetch_btn.config(state=tk.DISABLED)
        self.httpinfo_progress.start(12)

        if current_tab_text in ("Payload Metadata", "Alternative Filenames"):
            self.httpinfo_status_var.set("Fetching metadata and alternative filenames…")
            self._httpinfo_pending_jobs = 2

            for ch in self.hi_tree_metadata.get_children():
                self.hi_tree_metadata.delete(ch)
            self.hi_metadata_status_var.set("Loading…")

            self.hi_list_altnames.delete(0, tk.END)
            self.hi_list_altnames.insert(tk.END, "Checking…")

            threading.Thread(target=self._httpinfo_metadata_worker, args=(url,), daemon=True).start()
            threading.Thread(target=self._httpinfo_altnames_worker, args=(url,), daemon=True).start()

        else:
            self.httpinfo_status_var.set("Probing…")
            self._httpinfo_pending_jobs = 1
            self._httpinfo_last_result = None
            threading.Thread(target=self._httpinfo_worker, args=(url,), daemon=True).start()

    def _httpinfo_worker(self, url):
        try:
            result = probe_ota_url(url, status_cb=lambda m: self.root.after(
                0, self.httpinfo_status_var.set, m))
            self._httpinfo_last_result = result
            self.root.after(0, self._httpinfo_display, result)
        except Exception as exc:
            self.root.after(0, self.httpinfo_status_var.set, f"Error: {exc}")
        finally:
            self.root.after(0, self._httpinfo_done)

    def _httpinfo_done(self):
        self.httpinfo_progress.stop()
        self.httpinfo_fetch_btn.config(state=tk.NORMAL)
        self._httpinfo_pending_jobs = max(0, self._httpinfo_pending_jobs - 1)
        if self._httpinfo_pending_jobs == 0:
            current = self.httpinfo_status_var.get()
            if current in ("Fetching metadata and alternative filenames…", "Probing…"):
                self.httpinfo_status_var.set("")

    def _httpinfo_metadata_worker(self, url):
        try:
            meta = fetch_payload_metadata(url, status_cb=lambda m: self.root.after(
                0, self.hi_metadata_status_var.set, m))
            self.root.after(0, self._httpinfo_display_metadata, meta)
        except Exception as exc:
            self.root.after(0, self.hi_metadata_status_var.set, f"Metadata error: {exc}")
        finally:
            self.root.after(0, self._httpinfo_done)

    def _httpinfo_altnames_worker(self, url):
        meta = {}
        try:
            meta = fetch_payload_metadata(url)
        except Exception:
            pass

        last_modified = ''
        for label, val in (self._httpinfo_last_result or {}).get('general', []):
            if label == 'Last-Modified':
                last_modified = val
                break
        if not last_modified:
            try:
                req = urllib.request.Request(url, method='HEAD', headers={
                    'User-Agent': 'OTA-Prober/2.0',
                    'Accept-Encoding': 'identity',
                })
                ctx = ssl.create_default_context()
                with urllib.request.urlopen(req, timeout=12, context=ctx) as resp:
                    last_modified = resp.headers.get('Last-Modified', '') or ''
            except Exception:
                pass

        try:
            pre_fp = meta.get('fields', {}).get('pre-build') or self.current_ota_precondition
            post_fp = meta.get('fields', {}).get('post-build') or self.current_ota_postcondition
            alt = probe_alternative_filenames(
                url, last_modified,
                pre_fp, post_fp,
                status_cb=lambda m: self.root.after(
                    0, lambda: (self.hi_list_altnames.delete(0, tk.END),
                                self.hi_list_altnames.insert(tk.END, m))))
            self.root.after(0, self._httpinfo_display_altnames, alt)
        except Exception as exc:
            self.root.after(0, self._httpinfo_display_altnames,
                             {'checked': False, 'reason': f"Error: {exc}", 'results': []})
        finally:
            self.root.after(0, self._httpinfo_done)

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

    def _httpinfo_display_metadata(self, meta: dict):
        for ch in self.hi_tree_metadata.get_children():
            self.hi_tree_metadata.delete(ch)

        if meta.get('found'):
            for k, v in meta.get('fields', {}).items():
                self.hi_tree_metadata.insert("", tk.END, values=(k, v))
            self.hi_metadata_status_var.set(
                f"Found in {meta.get('source', '?')} — {len(meta.get('fields', {}))} field(s)")
        else:
            err = meta.get('error') or "No metadata fields found (package may not expose plaintext metadata)."
            self.hi_metadata_status_var.set(err.strip(' |'))

    def _httpinfo_display_altnames(self, alt: dict):
        self.hi_list_altnames.delete(0, tk.END)

        if not alt.get('checked'):
            self.hi_list_altnames.insert(tk.END, alt.get('reason', 'Not checked'))
            return

        working = [candidate_url for name, candidate_url, ok in alt.get('results', []) if ok]
        if not working:
            self.hi_list_altnames.insert(tk.END, "No working alternative links found.")
            return

        for url in working:
            self.hi_list_altnames.insert(tk.END, url)

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
        ttk.Label(fp_lf, text="Use {BUILD}, {INC} and {KEY} as placeholders:").pack(anchor=tk.W)   # видалено {LOCALE}
        self.brute_fp_var = tk.StringVar(
            value="google/baracus/baracus:6.0/{BUILD}/{INC}:{KEY}"
        )
        ttk.Entry(fp_lf, textvariable=self.brute_fp_var, font=('Courier', 9)).pack(fill=tk.X, pady=3)
        ttk.Label(fp_lf, text="{BUILD} = build ID   {INC} = incremental   {KEY} = key type",
                  foreground='#666666').pack(anchor=tk.W)

        mid = ttk.Frame(wrapper)
        mid.pack(fill=tk.X, pady=(0, 6))
        mid.columnconfigure(0, weight=3)   # Build Tags
        mid.columnconfigure(1, weight=3)   # Key Types
        mid.columnconfigure(2, weight=1)   # Locales
        mid.columnconfigure(3, weight=0)   # Incremental

        # Build Tags
        bt_lf = ttk.LabelFrame(mid, text="Build Tags", padding="6")
        bt_lf.grid(row=0, column=0, sticky=tk.NSEW, padx=(0, 6))
        self.brute_tags_text = tk.Text(bt_lf, height=4, font=('Courier', 9))
        self.brute_tags_text.pack(fill=tk.BOTH, expand=True)
        self.brute_tags_text.insert(tk.END, "MRTA.181211.008")

        # Key Types
        kt_lf = ttk.LabelFrame(mid, text="Key Types", padding="6")
        kt_lf.grid(row=0, column=1, sticky=tk.NSEW, padx=(0, 6))
        self.brute_keys_text = tk.Text(kt_lf, height=4, font=('Courier', 9))
        self.brute_keys_text.pack(fill=tk.BOTH, expand=True)
        self.brute_keys_text.insert(tk.END,
            "user/release-keys\nuser/test-keys")

        # Locales (тепер у колонці 2)
        loc_lf = ttk.LabelFrame(mid, text="Locales", padding="6")
        loc_lf.grid(row=0, column=2, sticky=tk.NSEW, padx=(0, 6))
        self.brute_locales_text = tk.Text(loc_lf, height=4, font=('Courier', 9))
        self.brute_locales_text.pack(fill=tk.BOTH, expand=True)
        self.brute_locales_text.insert(tk.END, "en-US\nuk-UA\nru-RU")

        # Incremental Range (тепер у колонці 3)
        inc_lf = ttk.LabelFrame(mid, text="Incremental Range", padding="6")
        inc_lf.grid(row=0, column=3, sticky=tk.NSEW)
        inc_lf.columnconfigure(1, weight=1)
        self.brute_inc_start_var = tk.StringVar(value="370000")
        self.brute_inc_end_var = tk.StringVar(value="400000")
        self.brute_inc_step_var = tk.StringVar(value="1")
        for row_i, (lbl, var) in enumerate(zip(
                ["Start:", "End:", "Step:"],
                [self.brute_inc_start_var, self.brute_inc_end_var, self.brute_inc_step_var])):
            ttk.Label(inc_lf, text=lbl).grid(row=row_i, column=0, sticky=tk.W, pady=3)
            ttk.Entry(inc_lf, textvariable=var, width=12).grid(row=row_i, column=1, sticky=tk.EW, padx=(6, 0), pady=3)

        # Options
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

        text.tag_configure('found', foreground='#006600', font=('Courier', 9, 'bold'))
        text.tag_configure('skip', foreground='#aaaaaa')
        text.tag_configure('error', foreground='#cc0000')
        text.tag_configure('header', foreground='#004499', font=('Courier', 9, 'bold'))
        text.tag_configure('info', foreground='#333333')
        text.tag_configure('changed', foreground='#cc6600', font=('Courier', 9, 'bold'))

        for line, tag in self._brute_log_buffer:
            text.insert(tk.END, line + '\n', tag)
        text.see(tk.END)

        self._brute_log_window = win
        self._brute_log_text = text

    def _close_brute_log_window(self):
        if self._brute_log_window:
            self._brute_log_window.destroy()
            self._brute_log_window = None
            self._brute_log_text = None

    def _brute_log(self, msg, tag='info'):
        self._brute_log_buffer.append((msg, tag))
        if self._brute_log_text and self._brute_log_window and self._brute_log_window.winfo_exists():
            self._brute_log_text.insert(tk.END, msg + '\n', tag)
            self._brute_log_text.see(tk.END)

    def _brute_clear_log(self):
        self._brute_log_buffer.clear()
        if self._brute_log_text and self._brute_log_window and self._brute_log_window.winfo_exists():
            self._brute_log_text.delete(1.0, tk.END)

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
        # {LOCALE} більше не використовується

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

        raw_locales = self.brute_locales_text.get("1.0", tk.END).strip()
        locales = [l.strip() for l in raw_locales.splitlines() if l.strip()]
        if not locales:
            # Якщо не задано жодної локаль, використовуємо поточну з головного вікна або en-US
            default_loc = self.locale_var.get().strip()
            locales = [default_loc if default_loc else "en-US"]

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
        locale_count = len(locales)   # завжди враховуємо локалі
        total = build_count * key_count * inc_count * locale_count
        if total == 0:
            total = 1

        self._brute_stop_flag = False
        self._brute_pause_event.set()
        self._brute_found_data.clear()
        self._brute_found_count = 0
        self._brute_processed = 0
        self._brute_total = total

        self._brute_clear_log()

        self.brute_start_btn.config(state=tk.DISABLED)
        self.brute_pause_btn.config(state=tk.NORMAL)
        self.brute_continue_btn.config(state=tk.DISABLED)
        self.brute_stop_btn.config(state=tk.NORMAL)
        self.brute_progress['maximum'] = total
        self.brute_progress['value'] = 0

        self._brute_log(f"Starting bruteforce: {total} combinations", 'header')
        self._brute_log(f"Template: {template}", 'header')
        self._brute_log(f"Locales to test: {', '.join(locales)}", 'header')
        self._brute_log("=" * 70, 'header')

        try:
            n_workers = max(1, min(1000, int(self.brute_workers_var.get())))
        except ValueError:
            n_workers = 10

        self._brute_queue = queue.Queue(maxsize=n_workers * 2)

        self._brute_producer_thread = threading.Thread(
            target=self._brute_producer,
            args=(build_tags, key_types, inc_start, inc_end, inc_step, template, n_workers,
                  use_build, use_inc, use_key, locales),
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
                        use_build, use_inc, use_key, locales):
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
                        for loc in locales:
                            if self._brute_stop_flag:
                                break
                            self._brute_queue.put((bt, kt, str(inc) if use_inc else "", loc, template), block=True)
                        if self._brute_stop_flag:
                            break
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
            build_tag, key_type, inc, loc, template = item

            fp = template
            if '{BUILD}' in template:
                fp = fp.replace('{BUILD}', build_tag)
            if '{INC}' in template:
                fp = fp.replace('{INC}', inc)
            if '{KEY}' in template:
                fp = fp.replace('{KEY}', key_type)
            # {LOCALE} більше не замінюється

            # Отримуємо timezone для даного locale
            tz = LOCALE_TZ_MAP.get(loc, 'America/New_York')

            max_retries = 3
            for attempt in range(max_retries):
                if self._brute_stop_flag:
                    break
                self._brute_pause_event.wait()
                if self._brute_stop_flag:
                    break
                try:
                    # ЗАВЖДИ передаємо locale та timezone у запит
                    settings, _raw = perform_checkin(fp, locale=loc, timezone=tz)
                    if not settings:
                        if attempt == max_retries - 1:
                            self._brute_log(f"  BUILD={build_tag} KEY={key_type} INC={inc} LOCALE={loc} → no response (after {max_retries} retries)", 'skip')
                            self._brute_increment_progress()
                        else:
                            time.sleep(1)
                        continue
                    ota = find_ota_link(settings)
                    self._brute_process_result(fp, build_tag, key_type, inc, loc, ota)
                    self._brute_increment_progress()
                    break
                except Exception as e:
                    if attempt == max_retries - 1:
                        self._brute_log(f"  BUILD={build_tag} KEY={key_type} INC={inc} LOCALE={loc} → ERROR: {e} (after {max_retries} retries)", 'error')
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

    def _brute_process_result(self, fp, build_tag, key_type, inc, loc, ota):
        skip_dupes = self.brute_skip_dupes_var.get()
        pause_on_find = self.brute_stop_on_find_var.get()
        save_otas = self.brute_save_otas_var.get()

        if ota is None:
            self._brute_log(f"  BUILD={build_tag} KEY={key_type} INC={inc} LOCALE={loc} → no OTA", 'skip')
            return
        url = ota.get('url')
        if not url:
            self._brute_log(f"  BUILD={build_tag} KEY={key_type} INC={inc} LOCALE={loc} → no OTA URL", 'skip')
            return

        title = ota.get('title', '')
        desc = ota.get('description', '')
        size = ota.get('size', '')
        meta = (title, desc, size)

        with self._brute_progress_lock:
            self._brute_found_count += 1

        with self._brute_progress_lock:
            meta_set = self._brute_found_data.get(url)
            if meta_set is None:
                # New URL
                self._brute_found_data[url] = {meta}
                is_new = True
                is_changed = False
                is_duplicate = False
            else:
                if meta in meta_set:
                    # Same metadata already seen for this URL
                    is_new = False
                    is_changed = False
                    is_duplicate = True
                else:
                    # New metadata set for this URL
                    meta_set.add(meta)
                    is_new = False
                    is_changed = True
                    is_duplicate = False

        if is_duplicate:
            if skip_dupes:
                self._brute_log(f"  BUILD={build_tag} KEY={key_type} INC={inc} LOCALE={loc} → OTA found (duplicate URL and metadata, skipped)", 'skip')
            else:
                self._brute_log(f"  BUILD={build_tag} KEY={key_type} INC={inc} LOCALE={loc} → OTA found (duplicate URL and metadata)", 'found')
            return

        # Log the result
        if is_new:
            local_count = len(self._brute_found_data)
            self._brute_log(f"", 'found')
            self._brute_log(f"  ★ NEW #{local_count}  BUILD={build_tag}  KEY={key_type}  INC={inc}  LOCALE={loc}", 'found')
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
            # Determine what changed for a meaningful message
            # Compare with any other metadata set for this URL
            other_meta = next(iter(meta_set - {meta}))
            other_title, other_desc, other_size = other_meta
            changed_title = (other_title != title)
            changed_desc = (other_desc != desc)
            if changed_title or changed_desc:
                change_msg = "Found OTA with different description (UPDATED)"
            elif other_size != size:
                change_msg = "OTA size changed (UPDATED)"
            else:
                change_msg = "OTA metadata updated (UPDATED)"
            local_count = len(self._brute_found_data)
            self._brute_log(f"", 'changed')
            self._brute_log(f"  ⚡ {change_msg}  BUILD={build_tag}  KEY={key_type}  INC={inc}  LOCALE={loc}", 'changed')
            self._brute_log(f"    Fingerprint : {fp}", 'changed')
            self._brute_log(f"    URL         : {url}", 'changed')
            if title:
                self._brute_log(f"    Title       : {title}", 'changed')
            if desc:
                self._brute_log(f"    Description : {desc[:80]}{'...' if len(desc)>80 else ''}", 'changed')
            if size:
                self._brute_log(f"    Size        : {size}", 'changed')
            self._brute_log(f"", 'changed')
        else:
            return  # should not happen

        # Save to OTAs.txt if enabled
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

        # Pause only when a completely new OTA URL is found (not on updates)
        if pause_on_find and is_new:
            self._brute_pause_event.clear()
            self.brute_pause_btn.config(state=tk.DISABLED)
            self.brute_continue_btn.config(state=tk.NORMAL)
            self.brute_stop_btn.config(state=tk.NORMAL)
            pause_msg = f"⏸ Paused after new OTA found (#{local_count}) — press Continue"
            self.brute_status_var.set(pause_msg)

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

    def on_copy_link_click(self):
        if not self.current_ota_link:
            self.status_var.set("No link to copy yet")
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(self.current_ota_link)
        self.status_var.set("Link copied to clipboard")

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
        self.copy_link_button.config(state=tk.DISABLED)
        self.update_status("Output cleared")

    def on_copy_click(self):
        try:
            content = self.output_text.get(1.0, tk.END)
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.update_status("Copied to clipboard", 'success')
        except Exception as e:
            self.update_status(f"Failed to copy: {e}", 'error')

    def _meta_autofill_url(self, url: str):
        self.httpinfo_url_var.set(url)

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
            self.copy_link_button.config(state=tk.DISABLED)
            self.update_status("Parsing fingerprint...")

            parsed = parse_fingerprint(fingerprint)
            self.update_status("Sending check-in request...")

            locale = self.locale_var.get().strip()
            timezone = self.timezone_var.get().strip()

            settings, raw_bytes = perform_checkin(fingerprint, locale, timezone)

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
                        'locale': locale,
                        'timezone': timezone,
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
                            'locale': locale,
                            'timezone': timezone,
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
            self.current_ota_precondition = ota_link.get('precondition', '')
            self.current_ota_postcondition = ota_link.get('postcondition', '')
            header_text = f"🔗 {ota_link['url']}"
            self.ota_link_label.config(text=header_text, foreground='#0066cc')
            self.copy_link_button.config(state=tk.NORMAL)
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
            self.copy_link_button.config(state=tk.DISABLED)
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

            # Отримуємо список locale з поля Scan Locales
            scan_locales_str = self.scan_locales_var.get().strip()
            if scan_locales_str:
                import re
                locales = [loc.strip() for loc in re.split(r'[,\s\n]+', scan_locales_str) if loc.strip()]
            else:
                locales = [self.locale_var.get().strip()]

            self.log_output("=" * 75, 'header')
            self.log_output("KEY TYPE SCAN RESULTS", 'header')
            self.log_output("=" * 75, 'header')
            self.log_output(f"Fingerprint base: {prefix}:", 'info')
            self.log_output(f"Locales: {', '.join(locales)}", 'info')
            self.log_output("")

            found_links = []
            total = len(key_types) * len(locales)
            counter = 0

            for loc in locales:
                tz = LOCALE_TZ_MAP.get(loc, 'America/New_York')
                for key in key_types:
                    counter += 1
                    test_fp = f"{prefix}:{key}"
                    self.log_output(f"[{counter}/{total}] Locale: {loc}  Key: {key}", 'section')
                    self.log_output(f"  Fingerprint: {test_fp}", 'info')
                    self.update_status(f"Scanning {key} with {loc} ({counter}/{total})...")

                    try:
                        settings, raw_bytes = perform_checkin(test_fp, locale=loc, timezone=tz)
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
                            found_links.append((key, loc, ota['url'], ota.get('title', ''), ota.get('size', '')))
                        else:
                            self.log_output("  Status: ❌ No OTA", 'error')
                    except Exception as e:
                        self.log_output(f"  Status: ❌ Error: {e}", 'error')

                    self.log_output("", 'info')

            self.log_output("=" * 75, 'header')
            if found_links:
                self.log_output(f"SUMMARY: Found {len(found_links)} OTA link(s)", 'success')
                for key, loc, url, title, size in found_links:
                    self.log_output(f"  - {key}  (locale {loc}) → {url}", 'success')
                    if title:
                        self.log_output(f"      Title: {title}", 'info')
                    if size:
                        self.log_output(f"      Size: {size}", 'info')
            else:
                self.log_output("SUMMARY: No OTA links found for any key type or locale", 'error')
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


def build_checkin_request(fingerprint, locale="en-US", timezone="America/New_York"):
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
    request += encode_string(6, locale)
    request += encode_string(12, timezone)
    request += encode_int64(14, 3)
    request += encode_int64(20, 0)
    request += encode_int64(22, 0)

    return request


def perform_checkin(fingerprint, locale="en-US", timezone="America/New_York"):
    try:
        parsed = parse_fingerprint(fingerprint)
        request_data = build_checkin_request(fingerprint, locale, timezone)
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


# ── Payload metadata extractor ───────────────────────────────────────────

PAYLOAD_METADATA_PREFIXES = [
    'post-build',
    'pre-build',
    'pre-device',
    'post-build-incremental',
    'post-sdk-level',
    'post-security-patch-level',
    'post-timestamp',
    'ota-type',
    'ota-required-cache',
    'pre-build-incremental',
]

EOCD_SIG = b'PK\x05\x06'
CDFH_SIG = b'PK\x01\x02'
LFH_SIG = b'PK\x03\x04'


def _extract_metadata_kv(blob: bytes, prefixes) -> dict:
    """
    Narrow scan used against a *raw, mostly-binary* chunk (e.g. the tail of
    a ZIP file before we've located/decompressed the actual metadata
    entry). Only pulls out the known prefixes, to avoid picking up noise
    from unrelated binary bytes that happen to contain '='.
    """
    result = {}
    for prefix in prefixes:
        needle = f'{prefix}='.encode('utf-8')
        start = blob.find(needle)
        if start == -1:
            continue
        val_start = start + len(needle)
        end = blob.find(b'\n', val_start)
        if end == -1:
            end = len(blob)
        try:
            value = blob[val_start:end].decode('utf-8', errors='replace').strip('\r')
        except Exception:
            continue
        if value:
            result[prefix] = value
    return result


def _parse_all_metadata_lines(blob: bytes, known_prefixes) -> dict:
    """
    Full scan used against a *clean, decompressed* metadata text blob
    (the actual contents of META-INF/com/android/metadata once we've
    correctly located and inflated it). Parses every `key=value` line,
    not just the ones in `known_prefixes`. Known keys are returned first,
    in their listed order; every other key found in the file (ota-id,
    ota-property-files, patch_type, version_name, wipe,
    reserve-image-size, india-image-size, etc.) is appended afterwards, in
    the order it appeared in the file, so nothing the file contains gets
    silently dropped regardless of OEM-specific fields.
    """
    try:
        text = blob.decode('utf-8', errors='replace')
    except Exception:
        return {}

    all_lines = {}
    order = []
    for raw_line in text.splitlines():
        line = raw_line.strip('\r').strip()
        if not line or '=' not in line:
            continue
        key, _, value = line.partition('=')
        key = key.strip()
        value = value.strip()
        if not key or not value:
            continue
        if key not in all_lines:
            order.append(key)
        all_lines[key] = value

    result = {}
    for prefix in known_prefixes:
        if prefix in all_lines:
            result[prefix] = all_lines[prefix]

    for key in order:
        if key not in result:
            result[key] = all_lines[key]

    return result


def _find_zip_metadata_entry(tail_blob: bytes, tail_offset: int):
    """
    Look for the End Of Central Directory record inside `tail_blob`, then
    walk the central directory to find the META-INF/com/android/metadata
    entry. Returns (local_header_offset, compressed_size, compression_method,
    file_name) or None if not found.
    """
    eocd_pos = tail_blob.rfind(EOCD_SIG)
    if eocd_pos == -1:
        return None

    try:
        cd_size = struct.unpack('<I', tail_blob[eocd_pos + 12:eocd_pos + 16])[0]
        cd_offset = struct.unpack('<I', tail_blob[eocd_pos + 16:eocd_pos + 20])[0]
    except struct.error:
        return None

    # central directory offset is absolute in the *whole* file; convert
    # to an offset relative to our tail_blob if it falls inside it
    cd_start_in_blob = cd_offset - tail_offset
    if cd_start_in_blob < 0:
        # central directory isn't inside the fetched tail chunk at all
        return None

    pos = cd_start_in_blob
    end = cd_start_in_blob + cd_size
    while pos < end and pos < len(tail_blob) - 46:
        if tail_blob[pos:pos + 4] != CDFH_SIG:
            break
        compression_method = struct.unpack('<H', tail_blob[pos + 10:pos + 12])[0]
        compressed_size = struct.unpack('<I', tail_blob[pos + 20:pos + 24])[0]
        name_len = struct.unpack('<H', tail_blob[pos + 28:pos + 30])[0]
        extra_len = struct.unpack('<H', tail_blob[pos + 30:pos + 32])[0]
        comment_len = struct.unpack('<H', tail_blob[pos + 32:pos + 34])[0]
        local_header_offset = struct.unpack('<I', tail_blob[pos + 42:pos + 46])[0]
        name = tail_blob[pos + 46:pos + 46 + name_len]

        if name == b'META-INF/com/android/metadata':
            return local_header_offset, compressed_size, compression_method, name.decode()

        pos += 46 + name_len + extra_len + comment_len

    return None


# Допоміжна функція для пошуку локального заголовка в голові
def _find_local_metadata_header(data: bytes, offset: int = 0):
    """Find local file header for META-INF/com/android/metadata in a byte chunk."""
    pos = offset
    while pos < len(data) - 30:
        idx = data.find(LFH_SIG, pos)
        if idx == -1:
            break
        try:
            name_len = struct.unpack('<H', data[idx+26:idx+28])[0]
            extra_len = struct.unpack('<H', data[idx+28:idx+30])[0]
            if idx + 30 + name_len > len(data):
                pos = idx + 1
                continue
            name = data[idx+30:idx+30+name_len]
            if name == b'META-INF/com/android/metadata':
                compressed_size = struct.unpack('<I', data[idx+18:idx+22])[0]
                compression_method = struct.unpack('<H', data[idx+10:idx+12])[0]
                return idx, compressed_size, compression_method, name.decode()
        except struct.error:
            pass
        pos = idx + 1
    return None


def fetch_payload_metadata(url: str, status_cb=None, timeout: int = 30,
                            chunk_bytes: int = 2 * 1024 * 1024) -> dict:
    """
    Fetch OTA package metadata (pre/post build fingerprints, security patch
    level, timestamp, etc.) without downloading the whole file.

    Strategies:
    1) ZIP central directory in the tail (most reliable)
    2) local header search in the head (if metadata is near the start)
    3) naive key scan in head (known prefixes only, no garbage)
    """
    def _s(msg):
        if status_cb:
            status_cb(msg)

    out = {
        'found': False,
        'fields': {},
        'source': None,
        'error': None,
        'bytes_scanned': 0,
    }
    errors = []

    def _get_range(range_header):
        req = urllib.request.Request(url, headers={
            'User-Agent': 'OTA-Prober/2.0',
            'Accept-Encoding': 'identity',
            'Range': range_header,
        })
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
            return resp.read()

    def _head_size():
        head_req = urllib.request.Request(url, method='HEAD', headers={
            'User-Agent': 'OTA-Prober/2.0',
            'Accept-Encoding': 'identity',
        })
        ctx = ssl.create_default_context()
        with urllib.request.urlopen(head_req, timeout=timeout, context=ctx) as resp:
            return int(resp.headers.get('Content-Length', '0') or '0')

    total_size = 0
    try:
        total_size = _head_size()
    except Exception as e:
        errors.append(f"HEAD size lookup failed: {e}")

    # ── Tail fetch ──────────────────────────────────────────────────────────
    tail_data = b''
    tail_offset = 0
    if total_size > 0:
        try:
            tail_offset = max(0, total_size - chunk_bytes)
            _s(f"Fetching last {chunk_bytes // 1024 // 1024} MiB…")
            tail_data = _get_range(f'bytes={tail_offset}-{total_size - 1}')
            out['bytes_scanned'] += len(tail_data)
        except Exception as e:
            errors.append(f"Tail fetch failed: {e}")

    # ── Strategy 1: naive scan of tail chunk (works if STORED) ──────────
    if tail_data:
        anchor = -1
        for prefix in PAYLOAD_METADATA_PREFIXES:
            pos = tail_data.find(f'{prefix}='.encode('utf-8'))
            if pos != -1 and (anchor == -1 or pos < anchor):
                anchor = pos
        if anchor != -1:
            search_start = max(0, anchor - 4096)
            block_start = tail_data.rfind(LFH_SIG, search_start, anchor)
            if block_start == -1:
                block_start = search_start
            else:
                try:
                    name_len = struct.unpack('<H', tail_data[block_start + 26:block_start + 28])[0]
                    extra_len = struct.unpack('<H', tail_data[block_start + 28:block_start + 30])[0]
                    block_start = block_start + 30 + name_len + extra_len
                except struct.error:
                    pass
            block_end = tail_data.find(LFH_SIG, anchor)
            if block_end == -1:
                block_end = tail_data.find(CDFH_SIG, anchor)
            if block_end == -1:
                block_end = tail_data.find(EOCD_SIG, anchor)
            if block_end == -1:
                block_end = len(tail_data)
            fields = _parse_all_metadata_lines(tail_data[block_start:block_end], PAYLOAD_METADATA_PREFIXES)
            if fields:
                out['found'] = True
                out['fields'] = fields
                out['source'] = f'tail raw scan ({len(tail_data):,} bytes)'
                return out
        fields = _extract_metadata_kv(tail_data, PAYLOAD_METADATA_PREFIXES)
        if fields:
            out['found'] = True
            out['fields'] = fields
            out['source'] = f'tail raw scan ({len(tail_data):,} bytes, partial)'
            return out

    # ── Strategy 2: proper ZIP central-directory parse (handles DEFLATE) ──
    if tail_data:
        try:
            _s("Parsing ZIP central directory…")
            entry = _find_zip_metadata_entry(tail_data, tail_offset)
            if entry:
                local_header_offset, compressed_size, compression_method, name = entry

                lh_start_in_tail = local_header_offset - tail_offset
                if 0 <= lh_start_in_tail and lh_start_in_tail + 30 <= len(tail_data):
                    lh_blob = tail_data
                    lh_pos = lh_start_in_tail
                else:
                    _s("Fetching local file header…")
                    lh_blob = _get_range(
                        f'bytes={local_header_offset}-{local_header_offset + 4096}')
                    out['bytes_scanned'] += len(lh_blob)
                    lh_pos = 0

                if lh_blob[lh_pos:lh_pos + 4] == LFH_SIG:
                    name_len = struct.unpack('<H', lh_blob[lh_pos + 26:lh_pos + 28])[0]
                    extra_len = struct.unpack('<H', lh_blob[lh_pos + 28:lh_pos + 30])[0]
                    data_start_in_lh_blob = lh_pos + 30 + name_len + extra_len

                    if data_start_in_lh_blob + compressed_size <= len(lh_blob):
                        entry_data = lh_blob[data_start_in_lh_blob:data_start_in_lh_blob + compressed_size]
                    else:
                        abs_data_start = local_header_offset + 30 + name_len + extra_len
                        _s(f"Fetching {name} entry ({compressed_size} bytes)…")
                        entry_data = _get_range(
                            f'bytes={abs_data_start}-{abs_data_start + compressed_size - 1}')
                        out['bytes_scanned'] += len(entry_data)

                    if compression_method == 0:
                        plain = entry_data
                    elif compression_method == 8:
                        try:
                            plain = zlib.decompress(entry_data, -15)
                        except Exception as e:
                            errors.append(f"Inflate failed: {e}")
                            plain = b''
                    else:
                        errors.append(f"Unsupported compression method {compression_method}")
                        plain = b''

                    if plain:
                        fields = _parse_all_metadata_lines(plain, PAYLOAD_METADATA_PREFIXES)
                        if fields:
                            out['found'] = True
                            out['fields'] = fields
                            out['source'] = f'ZIP entry {name} (method={compression_method})'
                            return out
                        else:
                            errors.append(
                                "Metadata entry decoded but no known keys matched "
                                f"(first 200 bytes: {plain[:200]!r})")
                else:
                    errors.append("Local file header signature mismatch")
            else:
                errors.append("META-INF/com/android/metadata not found in central directory")
        except Exception as e:
            errors.append(f"ZIP parse failed: {e}")

    # ── Strategy 3: ZIP local header in head ──────────────────────────────
    if not out['found'] and total_size > 0:
        head_size = min(total_size, chunk_bytes)
        head_data = b''
        try:
            _s(f"Fetching first {head_size // 1024 // 1024} MiB (head) for local header…")
            head_data = _get_range(f'bytes=0-{head_size-1}')
            out['bytes_scanned'] += len(head_data)
        except Exception as e:
            errors.append(f"Head fetch for local header failed: {e}")

        if head_data:
            entry = _find_local_metadata_header(head_data, 0)
            if entry:
                local_offset, compressed_size, compression_method, name = entry
                name_len = struct.unpack('<H', head_data[local_offset+26:local_offset+28])[0]
                extra_len = struct.unpack('<H', head_data[local_offset+28:local_offset+30])[0]
                data_start = local_offset + 30 + name_len + extra_len
                if data_start + compressed_size <= len(head_data):
                    entry_data = head_data[data_start:data_start+compressed_size]
                else:
                    abs_data_start = data_start
                    _s(f"Fetching {name} entry ({compressed_size} bytes) from head…")
                    entry_data = _get_range(
                        f'bytes={abs_data_start}-{abs_data_start + compressed_size - 1}')
                    out['bytes_scanned'] += len(entry_data)

                if compression_method == 0:
                    plain = entry_data
                elif compression_method == 8:
                    try:
                        plain = zlib.decompress(entry_data, -15)
                    except Exception as e:
                        errors.append(f"Inflate failed (head): {e}")
                        plain = b''
                else:
                    errors.append(f"Unsupported compression method {compression_method} (head)")
                    plain = b''

                if plain:
                    fields = _parse_all_metadata_lines(plain, PAYLOAD_METADATA_PREFIXES)
                    if fields:
                        out['found'] = True
                        out['fields'] = fields
                        out['source'] = f'ZIP entry from head {name} (method={compression_method})'
                        return out
                    else:
                        errors.append("Head metadata entry decoded but no known keys matched")

    # ── Strategy 4: naive key scan in head (known prefixes only) ──────────
    if not out['found'] and total_size > 0:
        if 'head_data' not in locals() or not head_data:
            try:
                head_size = min(total_size, chunk_bytes)
                _s(f"Fetching first {head_size // 1024 // 1024} MiB (head) for key scan…")
                head_data = _get_range(f'bytes=0-{head_size-1}')
                out['bytes_scanned'] += len(head_data)
            except Exception as e:
                errors.append(f"Head fetch for key scan failed: {e}")
                head_data = b''
        if head_data:
            fields = _extract_metadata_kv(head_data, PAYLOAD_METADATA_PREFIXES)
            if fields:
                out['found'] = True
                out['fields'] = fields
                out['source'] = f'head raw scan (known prefixes only, {len(head_data):,} bytes)'
                return out

    out['error'] = " | ".join(errors) if errors else "metadata not found in head or tail"
    return out


# ── Alternative filename prober (legacy May 2016 naming scheme) ─────────

LEGACY_LASTMOD_PREFIX = "Mon, 16 May 2016"


def _build_id_from_fingerprint(fingerprint: str):
    """Return the build tag (e.g. 'BP1A.250505.005') and device codename
    from a raw fingerprint string, or (None, None) if it doesn't parse."""
    try:
        parsed = parse_fingerprint(fingerprint)
        return parsed['build_tag'], parsed['device']
    except Exception:
        return None, None


def _extract_sha1_from_url(url: str):
    """Pull the sha1-looking filename stem out of an OTA URL, e.g.
    https://.../AbCdEf0123456789....zip -> AbCdEf0123456789..."""
    path = urlparse(url).path
    fname = path.rsplit('/', 1)[-1]
    if fname.lower().endswith('.zip'):
        fname = fname[:-4]
    # strip any trailing ".XXXXXXXX" 8-char short-hash suffix if present,
    # keep only the leading sha1-like token before the first dot
    stem = fname.split('.')[0]
    return stem


def build_alternative_filenames(sha1: str, device: str, post_build_id: str,
                                 pre_build_id: str, incremental: str):
    """
    Generate the candidate legacy (~May 2016 era) OTA filenames for either
    the full-update naming scheme (pre+post build known) or the direct-OTA
    naming scheme (only post-build/incremental known).
    """
    names = []
    short = sha1[:8] if sha1 else ''

    if pre_build_id and post_build_id:
        names.append(f"{sha1}.signed-{device}-{post_build_id}-from-{pre_build_id}.zip")
        names.append(f"{sha1}.Dotasigned-{device}-{post_build_id}-from-{pre_build_id}.zip")
        names.append(f"{sha1}.signed-{device}-{post_build_id}-from-{pre_build_id}.{short}.zip")
        names.append(f"{sha1}.signed-signed-{device}-{post_build_id}-from-{pre_build_id}.zip")
        names.append(f"{sha1}.signed-signed-{device}-{post_build_id}-from-{pre_build_id}.{short}.zip")
    elif post_build_id and incremental:
        names.append(f"{sha1}.signed-{device}-ota-{incremental}.zip")
        names.append(f"{sha1}.signed-signed{device}-ota-{incremental}.zip")

    return names


def check_alternative_ota_names(base_prefix: str, candidates: list, status_cb=None, timeout: int = 12):
    """HEAD-check each candidate filename against base_prefix; return list
    of (name, url, working: bool) tuples."""
    def _s(msg):
        if status_cb:
            status_cb(msg)

    results = []
    for i, name in enumerate(candidates):
        candidate_url = base_prefix + name
        _s(f"Checking alternative {i+1}/{len(candidates)}…")
        working = False
        try:
            req = urllib.request.Request(candidate_url, method='HEAD', headers={
                'User-Agent': 'OTA-Prober/2.0',
                'Accept-Encoding': 'identity',
            })
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                working = resp.getcode() in (200, 206)
        except urllib.error.HTTPError as e:
            working = e.code in (200, 206)
        except Exception:
            working = False
        results.append((name, candidate_url, working))
    return results


def probe_alternative_filenames(url: str, last_modified: str,
                                 pre_build_fingerprint: str, post_build_fingerprint: str,
                                 status_cb=None, timeout: int = 12):
    """
    If the OTA link's Last-Modified date matches the legacy naming era
    (Mon, 16 May 2016), try substituting a set of historically-known
    filename patterns into the same directory and see which ones resolve
    (HTTP 200/206) instead of 404. Also normalizes 'ota-api' to 'ota'
    in the base URL, since that's the path form the legacy filenames use.

    pre_build_fingerprint / post_build_fingerprint are the raw fingerprint
    strings from the OTA link's precondition/postcondition fields (may be
    empty). Returns a dict with 'checked', 'reason', and 'results' (list of
    (name, url, working) tuples).
    """
    def _s(msg):
        if status_cb:
            status_cb(msg)

    out = {'checked': False, 'reason': None, 'results': []}

    if not last_modified or not last_modified.strip().startswith(LEGACY_LASTMOD_PREFIX):
        out['reason'] = f"Last-Modified doesn't match legacy date ({LEGACY_LASTMOD_PREFIX})"
        return out

    post_build_id, device = _build_id_from_fingerprint(post_build_fingerprint) if post_build_fingerprint else (None, None)
    pre_build_id, _ = _build_id_from_fingerprint(pre_build_fingerprint) if pre_build_fingerprint else (None, None)

    if not device:
        out['reason'] = "Could not determine device codename (post-build fingerprint missing or unparsable)"
        return out

    incremental = None
    if post_build_fingerprint:
        try:
            incremental = parse_fingerprint(post_build_fingerprint)['incremental']
        except Exception:
            incremental = None

    base_url = url
    if 'ota-api' in base_url:
        base_url = base_url.replace('ota-api', 'ota')

    parsed = urlparse(base_url)
    dir_path = parsed.path.rsplit('/', 1)[0] + '/'
    base_prefix = f"{parsed.scheme}://{parsed.netloc}{dir_path}"
    sha1 = _extract_sha1_from_url(base_url)

    original_fname = parsed.path.rsplit('/', 1)[-1]

    if '.signed-' in original_fname:
        # The link already uses the signed-* naming scheme, so there's no
        # need to brute-force every historical pattern — just strip
        # whatever comes after the sha1 (keeping only the .zip extension)
        # and check whether that trimmed-down name resolves on its own.
        trimmed_name = f"{sha1}.zip"
        candidates = [trimmed_name] if trimmed_name != original_fname else []
        if not candidates:
            out['reason'] = "Filename is already a bare sha1.zip — nothing to trim"
            return out
        out['checked'] = True
        _s("Checking trimmed sha1.zip variant…")
        out['results'] = check_alternative_ota_names(base_prefix, candidates, status_cb=status_cb, timeout=timeout)
        return out

    candidates = build_alternative_filenames(sha1, device, post_build_id, pre_build_id, incremental)

    if not candidates:
        out['reason'] = "Not enough build info to construct candidate filenames"
        return out

    out['checked'] = True
    _s(f"Checking {len(candidates)} alternative filename(s)…")
    out['results'] = check_alternative_ota_names(base_prefix, candidates, status_cb=status_cb, timeout=timeout)
    return out


# ── HTTP Info prober ──────────────────────────────────────────────────────

def probe_ota_url(url: str, status_cb=None, timeout: int = 15) -> dict:
    def _s(msg):
        if status_cb:
            status_cb(msg)

    results = []
    for i, name in enumerate(candidates):
        candidate_url = base_prefix + name
        _s(f"Checking alternative {i+1}/{len(candidates)}…")
        working = False
        try:
            req = urllib.request.Request(candidate_url, method='HEAD', headers={
                'User-Agent': 'OTA-Prober/2.0',
                'Accept-Encoding': 'identity',
            })
            ctx = ssl.create_default_context()
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                working = resp.getcode() in (200, 206)
        except urllib.error.HTTPError as e:
            working = e.code in (200, 206)
        except Exception:
            working = False
        results.append((name, candidate_url, working))
    return results


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
