import os
import sys
import json
import subprocess
import urllib.parse
import tempfile
from http.server import HTTPServer, BaseHTTPRequestHandler

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
from libcompiler.i18n import t

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        url_path = urllib.parse.unquote(self.path)
        relative_path = "index.html" if url_path == "/" else url_path.lstrip("/").replace("/", os.sep)
        
        # If it's a frontend asset, serve from BASE_DIR. Otherwise, serve from PROJECT_ROOT.
        if relative_path in ["index.html", "rsc-highlighter.js"]:
            file_path = os.path.join(BASE_DIR, relative_path)
        else:
            file_path = os.path.join(PROJECT_ROOT, relative_path)

        if os.path.exists(file_path) and os.path.isfile(file_path):
            try:
                with open(file_path, "rb") as f:
                    content = f.read()

                if relative_path.endswith(".html"): content_type = "text/html"
                elif relative_path.endswith(".js"): content_type = "application/javascript"
                elif relative_path.endswith(".css"): content_type = "text/css"
                elif relative_path.endswith(".ico"): content_type = "image/x-icon"
                elif relative_path.endswith(".json"): content_type = "application/json"
                elif relative_path.endswith(".txt"): content_type = "text/plain; charset=utf-8"
                else: content_type = "application/octet-stream"

                self.send_response(200)
                self.send_header("Content-Type", content_type)
                self.end_headers()
                self.wfile.write(content)
            except Exception as e:
                self.send_error(500, f"Error reading file: {str(e)}")
        else:
            self.send_error(404, f"File not found: {relative_path}")

    def do_POST(self):
        if self.path == '/compile':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                
                env = os.environ.copy()
                env["PYTHONIOENCODING"] = "utf-8"
                env["PYTHONUNBUFFERED"] = "1"
                for k, v in data.get('files', {}).items():
                    env[f"RAC_MOCK_FILE_{k.replace('.','_').upper()}"] = v

                # Write code to a temp file
                with tempfile.NamedTemporaryFile(suffix=".rsc", delete=False, dir=PROJECT_ROOT) as tmp:
                    tmp.write(data.get('code', '').encode('utf-8'))
                    tmp_name = tmp.name

                cmd = [sys.executable, os.path.join(PROJECT_ROOT, "rac.py")]
                lang = data.get('lang', 'en_US')
                cmd.extend(["-l", lang])
                cmd.extend(["580vnx", os.path.basename(tmp_name)])
                res = subprocess.run(cmd, capture_output=True, text=True, cwd=PROJECT_ROOT, env=env, encoding='utf-8')
                
                # Cleanup temp file
                try:
                    os.remove(tmp_name)
                except Exception:
                    pass
                
                response = {
                    "output": res.stdout,
                    "notes": res.stderr or "",
                    "returncode": res.returncode,
                    "bytes_count": len(res.stdout.split()) if res.stdout else 0
                }
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response).encode())
                
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())

if __name__ == "__main__":
    server = HTTPServer(('127.0.0.1', 5000), SimpleHandler)
    print(t("web_ide_server_running", port=5000))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
        print(t("web_ide_server_stopped"))
