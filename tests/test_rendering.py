import unittest
import threading
import http.client
import time
import os
import sys
import shutil

# Add parent directory to path to import md_server
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import md_server

# Configuration for test server
TEST_PORT = 8091
TEST_ROOT = "test_workspace"

class TestServerRendering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a dummy workspace
        if os.path.exists(TEST_ROOT):
            shutil.rmtree(TEST_ROOT)
        os.makedirs(TEST_ROOT)
        
        # Create dummy files
        with open(os.path.join(TEST_ROOT, "hello.py"), "w") as f:
            f.write("print('Hello World')")
            
        with open(os.path.join(TEST_ROOT, "README.md"), "w") as f:
            f.write("# Test Title\n\nThis is a test.")

        # Configure server to use test settings
        md_server.PORT = TEST_PORT
        md_server.WEB_ROOT = TEST_ROOT
        # Force templates to reload from the correct relative path if needed
        # (Assuming md_server handles relative paths correctly from CWD)
        
        # Start server in a thread
        cls.server_thread = threading.Thread(target=cls.run_server)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        
        # Give it a moment to start
        time.sleep(1)

    @classmethod
    def run_server(cls):
        # We need to run this inside the repo root context so it finds templates
        # But we also need to serve TEST_ROOT.
        # md_server.py uses WEB_ROOT global.
        with md_server.ReusableTCPServer(("", TEST_PORT), md_server.MarkdownViewerHandler) as httpd:
            cls.httpd = httpd
            httpd.serve_forever()

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, 'httpd'):
            cls.httpd.shutdown()
            cls.httpd.server_close()
        if os.path.exists(TEST_ROOT):
            shutil.rmtree(TEST_ROOT)

    def request_path(self, path):
        conn = http.client.HTTPConnection("localhost", TEST_PORT)
        conn.request("GET", path)
        response = conn.getresponse()
        data = response.read().decode('utf-8')
        conn.close()
        return response.status, data

    def test_01_listing_rendering(self):
        """Ensure the root listing renders with the list template."""
        status, html = self.request_path("/")
        self.assertEqual(status, 200)
        
        # Check for listing-specific elements (from listing.html)
        self.assertIn('<body class="listing-view">', html)
        self.assertIn('id="search"', html)
        self.assertIn('hello.py', html)
        self.assertIn('README.md', html)

    def test_02_code_rendering(self):
        """Ensure code files render with the code viewer template."""
        status, html = self.request_path("/hello.py")
        self.assertEqual(status, 200)
        
        # Check for code-viewer specific elements (from code.html)
        self.assertIn('<body class="code-view">', html)
        self.assertIn('hljs.highlightAll()', html)
        self.assertIn('language-python', html)
        # Content is HTML-escaped in the template
        self.assertIn("print(&#x27;Hello World&#x27;)", html)

    def test_03_markdown_rendering(self):
        """Ensure markdown files render with the markdown viewer template."""
        status, html = self.request_path("/README.md")
        self.assertEqual(status, 200)
        
        # Check for markdown-viewer specific elements (from viewer.html)
        self.assertIn('<body class="markdown-view">', html)
        self.assertIn('github-markdown-css', html)
        # Content is inserted into specific div
        self.assertIn('# Test Title', html) 

if __name__ == '__main__':
    unittest.main()
