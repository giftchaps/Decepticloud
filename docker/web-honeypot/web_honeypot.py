#!/usr/bin/env python3
from flask import Flask, request, render_template_string
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - Web Honeypot - %(message)s')

app = Flask(__name__)

LOGIN_PAGE = '''
<!DOCTYPE html>
<html>
<head><title>Admin Login</title></head>
<body>
<h2>System Administrator Login</h2>
<form method="post" action="/login">
    <p>Username: <input type="text" name="username"></p>
    <p>Password: <input type="password" name="password"></p>
    <p><input type="submit" value="Login"></p>
</form>
</body>
</html>
'''

@app.route('/')
def index():
    logging.info(f"Web access from {request.remote_addr}")
    return LOGIN_PAGE

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username', '')
    password = request.form.get('password', '')
    logging.info(f"Login attempt from {request.remote_addr}: {username}:{password}")
    return "Invalid credentials", 401

@app.route('/<path:path>')
def catch_all(path):
    logging.info(f"Path access from {request.remote_addr}: /{path}")
    return "Not Found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=False)