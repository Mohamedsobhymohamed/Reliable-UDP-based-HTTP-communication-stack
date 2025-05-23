# Reliable UDP HTTP Communication

This project implements a **Reliable UDP-based HTTP communication stack**, simulating TCP-like reliability features (stop-and-wait and Go-Back-N) over unreliable UDP. It includes a client-server architecture, HTTP request handling, and a TCP-to-UDP proxy for testing with web browsers.

---

## 🗂 Project Structure

├── reliable_udp_http.py # Reliable UDP with stop-and-wait
├── reliable_udp_sliding_window.py # Reliable UDP with Go-Back-N (GBN)
├── udp_http_server_gbn.py # HTTP server using GBN protocol
├── udp_http_client_gbn.py # HTTP client using GBN protocol
├── tcp_udp_proxy.py # Proxy to allow browser to test UDP HTTP server
├── test_runner.py # Automates testing of client-server with loss/corruption
├── tcp_over_udp_http_capture.pcapng # Wireshark capture file of a TCP-over-UDP session
└── README.md
---

## 🧠 Overview

UDP is connectionless and does not guarantee delivery or ordering. This project builds reliable HTTP communication on top of UDP using two techniques:
- **Stop-and-Wait**: Used in `reliable_udp_http.py`
- **Go-Back-N (GBN)**: Used in `reliable_udp_sliding_window.py`

Each supports artificial **packet loss** and **corruption**, simulating real network behavior.

---

## 🚀 How to Run

### 1. Install Python 3

Ensure you have Python 3 installed. Install required modules (if any):

pip install -r requirements.txt
# Currently, no external dependencies are used
2. Run Stop-and-Wait Simulation
# Run server
python reliable_udp_http.py server --loss 0.1 --corrupt 0.1

# In another terminal, run client
python reliable_udp_http.py client --loss 0.1 --corrupt 0.1
3. Run GBN Simulation
# Start GBN server
python udp_http_server_gbn.py --loss 0.1 --corrupt 0.1

# In another terminal, run GBN client
python udp_http_client_gbn.py --loss 0.1 --corrupt 0.1
4. Test with Web Browser via Proxy
# Start TCP to UDP proxy
python tcp_udp_proxy.py
Then visit http://localhost:9090/index.html in your browser. This redirects browser requests to the UDP HTTP server.

## 🧪 Test Automation
Use the test_runner.py to automate and evaluate the server-client interaction under packet loss and corruption.

python test_runner.py
## ⚙️ Features
Simulates reliable data transfer with:

Checksums

Acknowledgments

Retransmissions

Sliding window (GBN)

Supports both GET and POST HTTP requests

Emulates real-world network faults

Proxy server bridges TCP and UDP for browser testing

Wireshark-compatible .pcapng capture for packet analysis

## 🧰 Configurable Parameters
Parameter	Description	Default
--loss	Packet loss probability (0.0–1.0)	0.1
--corrupt	Packet corruption probability	0.1

## 📡 Packet Capture
Use tcp_over_udp_http_capture.pcapng to analyze communication in tools like Wireshark.

## 📄 License
This project is provided for educational purposes and is released under the MIT License.

## 🙌 Acknowledgments
Inspired by networking labs and reliable transport protocol simulations. Implements core networking concepts like:

Stop-and-Wait ARQ

Go-Back-N ARQ

TCP-like handshaking and teardown
