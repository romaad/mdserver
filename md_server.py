import http.server
import socketserver
import os
import urllib.parse
import string
import logging
import html

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("md_server.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("md_server")

PORT = 8090
WEB_ROOT = "/home/ramadan/.openclaw/workspace"
TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# Load templates
def load_template(name):
    path = os.path.join(TEMPLATE_DIR, name)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return string.Template(f.read())
    return string.Template(f"<h1>Template {name} not found</h1>")

LISTING_TEMPLATE = load_template("listing.html")
VIEWER_TEMPLATE = load_template("viewer.html")
CODE_TEMPLATE = load_template("code.html")
CSV_TEMPLATE = load_template("csv.html")

class MarkdownViewerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        logger.info(f"GET {self.path} - {self.client_address[0]}")
        
        # Decode the URL path
        path = urllib.parse.unquote(self.path)
        
        # Handle static files explicitly
        if path.startswith("/static/"):
            self.serve_static(path)
            return
        
        # Security check
        if ".." in path:
            logger.warning(f"Blocked directory traversal: {path}")
            self.send_error(403, "Forbidden")
            return

        # Map to local file path
        # Remove query parameters for file lookup
        clean_path = path.split('?')[0]
        full_path = os.path.join(WEB_ROOT, clean_path.lstrip("/"))
        
        try:
            if os.path.isdir(full_path):
                self.list_directory_custom(full_path, clean_path)
            elif os.path.isfile(full_path):
                self.serve_file(full_path, path) # Pass original path for query params
            else:
                logger.warning(f"Not found: {full_path}")
                self.send_error(404, "File not found")
        except Exception as e:
            logger.exception(f"Error serving {path}: {e}")
            self.send_error(500, f"Internal Server Error: {e}")

    def serve_static(self, path):
        static_file = path.replace("/static/", "", 1).split('?')[0]
        static_path = os.path.join(STATIC_DIR, static_file)
        if os.path.exists(static_path) and os.path.isfile(static_path):
            self.send_response(200)
            if static_path.endswith(".css"):
                self.send_header("Content-type", "text/css; charset=utf-8")
            self.end_headers()
            with open(static_path, "rb") as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404, "Static file not found")

    def list_directory_custom(self, full_path, url_path):
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()
        
        items = []
        if url_path != "/":
            parent = os.path.dirname(url_path.rstrip("/"))
            if parent == "": parent = "/"
            items.append(f'<li><a href="{parent}"><span class="icon">⬆️</span> ..</a></li>')
            
        try:
            for item in sorted(os.listdir(full_path)):
                if item.startswith("."): continue
                
                abs_item_path = os.path.join(full_path, item)
                is_dir = os.path.isdir(abs_item_path)
                
                display_name = item + ("/" if is_dir else "")
                icon = "📂" if is_dir else "📄"
                
                # Link is relative to current path
                link_target = os.path.join(url_path, item).replace("\\", "/")
                if is_dir: link_target += "/"
                
                link_href = urllib.parse.quote(link_target)
                
                items.append(f'<li><a href="{link_href}"><span class="icon">{icon}</span> {display_name}</a></li>')
        except Exception as e:
            items.append(f"<li>Error listing directory: {e}</li>")
        
        self.wfile.write(LISTING_TEMPLATE.safe_substitute(path=url_path, items="\n".join(items)).encode("utf-8"))

    def serve_file(self, full_path, url_path):
        # Check if raw requested
        is_raw = "raw=true" in url_path
        _, ext = os.path.splitext(full_path)
        ext = ext.lower()

        # Markdown Viewer
        if ext in ['.md', '.markdown'] and not is_raw:
            self.render_viewer(full_path)
            return

        # CSV Viewer
        if ext == '.csv' and not is_raw:
            self.render_csv(full_path)
            return

        # Code Viewer
        code_exts = {
            ".py": "python", ".js": "javascript", ".css": "css", ".html": "xml", 
            ".json": "json", ".yml": "yaml", ".yaml": "yaml", ".sh": "bash", 
            ".conf": "bash", ".xml": "xml", ".c": "c", ".cpp": "cpp", ".h": "c",
            ".java": "java", ".go": "go", ".rs": "rust", ".ts": "typescript",
            ".tsx": "typescript", ".jsx": "javascript", ".sql": "sql", ".ini": "ini",
            ".log": "plaintext", ".txt": "plaintext", ".csv": "plaintext",
            ".tsv": "plaintext", ".env": "plaintext", ".gitignore": "plaintext"
        }
        
        is_text_file = False
        lang = "plaintext"
        
        if ext in code_exts:
            is_text_file = True
            lang = code_exts[ext]
        else:
            import mimetypes
            mime, _ = mimetypes.guess_type(full_path)
            if mime and mime.startswith('text/'):
                is_text_file = True
            else:
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        f.read(1024)
                    is_text_file = True
                except Exception:
                    is_text_file = False

        if is_text_file and not is_raw:
            self.render_code(full_path, lang)
            return

        # Default raw serve
        # Hack to serve from correct root since SimpleHTTPRequestHandler uses CWD
        current_dir = os.getcwd()
        try:
            os.chdir(WEB_ROOT)
            # Create a new handler instance or trick the super method?
            # It's easier to just read and send manually for a simple server
            self.send_response(200)
            # Let SimpleHTTPRequestHandler guess the type if we used it, but here:
            import mimetypes
            ctype, _ = mimetypes.guess_type(full_path)
            if ctype:
                self.send_header("Content-type", ctype)
            self.end_headers()
            with open(full_path, "rb") as f:
                self.wfile.write(f.read())
        except Exception as e:
             logger.error(f"Error serving raw file {full_path}: {e}")
             self.send_error(500, str(e))
        finally:
            os.chdir(current_dir)

    def render_viewer(self, full_path):
        if os.path.exists(full_path):
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            
            safe_content = html.escape(content)
            
            self.wfile.write(VIEWER_TEMPLATE.safe_substitute(
                filename=os.path.basename(full_path),
                raw_content=safe_content
            ).encode("utf-8"))

    def render_csv(self, full_path):
        if os.path.exists(full_path):
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            
            safe_content = html.escape(content)
            
            self.wfile.write(CSV_TEMPLATE.safe_substitute(
                filename=os.path.basename(full_path),
                raw_content=safe_content
            ).encode("utf-8"))

    def render_code(self, full_path, lang):
         if os.path.exists(full_path):
            self.send_response(200)
            self.send_header("Content-type", "text/html; charset=utf-8")
            self.end_headers()
            
            with open(full_path, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
            
            safe_content = html.escape(content)
            
            self.wfile.write(CODE_TEMPLATE.safe_substitute(
                filename=os.path.basename(full_path),
                ext=lang,
                content=safe_content
            ).encode("utf-8"))

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    with ReusableTCPServer(("", PORT), MarkdownViewerHandler) as httpd:
        logger.info(f"Serving at http://localhost:{PORT}")
        print(f"Serving at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
