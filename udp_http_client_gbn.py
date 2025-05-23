
from reliable_udp_sliding_window import ReliableUDP_GBN
import argparse

class HTTPClientGBN:
    def __init__(self, server_addr, loss_prob=0.1, corrupt_prob=0.1):
        self.client = ReliableUDP_GBN(('0.0.0.0', 0), server_addr, loss_prob=loss_prob, corrupt_prob=corrupt_prob)

    def get(self, path):
        request = f"GET {path} HTTP/1.0\r\nHost: localhost\r\n\r\n"
        self.client.send([request.encode()])
        response = self.client.recv()
        print("Received:\n", response.decode())

    def post(self, path, body=""):
        request = (
            f"POST {path} HTTP/1.0\r\n"
            f"Host: localhost\r\n"
            f"Content-Length: {len(body)}\r\n"
            f"Content-Type: text/plain\r\n\r\n{body}"
        )
        self.client.send([request.encode()])
        response = self.client.recv()
        print("Received:\n", response.decode())

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--loss", type=float, default=0.1)
    parser.add_argument("--corrupt", type=float, default=0.1)
    args = parser.parse_args()
    client = HTTPClientGBN(('localhost', 8080), loss_prob=args.loss, corrupt_prob=args.corrupt)
    client.get("/index.html")
    client.post("/submit", "name=Project")
