
from reliable_udp_sliding_window import ReliableUDP_GBN
import argparse

class HTTPServerGBN:
    def __init__(self, host='localhost', port=8080, loss_prob=0.1, corrupt_prob=0.1):
        self.server = ReliableUDP_GBN((host, port), loss_prob=loss_prob, corrupt_prob=corrupt_prob)

    def serve_forever(self):
        print("HTTP Server (GBN) started.")
        while True:
            try:
                data = self.server.recv()
                request = data.decode()
                lines = request.split('\r\n')
                if not lines:
                    continue
                method_line = lines[0].split()
                if len(method_line) < 2:
                    continue
                method, path = method_line[:2]
                if method == 'GET':
                    content = f"<html><body><h1>You requested {path}</h1></body></html>"
                    status = "HTTP/1.0 200 OK"
                elif method == 'POST':
                    content = f"<html><body><h1>POST Received to {path}</h1></body></html>"
                    status = "HTTP/1.0 200 OK"
                else:
                    content = "<html><body><h1>404 Not Found</h1></body></html>"
                    status = "HTTP/1.0 404 Not Found"
                response = f"{status}\r\nContent-Length: {len(content)}\r\nContent-Type: text/html\r\n\r\n{content}"
                self.server.send([response.encode()])
            except TimeoutError:
                continue

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--loss", type=float, default=0.1)
    parser.add_argument("--corrupt", type=float, default=0.1)
    args = parser.parse_args()
    server = HTTPServerGBN(loss_prob=args.loss, corrupt_prob=args.corrupt)
    server.serve_forever()
