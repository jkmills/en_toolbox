#!/usr/bin/env python3
"""
Secure HTTP Server with API Proxy for Render Deployment
This serves the HTML file and proxies API requests using environment variables for security.
"""

import http.server
import socketserver
import urllib.request
import urllib.parse
import json
import os
import sys
from pathlib import Path

# Configuration
PORT = int(os.environ.get('PORT', 10000))  # Render uses PORT environment variable
HTML_FILE = "emergency-signin.html"

class APIProxyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/users":
            self.handle_api_request()
        elif self.path == "/" or self.path == "":
            # Redirect root to HTML file
            self.send_response(302)
            self.send_header('Location', f'/{HTML_FILE}')
            self.end_headers()
        else:
            # Serve static files
            super().do_GET()
    
    def handle_api_request(self):
        try:
            # Get token from environment variable (secure)
            token = os.environ.get('EMERGENCY_NETWORKING_TOKEN')
            if not token:
                print("ERROR: EMERGENCY_NETWORKING_TOKEN environment variable not set")
                self.send_error(500, "API token not configured")
                return
            
            print(f"Making API request to Emergency Networking...")
            
            # Make request to Emergency Networking API
            req = urllib.request.Request(
                'https://app.emergencynetworking.com/department-api/users',
                headers={
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json',
                    'User-Agent': 'Emergency-SignIn-Generator-Render/1.0'
                }
            )
            
            with urllib.request.urlopen(req) as response:
                data = response.read()
                
                print(f"API request successful, received {len(data)} bytes")
                
                # Send successful response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
                self.end_headers()
                self.wfile.write(data)
                
        except urllib.error.HTTPError as e:
            error_msg = f"API Error: {e.code} - {e.reason}"
            print(error_msg)
            self.send_error(e.code, error_msg)
        except Exception as e:
            error_msg = f"Proxy Error: {str(e)}"
            print(error_msg)
            self.send_error(500, error_msg)
    
    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        self.end_headers()

    def log_message(self, format, *args):
        # Custom logging for Render
        print(f"[{self.address_string()}] {format % args}")

def main():
    # Change to the directory containing this script
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check if HTML file exists
    if not Path(HTML_FILE).exists():
        print(f"Error: {HTML_FILE} not found in current directory")
        print(f"Current directory: {script_dir}")
        sys.exit(1)
    
    # Check if environment variable is set
    token = os.environ.get('EMERGENCY_NETWORKING_TOKEN')
    if not token:
        print("WARNING: EMERGENCY_NETWORKING_TOKEN environment variable not set")
        print("This will cause API requests to fail")
    else:
        print("✓ EMERGENCY_NETWORKING_TOKEN environment variable found")
    
    # Start the server
    print("Emergency Networking Sign-In Generator - Render Deployment")
    print("=" * 60)
    print(f"Serving at: http://0.0.0.0:{PORT}")
    print(f"HTML file: {HTML_FILE}")
    print(f"API Proxy: /api/users -> Emergency Networking API")
    print("Press Ctrl+C to stop server")
    print()
    
    # Start server
    try:
        with socketserver.TCPServer(("0.0.0.0", PORT), APIProxyHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()