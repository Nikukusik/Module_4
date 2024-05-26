from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import mimetypes
import pathlib
import json
import socket
from datetime import datetime
from threading import Thread

SOCKET_HOST = 'localhost'
SOCKET_PORT = 5000

class HttpHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        data = self.rfile.read(int(self.headers['Content-Length']))
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socket.sendto(data, (SOCKET_HOST, SOCKET_PORT))
        client_socket.close()
        self.send_response(302)
        self.send_header('Location', '/')
        self.end_headers()

    def do_GET(self):
        pr_url = urllib.parse.urlparse(self.path)
        match pr_url.path:
            case '/':
                self.send_html_file("index.html")
            case '/message':
                self.send_html_file("message.html")
            case _:
                if pathlib.Path().joinpath(pr_url.path[1:]).exists():
                    self.send_static()
                else:
                    self.send_html_file('error.html', 404)


    
    def send_html_file(self, filename, status = 200):
        self.send_response(status)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as fd:
            self.wfile.write(fd.read())

    def send_static(self):
        self.send_response(200)
        mt = mimetypes.guess_type(self.path)
        if mt:
            self.send_header("Content-type", mt[0])
        else:
            self.send_header("Content-type", 'text/plain')
        self.end_headers()
        with open(f'.{self.path}', 'rb') as file:
            self.wfile.write(file.read())


def save_data_json(data):
        data_parse = urllib.parse.unquote_plus(data.decode())
        current_dt = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
        new_data = {current_dt: {key: value for key, value in [el.split('=') for el in data_parse.split('&')]}}
        file_path = 'storage/data.json'
        try:
            with open(file_path, "r", encoding = "utf-8") as fh:
                existing_data = json.load(fh)        
        except FileNotFoundError:
            existing_data = {}
        
        existing_data.update(new_data)

        with open(file_path, "w", encoding = "utf-8") as fh:
            json.dump(existing_data, fh, ensure_ascii = False, indent = 2)

def run_socket_server(host, port):
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.bind((host, port))
        try:
            while True:
                msg, adrress = server_socket.recvfrom(1024)
                save_data_json(msg)
        except KeyboardInterrupt:
            pass
        finally:
            server_socket.close()

def run(server_class = HTTPServer, handler_class = HttpHandler):
    server_address = ('', 3000)
    http = server_class(server_address, handler_class)
    try:
        http.serve_forever()
    except KeyboardInterrupt:
        http.server_close()


if __name__ == '__main__':
    server_http = Thread(target=run)
    server_http .start()

    server_socker = Thread(target=run_socket_server, args=(SOCKET_HOST, SOCKET_PORT))
    server_socker .start()

