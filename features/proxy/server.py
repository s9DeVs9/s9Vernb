
import socket
import select
import base64
import threading


class RotationProxyServer:

    def __init__(self, proxies, port=8888):
        self.proxies = proxies
        self.port = port
        self._server_sock = None
        self._thread = None
        self._running = False
        self._proxy_idx = 0
        self._stats = {"requests": 0, "errors": 0}
        self._lock = threading.Lock()

    def start(self):
        self._server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._server_sock.settimeout(1.0)
        self._server_sock.bind(("127.0.0.1", self.port))
        self._server_sock.listen(100)
        self._running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._server_sock:
            try:
                self._server_sock.close()
            except Exception:
                pass

    def _get_next_proxy(self):
        p = self.proxies[self._proxy_idx % len(self.proxies)]
        self._proxy_idx = (self._proxy_idx + 1) % len(self.proxies)
        return p

    def _run(self):
        while self._running:
            try:
                client_sock, addr = self._server_sock.accept()
                t = threading.Thread(target=self._handle_client,
                                     args=(client_sock,), daemon=True)
                t.start()
            except socket.timeout:
                continue
            except OSError:
                break

    def _handle_client(self, client_sock):
        try:
            data = client_sock.recv(4096)
            if not data:
                client_sock.close()
                return

            first_line = data.split(b"\r\n")[0].decode("utf-8", errors="ignore")
            method = first_line.split(" ")[0] if first_line else ""

            if method == "CONNECT":
                self._handle_connect(client_sock, data)
            else:
                self._handle_http(client_sock, data)

            with self._lock:
                self._stats["requests"] += 1
        except Exception:
            with self._lock:
                self._stats["errors"] += 1
        finally:
            try:
                client_sock.close()
            except Exception:
                pass

    def _handle_connect(self, client_sock, data):
        parts = data.split(b"\r\n")[0].split(b" ")
        target = parts[1].decode("utf-8", errors="ignore")
        if ":" in target:
            host, port = target.rsplit(":", 1)
            port = int(port)
        else:
            host, port = target, 443

        proxy = self._get_next_proxy()
        try:
            remote = socket.create_connection(
                (proxy["host"], proxy["port"]), timeout=10
            )
            req = f"CONNECT {host}:{port} HTTP/1.1\r\nHost: {host}:{port}\r\n"
            if proxy.get("user"):
                cred = base64.b64encode(
                    f"{proxy['user']}:{proxy['pass']}".encode()
                ).decode()
                req += f"Proxy-Authorization: Basic {cred}\r\n"
            req += "\r\n"
            remote.sendall(req.encode())

            resp = remote.recv(4096)
            if b"200" in resp.split(b"\r\n")[0]:
                client_sock.sendall(
                    b"HTTP/1.1 200 Connection Established\r\n\r\n"
                )
                self._tunnel(client_sock, remote)
            else:
                client_sock.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            remote.close()
        except Exception:
            try:
                client_sock.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            except Exception:
                pass

    def _handle_http(self, client_sock, data):
        first_line = data.split(b"\r\n")[0].decode("utf-8", errors="ignore")
        parts = first_line.split(" ")
        if len(parts) < 3:
            client_sock.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            return

        url = parts[1]
        if not url.startswith("http://"):
            client_sock.sendall(b"HTTP/1.1 400 Bad Request\r\n\r\n")
            return

        url_path = url[7:]
        if "/" in url_path:
            host_port, path = url_path.split("/", 1)
            path = "/" + path
        else:
            host_port, path = url_path, "/"

        if ":" in host_port:
            host, port = host_port.rsplit(":", 1)
            port = int(port)
        else:
            host, port = host_port, 80

        proxy = self._get_next_proxy()
        try:
            remote = socket.create_connection(
                (proxy["host"], proxy["port"]), timeout=10
            )
            new_request = data.replace(
                f"http://{host_port}{path}".encode(), path.encode(), 1
            )
            if proxy.get("user"):
                cred = base64.b64encode(
                    f"{proxy['user']}:{proxy['pass']}".encode()
                ).decode()
                new_request = new_request.replace(
                    b"\r\n\r\n",
                    f"\r\nProxy-Authorization: Basic {cred}\r\n\r\n".encode(),
                    1,
                )
            remote.sendall(new_request)
            self._tunnel(client_sock, remote)
            remote.close()
        except Exception:
            try:
                client_sock.sendall(b"HTTP/1.1 502 Bad Gateway\r\n\r\n")
            except Exception:
                pass

    def _tunnel(self, sock1, sock2):
        sockets = [sock1, sock2]
        while self._running:
            try:
                readable, _, exceptional = select.select(sockets, [], sockets, 30)
                if exceptional or not readable:
                    break
                for s in readable:
                    other = sock2 if s is sock1 else sock1
                    data = s.recv(8192)
                    if not data:
                        return
                    other.sendall(data)
            except Exception:
                break

    @property
    def stats(self):
        with self._lock:
            return dict(self._stats)
