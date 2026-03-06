import http.server
import socketserver
import os
import urllib.parse

PORT = 8090
WEB_ROOT = "/home/ramadan/.openclaw/workspace"

# Simple HTML template for the directory listing
LISTING_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Index of {path}</title>
    <style>
        :root {
            --bg-color: #fff;
            --text-color: #24292e;
            --link-color: #0366d6;
            --hover-bg: #f6f8fa;
            --border-color: #eaecef;
            --input-bg: #fff;
            --input-border: #d1d5da;
            --icon-color: #6a737d;
        }
        @media (prefers-color-scheme: dark) {
            :root {
                --bg-color: #0d1117;
                --text-color: #c9d1d9;
                --link-color: #58a6ff;
                --hover-bg: #161b22;
                --border-color: #30363d;
                --input-bg: #0d1117;
                --input-border: #30363d;
                --icon-color: #8b949e;
            }
        }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; padding: 20px; max-width: 800px; margin: 0 auto; color: var(--text-color); background-color: var(--bg-color); }
        h1 { font-size: 1.5rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5em; margin-bottom: 1em; word-break: break-all; color: var(--text-color); }
        ul { list-style: none; padding: 0; margin: 0; }
        li { border-bottom: 1px solid var(--border-color); }
        li:last-child { border-bottom: none; }
        a { text-decoration: none; color: var(--link-color); display: block; padding: 12px 5px; font-size: 16px; transition: background 0.2s; }
        a:hover { text-decoration: none; background-color: var(--hover-bg); border-radius: 4px; }
        .icon { margin-right: 8px; color: var(--icon-color); }
        @media (max-width: 600px) {
            body { padding: 15px; }
            a { padding: 15px 5px; font-size: 18px; } /* Larger touch targets */
        }
        #search { width: 100%; padding: 10px; margin-bottom: 20px; font-size: 16px; border: 1px solid var(--input-border); border-radius: 6px; box-sizing: border-box; background-color: var(--input-bg); color: var(--text-color); }
    </style>
</head>
<body>
    <h1>Index of {path}</h1>
    <input type="text" id="search" placeholder="Search files..." onkeyup="filterList()">
    <ul id="file-list">
        {items}
    </ul>
    <script>
        function filterList() {{
            const input = document.getElementById('search');
            const filter = input.value.toLowerCase();
            const ul = document.getElementById('file-list');
            const li = ul.getElementsByTagName('li');
            for (let i = 0; i < li.length; i++) {{
                const a = li[i].getElementsByTagName('a')[0];
                const txtValue = a.textContent || a.innerText;
                if (txtValue.toLowerCase().indexOf(filter) > -1) {{
                    li[i].style.display = "";
                }} else {{
                    li[i].style.display = "none";
                }}
            }}
        }}
    </script>
</body>
</html>
"""

# HTML template for the markdown viewer
VIEWER_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{filename}</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.2.0/github-markdown-light.min.css">
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <style>
        @media (prefers-color-scheme: dark) {{
            body {{ background-color: #0d1117 !important; color: #c9d1d9 !important; }}
            .markdown-body {{ color: #c9d1d9 !important; }}
            .header {{ background: #161b22 !important; border-bottom-color: #30363d !important; }}
            .btn {{ background: #0d1117 !important; color: #c9d1d9 !important; border-color: #30363d !important; }}
            .btn:hover {{ background-color: #30363d !important; }}
            #source-view {{ background: #0d1117 !important; color: #c9d1d9 !important; }}
        }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; padding: 0; margin: 0; }}
        .header {{ background: #f6f8fa; padding: 10px 20px; border-bottom: 1px solid #e1e4e8; display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 100; }}
        .markdown-body {{ box-sizing: border-box; min-width: 200px; max-width: 980px; margin: 0 auto; padding: 45px; }}
        @media (max-width: 767px) {{ .markdown-body {{ padding: 15px; }} }}
        #source-view {{ display: none; white-space: pre-wrap; font-family: monospace; background: #fff; padding: 20px; overflow: auto; margin: 0 auto; max-width: 980px; }}
        .btn {{ cursor: pointer; padding: 5px 12px; background: #fff; border: 1px solid #d1d5da; border-radius: 3px; font-size: 14px; color: #24292e; text-decoration: none; }}
        .btn:hover {{ background-color: #f3f4f6; }}
    </style>
    <script>
        // Check for dark mode and swap markdown CSS
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {{
            document.querySelector('link[rel="stylesheet"]').href = "https://cdnjs.cloudflare.com/ajax/libs/github-markdown-css/5.2.0/github-markdown-dark.min.css";
        }}
    </script>
</head>
<body>
    <div class="header">
        <div>
            <a href="/" class="btn">⬅ Back</a>
            <span style="margin-left: 10px; font-weight: bold;">{filename}</span>
        </div>
        <div>
            <button class="btn" onclick="toggleView()">Source / Rendered</button>
            <a href="?raw=true" class="btn" download>Download</a>
        </div>
    </div>

    <div id="content" class="markdown-body"></div>
    <pre id="source-view">{raw_content}</pre>

    <script>
        const rawContent = document.getElementById('source-view').textContent;
        document.getElementById('content').innerHTML = marked.parse(rawContent);

        function toggleView() {{
            const content = document.getElementById('content');
            const source = document.getElementById('source-view');
            if (source.style.display === 'none') {{
                source.style.display = 'block';
                content.style.display = 'none';
            }} else {{
                source.style.display = 'none';
                content.style.display = 'block';
            }}
        }}
    </script>
</body>
</html>
"""

# HTML template for code viewer
CODE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{filename}</title>
    <link rel="stylesheet" id="hljs-theme" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/python.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/bash.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/yaml.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/json.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/xml.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/languages/css.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/highlightjs-line-numbers.js/2.8.0/highlightjs-line-numbers.min.js"></script>
    <style>
        :root {
            --bg-color: #fff;
            --text-color: #24292e;
            --header-bg: #f6f8fa;
            --header-border: #e1e4e8;
            --pre-bg: #f6f8fa;
            --ln-color: #ccc;
            --ln-border: #ccc;
            --btn-bg: #fff;
            --btn-border: #d1d5da;
            --btn-hover: #f3f4f6;
        }
        @media (prefers-color-scheme: dark) {{
            :root {{
                --bg-color: #0d1117;
                --text-color: #c9d1d9;
                --header-bg: #161b22;
                --header-border: #30363d;
                --pre-bg: #0d1117;
                --ln-color: #484f58;
                --ln-border: #30363d;
                --btn-bg: #21262d;
                --btn-border: #363b42;
                --btn-hover: #30363d;
            }}
        }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif; padding: 0; margin: 0; background-color: var(--bg-color); color: var(--text-color); }}
        .header {{ background: var(--header-bg); padding: 10px 20px; border-bottom: 1px solid var(--header-border); display: flex; justify-content: space-between; align-items: center; position: sticky; top: 0; z-index: 10; }}
        .container {{ padding: 20px; overflow-x: auto; }}
        pre {{ margin: 0; padding: 10px; border-radius: 6px; background-color: var(--pre-bg); }}
        code {{ font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace; font-size: 14px; }}
        .btn {{ cursor: pointer; padding: 5px 12px; background: var(--btn-bg); border: 1px solid var(--btn-border); border-radius: 3px; font-size: 14px; color: var(--text-color); text-decoration: none; display: inline-block; margin-left: 5px;}}
        .btn:hover {{ background-color: var(--btn-hover); }}
        /* Line numbers styling */
        .hljs-ln-numbers {{ -webkit-touch-callout: none; -webkit-user-select: none; -khtml-user-select: none; -moz-user-select: none; -ms-user-select: none; user-select: none; text-align: right; color: var(--ln-color); border-right: 1px solid var(--ln-border); vertical-align: top; padding-right: 5px; }}
        .hljs-ln-code {{ padding-left: 10px; }}
        
        /* Wrap lines class */
        .wrap-lines .hljs-ln-code {{ white-space: pre-wrap; word-wrap: break-word; }}
    </style>
    <script>
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {{
            document.getElementById('hljs-theme').href = "https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css";
        }}
    </script>
</head>
<body>
    <div class="header">
        <div>
            <a href="/" class="btn">⬅ Back</a>
            <span style="margin-left: 10px; font-weight: bold;">{filename}</span>
        </div>
        <div>
            <button class="btn" onclick="toggleWrap()">Wrap Lines</button>
            <button class="btn" onclick="copyToClipboard()">Copy</button>
            <a href="?raw=true" class="btn" download>Download</a>
        </div>
    </div>

    <div class="container">
        <pre><code id="code-block" class="language-{ext}">{content}</code></pre>
    </div>

    <script>
        hljs.highlightAll();
        hljs.initLineNumbersOnLoad();

        function toggleWrap() {{
            document.querySelector('table').classList.toggle('wrap-lines');
        }}

        function copyToClipboard() {{
            const code = document.getElementById('code-block').innerText;
            navigator.clipboard.writeText(code).then(() => {{
                const btn = document.querySelector('button[onclick="copyToClipboard()"]');
                const originalText = btn.innerText;
                btn.innerText = "Copied!";
                setTimeout(() => {{ btn.innerText = originalText; }}, 2000);
            }}).catch(err => {{
                console.error('Failed to copy: ', err);
            }});
        }}
    </script>
</body>
</html>
"""

class MarkdownViewerHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        # Decode the URL path
        path = urllib.parse.unquote(self.path)
        
        # Security check: prevent directory traversal
        if ".." in path:
            self.send_error(403, "Forbidden")
            return

        # Map to local file path
        # If path starts with /plans/, map it to WEB_ROOT/plans/
        # Wait, WEB_ROOT is public_html. Let's assume public_html structure mirrors URL.
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
                # Fix: Don't join path here for the display link, relative is safer/easier
                # link_path = os.path.join(path, item).replace("\\", "/") 
                # Actually standard SimpleHTTPRequestHandler uses relative links usually
                
                abs_item_path = os.path.join(full_path, item)
                is_dir = os.path.isdir(abs_item_path)
                
                display_name = item + ("/" if is_dir else "")
                icon = "📂" if is_dir else "📄"
                
                # Link is just the item name, relative to current page
                link_href = urllib.parse.quote(display_name)
                
                items.append(f'<li><a href="{link_href}"><span class="icon">{icon}</span> {display_name}</a></li>')
            
            self.wfile.write(LISTING_TEMPLATE.format(path=path, items="\n".join(items)).encode("utf-8"))
            return

        # Check if it's a markdown file and user didn't ask for raw
        if full_path.endswith(".md") and "raw=true" not in self.path:
            if os.path.exists(full_path):
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()
                
                with open(full_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                # Escape HTML in the source view to prevent rendering issues inside <pre>
                import html
                safe_content = html.escape(content)
                
                self.wfile.write(VIEWER_TEMPLATE.format(
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
            ".md": "markdown" # Fallback if md handler missed it? No, md is above.
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
                
                self.wfile.write(CODE_TEMPLATE.format(
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

print(f"Serving {WEB_ROOT} on port {PORT}...")
with ReusableTCPServer(("", PORT), MarkdownViewerHandler) as httpd:
    httpd.serve_forever()
