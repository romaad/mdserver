# Markdown Preview Server

A lightweight, zero-dependency* Python HTTP server to browse directories and render Markdown files on the fly.

## Features

- 📱 **Mobile-Friendly**: Responsive layout with large touch targets.
- 🔍 **Search**: Instant client-side filtering of file lists.
- 🎨 **GitHub Style**: Renders Markdown using GitHub-like CSS.
- 📂 **Navigation**: Clean file explorer with icons.
- ⚡ **Fast**: Built on standard library `http.server`.

## Requirements

- Python 3.x
- No local pip packages required (uses CDN for `marked.js` and CSS).

## Usage

1. Place `md_server.py` in the directory you want to serve (or configure `WEB_ROOT` inside the script).
2. Run the server:
   ```bash
   python3 md_server.py
   ```
3. Open your browser to:
   ```
   http://localhost:8090
   ```

## Configuration

Edit the top of `md_server.py` to change settings:

```python
PORT = 8090
WEB_ROOT = "." # Directory to serve
```
