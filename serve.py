#!/usr/bin/env python3
"""
Simple HTTP server to serve the Places AI frontend
"""
import http.server
import socketserver
import os
from pathlib import Path

PORT = 3000
DIRECTORY = Path(__file__).parent

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

if __name__ == "__main__":
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"""
🚀 Places AI Frontend Server
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📱 Frontend URL: http://localhost:{PORT}
🎯 API URL: http://localhost:8000/v1

📝 Instructions:
1. Make sure your FastAPI server is running on port 8000
2. Open http://localhost:{PORT} in your browser
3. Start discovering amazing places with AI!

Press Ctrl+C to stop the server
            """)
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n👋 Server stopped. See you later!")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {PORT} is already in use. Try stopping other servers or use a different port.")
        else:
            print(f"❌ Error starting server: {e}") 