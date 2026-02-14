#!/usr/bin/env python3

import sys
import gzip
import urllib.request
import urllib.error
import json
import io
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
from datetime import datetime
import webbrowser
try:
    from tkinterweb import HtmlFrame
except ImportError:
    HtmlFrame = None

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class OTAProberGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("OTA Prober")
        self.root.geometry("1000x700")
        self.root.configure(bg='#f0f0f0')
        
        self.setup_styles()
        self.create_widgets()
        self.query_thread = None
    
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
        self.clear_button.config(state=tk.DISABLED)
        self.fingerprint_entry.config(state=tk.DISABLED)
        
        self.query_thread = threading.Thread(target=self.perform_query, args=(fingerprint,), daemon=True)
        self.query_thread.start()
    
    def perform_query(self, fingerprint):
        try:
            self.output_text.delete(1.0, tk.END)
            if self.html_frame:
                self.html_frame.load_html("")
            elif self.desc_text:
                self.desc_text.delete(1.0, tk.END)
            self.url_map.clear()
            self.current_ota_link = None
            self.update_status("Parsing fingerprint...")
            
            parsed = parse_fingerprint(fingerprint)
            self.update_status("Sending check-in request...")
            
            settings = perform_checkin(fingerprint)
            
            if not settings:
                self.log_output("ERROR: Check-in failed - No response from server", 'error')
                self.status_icon_var.set("❌")
                self.update_status("Query failed", 'error')
            else:
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
            
            self.log_output(f"\n  Target URL:", 'info')
            self.output_text.insert(tk.END, "    ", 'info')
            self.log_link(ota_link['url'], ota_link['url'])
            self.output_text.insert(tk.END, '\n', 'info')
            
            self.current_ota_link = ota_link['url']
            header_text = f"🔗 {ota_link['url']}"
            self.ota_link_label.config(text=header_text, foreground='#0066cc')
            
            if ota_link['description']:
                desc = ota_link['description']
                
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
                    {desc}
                    </body>
                    </html>
                    """
                    self.html_frame.load_html(html_content)
                elif self.desc_text:
                    self.desc_text.insert(tk.END, desc)
                
                self.log_output(f"\n  Description:", 'info')
                desc_plain = desc.replace('<br>', '\n').replace('<p>', '').replace('</p>', '').replace('<strong>', '').replace('</strong>', '').replace('<a href="', '').replace('">', '').replace('</a>', '')
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
            else:
                if self.html_frame:
                    self.html_frame.load_html("<p>(No description available)</p>")
                elif self.desc_text:
                    self.desc_text.insert(tk.END, "(No description available)")
            
            if ota_link['precondition']:
                self.log_output(f"\n  Precondition:", 'info')
                self.log_output(f"    {ota_link['precondition']}", 'info')
            
            if ota_link['postcondition']:
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
            return settings
    
    except urllib.error.URLError as e:
        print(f"Error: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return None

def get_android_version(api_level):
    try:
        api_str = str(api_level)
        
        if '.' in api_str:
            version_to_api = {
                '1.0': 1, '1.1': 2, '1.5': 3, '1.6': 4, '2.0': 5, '2.0.1': 6, '2.1': 7,
                '2.2': 8, '2.3': 9, '2.3.3': 10, '3.0': 11, '3.1': 12, '3.2': 13, '4.0': 14,
                '4.0.2': 15, '4.1': 16, '4.1.1': 16, '4.2': 17, '4.3': 18, '4.4': 19, '4.4W': 20, 
                '5.0': 21, '5.0.1': 21, '5.1': 22, '5.1.1': 22, '6.0': 23, '6.0.1': 23, '7.0': 24, '7.0.1': 24, 
                '7.1': 25, '7.1.1': 25, '8.0': 26, '8.0.1': 26, '8.1': 27, '8.1.1': 27, '9.0': 28,
                '10.0': 29, '11.0': 30, '12.0': 31, '12L': 32, '13.0': 33, '14.0': 34, '15.0': 35, '16.0': 36
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
            18: '4.3', 19: '4.4', 20: '4.4W', 21: '5.0', 22: '5.1', 23: '6.0', 24: '7.0',
            25: '7.1', 26: '8.0', 27: '8.1', 28: '9.0', 29: '10.0', 30: '11.0', 31: '12.0',
            32: '12L', 33: '13.0', 34: '14.0', 35: '15.0', 36: '16.0'
        }
        
        if level in historical:
            return f'{historical[level]} (API {level})'
        elif level > 36:
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
        'description': settings.get('update_description', ''),
        'precondition': settings.get('update_precondition', ''),
        'postcondition': settings.get('update_postcondition', ''),
    }

def get_service_summary(settings):
    return len(settings)

def format_output(fingerprint, settings, build_info, ota_link):
    
    output = []
    output.append("=" * 75)
    output.append("DEVICE & BUILD INFORMATION")
    output.append("=" * 75)
    
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
        output.append(f"\n  Target URL:")
        output.append(f"    {ota_link['url']}")
        
        if ota_link['description']:
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
        
        if ota_link['precondition']:
            output.append(f"\n  Precondition:")
            output.append(f"    {ota_link['precondition']}")
        
        if ota_link['postcondition']:
            output.append(f"\n  Postcondition:")
            output.append(f"    {ota_link['postcondition']}")
    else:
        output.append(f"  Status:            [NONE] No Update Available")
    
    output.append("\n" + "=" * 75)
    
    return "\n".join(output)


def main():
    root = tk.Tk()
    app = OTAProberGUI(root)
    root.mainloop()


if __name__ == '__main__':
    main()
