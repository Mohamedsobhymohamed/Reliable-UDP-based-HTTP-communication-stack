import socket
import time
import hashlib
import random
import argparse

BUFFER_SIZE = 4096
TIMEOUT = 2

SYN = 0x01
ACK = 0x02
FIN = 0x04

class ReliableUDP:
    def __init__(self, local_addr, remote_addr=None, loss_prob=0.1, corrupt_prob=0.1):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(local_addr)
        self.remote_addr = remote_addr
        self.seq = 0
        self.ack = 0
        self.loss_prob = loss_prob
        self.corrupt_prob = corrupt_prob
        self.seen_seq = set()

    def compute_checksum(self, data):
        return hashlib.md5(data).hexdigest()

    def make_packet(self, seq, ack, flags, payload):
        header = f"{seq}|{ack}|{flags}|".encode()
        checksum = self.compute_checksum(header + payload).encode()
        return checksum + b"|" + header + payload

    def parse_packet(self, packet):
        try:
            parts = packet.split(b"|", 4)
            if len(parts) != 5:
                return None
            checksum, seq, ack, flags, payload = parts
            header_payload = b"|".join(parts[1:])
            if checksum.decode() != self.compute_checksum(header_payload):
                return None
            return int(seq), int(ack), int(flags), payload
        except Exception as e:
            return None

    def handshake(self, is_server=False):
        if not is_server:
            syn_packet = self.make_packet(self.seq, 0, SYN, b"")
            self.sock.sendto(syn_packet, self.remote_addr)
            while True:
                try:
                    self.sock.settimeout(TIMEOUT)
                    packet, _ = self.sock.recvfrom(BUFFER_SIZE)
                    parsed = self.parse_packet(packet)
                    if parsed is None:
                        continue
                    seq, ack, flags, _ = parsed
                    if flags & SYN and flags & ACK:
                        ack_packet = self.make_packet(self.seq, seq, ACK, b"")
                        self.sock.sendto(ack_packet, self.remote_addr)
                        print("[CLIENT] Handshake complete.")
                        break
                except socket.timeout:
                    self.sock.sendto(syn_packet, self.remote_addr)
        else:
            while True:
                try:
                    packet, addr = self.sock.recvfrom(BUFFER_SIZE)
                    parsed = self.parse_packet(packet)
                    if parsed is None:
                        continue
                    seq, ack, flags, _ = parsed
                    if flags & SYN:
                        self.remote_addr = addr
                        syn_ack = self.make_packet(0, seq, SYN | ACK, b"")
                        self.sock.sendto(syn_ack, addr)
                        packet, _ = self.sock.recvfrom(BUFFER_SIZE)
                        parsed = self.parse_packet(packet)
                        if parsed is None:
                            continue
                        _, ack, flags, _ = parsed
                        if flags & ACK:
                            print("[SERVER] Handshake complete.")
                            break
                except socket.timeout:
                    continue

    def close(self):
        fin_packet = self.make_packet(self.seq, 0, FIN, b"")
        self.sock.sendto(fin_packet, self.remote_addr)
        while True:
            try:
                self.sock.settimeout(TIMEOUT)
                packet, _ = self.sock.recvfrom(BUFFER_SIZE)
                parsed = self.parse_packet(packet)
                if parsed is None:
                    continue
                _, ack, flags, _ = parsed
                if flags & ACK:
                    print("[INFO] Connection closed.")
                    break
            except socket.timeout:
                self.sock.sendto(fin_packet, self.remote_addr)

    def send(self, data):
        packet = self.make_packet(self.seq, 0, 0, data)
        while True:
            if random.random() > self.loss_prob:
                self.sock.sendto(packet, self.remote_addr)
            try:
                self.sock.settimeout(TIMEOUT)
                response, _ = self.sock.recvfrom(BUFFER_SIZE)
                parsed = self.parse_packet(response)
                if parsed is None:
                    continue
                r_seq, r_ack, r_flags, _ = parsed
                if r_flags & ACK and r_ack == self.seq:
                    self.seq = 1 - self.seq
                    return
            except socket.timeout:
                continue

    def recv(self):
        while True:
            try:
                self.sock.settimeout(TIMEOUT)
                packet, addr = self.sock.recvfrom(BUFFER_SIZE)

                if random.random() < self.corrupt_prob:
                    corrupted = bytearray(packet)
                    index = random.randint(0, len(corrupted) - 1)
                    corrupted[index] ^= 0xFF
                    packet = bytes(corrupted)

                parsed = self.parse_packet(packet)
                if parsed is None:
                    continue
                seq, ack, flags, payload = parsed

                try:
                    payload.decode()
                except UnicodeDecodeError:
                    continue

                

                if flags & FIN:
                    ack_packet = self.make_packet(0, seq, ACK, b"")
                    self.sock.sendto(ack_packet, addr)
                    print("[INFO] FIN received, connection closing.")
                    return b""

                if seq != self.ack:
                    continue

                ack_packet = self.make_packet(0, seq, ACK, b"")
                self.sock.sendto(ack_packet, addr)
                self.ack = 1 - self.ack
                self.remote_addr = addr
                return payload
            except socket.timeout:
                continue

class HTTPServer:
    def __init__(self, host='localhost', port=8080, loss_prob=0.1, corrupt_prob=0.1):
        self.server = ReliableUDP((host, port), loss_prob=loss_prob, corrupt_prob=corrupt_prob)
        self.server.handshake(is_server=True)

    def serve_forever(self):
        print("HTTP Server started.")
        while True:
            try:
                data = self.server.recv()
                if data == b"":
                    break
                try:
                    request = data.decode()
                except UnicodeDecodeError:
                    print("Received undecodable packet, likely corrupted.")
                    continue

                lines = request.split('\r\n')
                if not lines:
                    continue
                try:
                    method_line = lines[0].split()
                    method = method_line[0]
                    path = method_line[1] if len(method_line) > 1 else "/"
                except Exception as e:
                    print("Failed to parse method line:", e)
                    continue

                headers = {}
                for line in lines[1:]:
                    if line == "":
                        break
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        headers[parts[0].strip()] = parts[1].strip()

                if method == 'GET':
                    content = f"<html><body><h1>You requested {path}</h1></body></html>"
                    status = "HTTP/1.0 200 OK"
                elif method == 'POST':
                    body_index = request.find("\r\n\r\n")
                    body = request[body_index + 4:] if body_index != -1 else ""
                    print(f"[POST BODY] {body}")
                    content = f"<html><body><h1>POST Received: {body}</h1></body></html>"
                    status = "HTTP/1.0 200 OK"
                else:
                    content = "<html><body><h1>404 Not Found</h1></body></html>"
                    status = "HTTP/1.0 404 Not Found"

                response = (
                    f"{status}\r\n"
                    f"Content-Length: {len(content)}\r\n"
                    f"Content-Type: text/html\r\n"
                    f"Server: ReliableUDPServer/1.0\r\n\r\n"
                    f"{content}"
                )
                self.server.send(response.encode())
            except Exception as e:
                print("Server error:", e)
                continue

class HTTPClient:
    def __init__(self, server_addr, loss_prob=0.1, corrupt_prob=0.1):
        self.client = ReliableUDP(('0.0.0.0', 0), server_addr, loss_prob=loss_prob, corrupt_prob=corrupt_prob)
        self.client.handshake(is_server=False)

    def get(self, path):
        request = (
            f"GET {path} HTTP/1.0\r\n"
            f"Host: localhost\r\n"
            f"User-Agent: ReliableUDPClient/1.0\r\n"
            f"Connection: close\r\n\r\n"
        )
        self.client.send(request.encode())
        for _ in range(5):
            try:
                response = self.client.recv()
                print("Received:\n", response.decode())
                break
            except Exception as e:
                print("GET timeout or error, retrying...", e)
                time.sleep(1)

    def post(self, path, body=""):
        request = (
            f"POST {path} HTTP/1.0\r\n"
            f"Host: localhost\r\n"
            f"User-Agent: ReliableUDPClient/1.0\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"Content-Type: text/plain\r\n"
            f"Connection: close\r\n\r\n"
            f"{body}"
        )
        self.client.send(request.encode())
        for _ in range(5):
            try:
                response = self.client.recv()
                print("Received:\n", response.decode())
                break
            except Exception as e:
                print("POST timeout or error, retrying...", e)
                time.sleep(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("role", choices=["server", "client"], help="Run as server or client")
    parser.add_argument("--loss", type=float, default=0.1, help="Packet loss probability")
    parser.add_argument("--corrupt", type=float, default=0.1, help="Packet corruption probability")
    args = parser.parse_args()

    if args.role == "server":
        server = HTTPServer(loss_prob=args.loss, corrupt_prob=args.corrupt)
        server.serve_forever()
    elif args.role == "client":
        client = HTTPClient(('localhost', 8080), loss_prob=args.loss, corrupt_prob=args.corrupt)
        client.get("/index.html")
        client.post("/submit", "name=Project")
        client.client.close()
