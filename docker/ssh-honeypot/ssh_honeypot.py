#!/usr/bin/env python3
import socket
import threading
import paramiko
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - SSH Honeypot - %(message)s')

class SSHHoneypot(paramiko.ServerInterface):
    def check_auth_password(self, username, password):
        logging.info(f"Login attempt: {username}:{password}")
        return paramiko.AUTH_FAILED

    def check_channel_request(self, kind, chanid):
        return paramiko.OPEN_SUCCEEDED

def handle_connection(client_socket, addr):
    try:
        transport = paramiko.Transport(client_socket)
        transport.add_server_key(paramiko.RSAKey.generate(2048))
        server = SSHHoneypot()
        transport.set_server(server)
        transport.start_server()
        
        chan = transport.accept(20)
        if chan is None:
            transport.close()
            return
            
        chan.close()
        transport.close()
    except Exception as e:
        logging.error(f"Error handling connection from {addr}: {e}")

def main():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', 2222))
    server_socket.listen(100)
    
    logging.info("SSH Honeypot listening on port 2222")
    
    while True:
        client_socket, addr = server_socket.accept()
        logging.info(f"Connection from {addr}")
        thread = threading.Thread(target=handle_connection, args=(client_socket, addr))
        thread.daemon = True
        thread.start()

if __name__ == '__main__':
    main()