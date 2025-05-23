import socket
import threading
import time
import hashlib
import random

BUFFER_SIZE = 4096
TIMEOUT = 2
WINDOW_SIZE = 4
MAX_SEQ = 256

ACK = 0x02

class ReliableUDP_GBN:
    def __init__(self, local_addr, remote_addr=None, loss_prob=0.1, corrupt_prob=0.1):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(local_addr)
        self.remote_addr = remote_addr
        self.loss_prob = loss_prob
        self.corrupt_prob = corrupt_prob
        self.lock = threading.Lock()
        self.base = 0
        self.next_seq = 0
        self.buffer = {}
        self.ack_event = threading.Event()
        self.recv_thread = threading.Thread(target=self._recv_acks)
        self.recv_thread.daemon = True
        self.recv_thread.start()

    def compute_checksum(self, data):
        return hashlib.md5(data).hexdigest()

    def make_packet(self, seq, ack, flags, payload):
        header = f"{seq}|{ack}|{flags}|".encode()
        checksum = self.compute_checksum(header + payload).encode()
        return checksum + b"|" + header + payload

    def parse_packet(self, packet):
        parts = packet.split(b"|", 4)
        if len(parts) < 5:
            return None, None, None, None, None
        checksum, seq, ack, flags, payload = parts
        header_payload = b"|".join(parts[1:])
        if checksum.decode() != self.compute_checksum(header_payload):
            return None, None, None, None, None
        return int(seq), int(ack), int(flags), payload

    def _recv_acks(self):
        while True:
            try:
                self.sock.settimeout(TIMEOUT)
                packet, _ = self.sock.recvfrom(BUFFER_SIZE)
                seq, ack, flags, _ = self.parse_packet(packet)
                if flags & ACK:
                    with self.lock:
                        if self._in_window(self.base, ack):
                            self.base = (ack + 1) % MAX_SEQ
                            self.ack_event.set()
            except socket.timeout:
                continue

    def _in_window(self, base, seq):
        return (base <= seq < base + WINDOW_SIZE) or (base + WINDOW_SIZE >= MAX_SEQ and seq < (base + WINDOW_SIZE) % MAX_SEQ)

    def send(self, data_list):
        self.base = 0
        self.next_seq = 0
        self.buffer = {}

        while self.base < len(data_list):
            with self.lock:
                while self._in_window(self.base, self.next_seq) and self.next_seq < len(data_list):
                    payload = data_list[self.next_seq]
                    packet = self.make_packet(self.next_seq % MAX_SEQ, 0, 0, payload)
                    self.buffer[self.next_seq % MAX_SEQ] = (packet, time.time())
                    if random.random() > self.loss_prob:
                        self.sock.sendto(packet, self.remote_addr)
                    self.next_seq += 1

            self.ack_event.wait(timeout=TIMEOUT)
            self.ack_event.clear()

            with self.lock:
                now = time.time()
                for seq in list(self.buffer):
                    pkt, ts = self.buffer[seq]
                    if now - ts > TIMEOUT:
                        if random.random() > self.loss_prob:
                            self.sock.sendto(pkt, self.remote_addr)
                        self.buffer[seq] = (pkt, time.time())

    def recv(self):
        expected_seq = 0
        while True:
            try:
                packet, addr = self.sock.recvfrom(BUFFER_SIZE)
                self.remote_addr = addr
                seq, ack, flags, payload = self.parse_packet(packet)
                if seq == expected_seq:
                    ack_packet = self.make_packet(0, seq, ACK, b"")
                    self.sock.sendto(ack_packet, addr)
                    expected_seq = (expected_seq + 1) % MAX_SEQ
                    return payload
                else:
                    # Always ACK last in-order packet
                    ack_packet = self.make_packet(0, (expected_seq - 1) % MAX_SEQ, ACK, b"")
                    self.sock.sendto(ack_packet, addr)
            except socket.timeout:
                continue