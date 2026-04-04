import http.server
import socketserver
import json

PORT = 5005

class MockPerson2API(http.server.SimpleHTTPRequestHandler):
    def send_json(self, status_code, payload):
        self.send_response(status_code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(payload).encode())

    def do_GET(self):
        # 1. Health check / count endpoint
        if self.path == "/api/cad/entities/count":
            self.send_json(200, {
                "status": "Success",
                "data": {"TotalEntities": 3}
            })
            
        # 2. Main entity listing
        elif self.path == "/api/cad/entities/list":
            mock_data = [
                { "id": "uuid-1234", "type": "Line" },
                { "id": "uuid-5678", "type": "Circle" },
                { "id": "uuid-9012", "type": "Mesh" }
            ]
            self.send_json(200, {
                "status": "Success",
                "data": mock_data
            })
            
        # 3. Requesting single entity properties
        elif self.path.startswith("/api/cad/entities/"):
            entity_id = self.path.split("/")[-1]
            mock_props = {
                "type": "Line",
                "layer": "0",
                "color": "RGB(255,0,0)",
                "visible": True,
                "length": 45.2
            }
            self.send_json(200, {
                "status": "Success",
                "data": mock_props
            })
            
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        # 1. Load model endpoint
        if self.path == "/api/cad/load":
            self.send_json(200, {
                "status": "success",
                "message": "Model loaded successfully (MOCKED)."
            })
        else:
            self.send_response(404)
            self.end_headers()

# Allow fast restarts without "Address already in use"
socketserver.TCPServer.allow_reuse_address = True

print(f"🚀 PHASE 2 MOCK BACKEND SERVER IS RUNNING ON PORT {PORT}")
print("Leave this terminal open to test Flow A (Success)!")
print("Close this terminal (Ctrl+C) to test Flow B (Failure)!")

with socketserver.TCPServer(("0.0.0.0", PORT), MockPerson2API) as httpd:
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nMock server shutting down...")
