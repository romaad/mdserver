import http.server
import socketserver
import os
import urllib.parse
import string

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

class MarkdownViewerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Decode the URL path
        path = urllib.parse.unquote(self.path)
        
        # Handle static files explicitly (since they might not be in WEB_ROOT)
        if path.startswith("/static/"):
            static_file = path.replace("/static/", "", 1)
            static_path = os.path.join(STATIC_DIR, static_file)
            if os.path.exists(static_path) and os.path.isfile(static_path):
                self.send_response(200)
                if static_path.endswith(".css"):
                    self.send_header("Content-type", "text/css")
                self.end_headers()
                with open(static_path, "rb") as f:
                    self.wfile.write(f.read())
                return
        
        # Security check: prevent directory traversal
        if ".." in path:
            self.send_error(403, "Forbidden")
            return

        # Map to local file path
        full_path = os.path.join(WEB_ROOT, path.lstrip("/"))
        
        # Check if it's a directory
        if os.path.isdir(full_path):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            
            items = []
            if path != "/":
                items.append('<li><a href=".."><span class="icon">⬆️</span> ..</a></li>')
                
            for item in sorted(os.listdir(full_path)):
                if item.startswith("."): continue
                
                abs_item_path = os.path.join(full_path, item)
                is_dir = os.path.isdir(abs_item_path)
                
                display_name = item + ("/" if is_dir else "")
                icon = "📂" if is_dir else "📄"
                
                # Link is just the item name, relative to current page
                link_href = urllib.parse.quote(display_name)
                
                items.append(f'<li><a href="{link_href}"><span class="icon">{icon}</span> {display_name}</a></li>')
            
            self.wfile.write(LISTING_TEMPLATE.substitute(path=path, items="\n".join(items)).encode("utf-8"))
            return

        # Check if it's a markdown file and user didn't ask for raw
        if full_path.endswith(".md") and "raw=true" not in self.path:
            if os.path.exists(full_path):
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                import html
                safe_content = html.escape(content)
                
                self.wfile.write(VIEWER_TEMPLATE.substitute(
                    filename=os.path.basename(full_path),
                    raw_content=safe_content
                ).encode("utf-8"))
                return

        # Check if it's a code file and user didn't ask for raw
        code_exts = {
            ".py": "python", ".js": "javascript", ".css": "css", ".html": "xml", 
            ".json": "json", ".yml": "yaml", ".yaml": "yaml", ".sh": "bash", 
            ".conf": "bash", ".xml": "xml", ".c": "c", ".cpp": "cpp", ".h": "c",
            ".java": "java", ".go": "go", ".rs": "rust", ".ts": "typescript",
            ".tsx": "typescript", ".jsx": "javascript", ".sql": "sql", ".ini": "ini",
            ".md": "markdown"
        }
        _, ext = os.path.splitext(full_path)
        if ext in code_exts and "raw=true" not in self.path:
             if os.path.exists(full_path):
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                import html
                safe_content = html.escape(content)
                
                self.wfile.write(CODE_TEMPLATE.substitute(
                    filename=os.path.basename(full_path),
                    ext=code_exts[ext],
                    content=safe_content
                ).encode("utf-8"))
                return

        # Fallback to default handler for raw files / other types
        # We need to hack the directory context because SimpleHTTPRequestHandler uses CWD
        current_dir = os.getcwd()
        try:
            os.chdir(WEB_ROOT)
            super().do_GET()
        finally:
            os.chdir(current_dir)

class ReusableTCPServer(socketserver.TCPServer):
    allow_reuse_address = True

if __name__ == "__main__":
    print(f"Serving {WEB_ROOT} on port {PORT}...")
    with ReusableTCPServer(("", PORT), MarkdownViewerHandler) as httpd:
        httpd.serve_forever()
