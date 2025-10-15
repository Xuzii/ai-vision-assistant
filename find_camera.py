#!/usr/bin/env python3
"""
Camera IP Scanner
Scans your local network to find IP cameras
"""

import socket
import ipaddress
import concurrent.futures
from typing import List, Tuple

def get_local_ip():
    """Get the local IP address of this machine"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        return local_ip
    except:
        return "192.168.1.1"

def check_port(ip: str, port: int, timeout: float = 0.5) -> bool:
    """Check if a port is open on an IP address"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def scan_ip(ip: str) -> Tuple[str, dict]:
    """Scan an IP for common camera ports"""
    ports_to_check = {
        80: 'HTTP',
        554: 'RTSP',
        8000: 'HTTP-Alt',
        8080: 'HTTP-Proxy',
        8554: 'RTSP-Alt'
    }

    open_ports = {}
    for port, service in ports_to_check.items():
        if check_port(ip, port, timeout=0.3):
            open_ports[port] = service

    if open_ports:
        return (ip, open_ports)
    return None

def scan_network(network: str = None):
    """Scan the local network for cameras"""
    if network is None:
        local_ip = get_local_ip()
        # Assume /24 network (common for home networks)
        network = '.'.join(local_ip.split('.')[:-1]) + '.0/24'

    print(f"\nScanning network: {network}")
    print("This may take 30-60 seconds...")
    print("-" * 60)

    try:
        net = ipaddress.ip_network(network, strict=False)
    except ValueError as e:
        print(f"ERROR: Invalid network: {e}")
        return []

    ips_to_scan = [str(ip) for ip in net.hosts()]
    found_devices = []

    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        futures = {executor.submit(scan_ip, ip): ip for ip in ips_to_scan}

        completed = 0
        for future in concurrent.futures.as_completed(futures):
            completed += 1
            if completed % 50 == 0:
                print(f"Progress: {completed}/{len(ips_to_scan)} IPs scanned...")

            result = future.result()
            if result:
                found_devices.append(result)

    return found_devices

def main():
    print("\n" + "=" * 60)
    print("IP CAMERA SCANNER")
    print("=" * 60)

    local_ip = get_local_ip()
    print(f"\nYour computer's IP: {local_ip}")

    devices = scan_network()

    print("\n" + "=" * 60)
    print("SCAN RESULTS")
    print("=" * 60)

    if not devices:
        print("\nNo devices found with camera-related ports open.")
        print("\nTroubleshooting:")
        print("  1. Make sure your camera is powered on")
        print("  2. Verify camera is connected to the same network")
        print("  3. Check your router's DHCP client list")
        print("  4. Try accessing camera's web interface manually")
        print("  5. Some cameras may have ports disabled by default")
        return

    print(f"\nFound {len(devices)} device(s) with camera ports open:\n")

    for ip, ports in sorted(devices):
        print(f"IP: {ip}")
        for port, service in sorted(ports.items()):
            print(f"  - Port {port} ({service}) is OPEN")

        if 554 in ports or 8554 in ports:
            print("  ** Likely a camera (RTSP port open) **")

        if 80 in ports or 8000 in ports or 8080 in ports:
            http_port = 80 if 80 in ports else (8000 if 8000 in ports else 8080)
            print(f"  Try accessing: http://{ip}:{http_port}")

        print()

    print("=" * 60)
    print("NEXT STEPS")
    print("=" * 60)
    print("\n1. Try accessing the HTTP URLs above in your browser")
    print("2. Look for the camera's web interface")
    print("3. Find the RTSP settings in the camera's admin panel")
    print("4. Note the camera's:")
    print("   - IP address")
    print("   - Username/password")
    print("   - RTSP port (usually 554)")
    print("   - RTSP stream path")
    print("\n5. Test connection with:")
    print("   python test_camera.py --ip <IP> --username <user> --password <pass>")

if __name__ == "__main__":
    main()
