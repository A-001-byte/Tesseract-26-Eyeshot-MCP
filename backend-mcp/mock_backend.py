import http.server
import socketserver
import json

PORT = 5005

class MockPerson2API(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/api/cad/list_entities":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            
            # The exact array Person 2 promised
            mock_data = [
                { "id": "uuid-1234", "type": "Line" },
                { "id": "uuid-5678", "type": "Circle" },
                { "id": "uuid-9012", "type": "Mesh" }
            ]
            self.wfile.write(json.dumps(mock_data).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == "/api/cad/load_model":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            
            # The exact success message Person 2 promised
            mock_data = {
                "message": "Model loaded successfully."
            }
            self.wfile.write(json.dumps(mock_data).encode())
        else:
            self.send_response(404)
            self.end_headers()

# Allow fast restarts without "Address already in use"
socketserver.TCPServer.allow_reuse_address = True

print(f"🚀 MOCK PERSON 2 API IS RUNNING ON PORT {PORT}")
print("Leave this terminal open to test Flow A (Success)!")
print("Close this terminal (Ctrl+C) to test Flow B (Failure)!")

with socketserver.TCPServer(("0.0.0.0", PORT), MockPerson2API) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nMock server shutting down...")
