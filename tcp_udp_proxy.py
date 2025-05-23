import socket
from reliable_udp_http import ReliableUDP

def handle_browser_connection(tcp_conn, addr):
    client_data = tcp_conn.recv(4096)
    udp = ReliableUDP(('0.0.0.0', 0), ('localhost', 8080))
    udp.send(client_data)
    response = udp.recv()
    tcp_conn.sendall(response)
    tcp_conn.close()

tcp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
tcp_socket.bind(('localhost', 9090))
tcp_socket.listen(5)
print("Proxy listening on TCP port 9090")

while True:
    conn, addr = tcp_socket.accept()
    handle_browser_connection(conn, addr)
