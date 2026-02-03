#!/usr/bin/env python3

import sys
import gzip
import urllib.request
import urllib.error
import json
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


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
    if len(sys.argv) < 2:
        print("Usage: python probe.py <fingerprint> [OPTIONS]")
        print("\nOptions:")
        print("  --json         Output as JSON")
        print("  --save <file>  Save output to file")
        print("\nExample:")
        print("  python probe.py 'google/shamu/shamu:5.1/LYZ28E/1858530:user/release-keys'")
        sys.exit(1)
    
    fingerprints = []
    json_output = '--json' in sys.argv
    save_file = None
    
    if '--save' in sys.argv:
        idx = sys.argv.index('--save')
        if idx + 1 < len(sys.argv):
            save_file = sys.argv[idx + 1]
    
    for arg in sys.argv[1:]:
        if not arg.startswith('--') and '/' in arg:
            fingerprints.append(arg)
            break
    
    if not fingerprints:
        print("Error: No fingerprint provided")
        sys.exit(1)
    
    responses = {}
    build_infos = {}
    ota_links = {}
    
    fingerprint = fingerprints[0]
    print(f"Querying: {fingerprint}")
    
    try:
        parse_fingerprint(fingerprint)
    except ValueError as e:
        print(f"Error: Invalid fingerprint format\n{e}")
        sys.exit(1)
    
    settings = perform_checkin(fingerprint)
    
    if not settings:
        print("Error: Checkin failed")
        sys.exit(1)
    
    responses[fingerprint] = settings
    build_infos[fingerprint] = extract_build_details(fingerprint, settings)
    ota_links[fingerprint] = find_ota_link(settings)
    print(f"Received {get_service_summary(settings)} settings\n")
    
    output = format_output(
        fingerprints[0],
        responses[fingerprints[0]],
        build_infos[fingerprints[0]],
        ota_links[fingerprints[0]]
    )
    
    if json_output:
        json_data = {
            'fingerprint': fingerprints[0],
            'build_info': build_infos[fingerprints[0]],
            'ota_link': ota_links[fingerprints[0]],
            'total_settings': get_service_summary(responses[fingerprints[0]]),
        }
        output_str = json.dumps(json_data, indent=2)
    else:
        output_str = output
    
    try:
        print("\n" + output_str)
    except Exception:
        pass
    
    if save_file:
        with open(save_file, 'w', encoding='utf-8') as f:
            f.write(output_str)
        print(f"\n✓ Output saved to {save_file}")

if __name__ == '__main__':
    main()
