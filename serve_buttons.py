#!/usr/bin/env python3
"""
Simple local web server to serve button images for testing
Run this to serve button images locally
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

# Change to the static directory
os.chdir('static')

# Start the server
PORT = 8080
server = HTTPServer(('localhost', PORT), SimpleHTTPRequestHandler)
print(f"Button server running at http://localhost:{PORT}")
print("Serving button images from static/ directory")
print("Press Ctrl+C to stop")

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nServer stopped")
    server.shutdown()
