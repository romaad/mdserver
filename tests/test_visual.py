import unittest
import threading
import time
import os
import sys
import shutil
from PIL import Image, ImageStat

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import md_server

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Skipping visual tests: playwright not installed. Run `pip install playwright && playwright install`")
    sys.exit(0)

TEST_PORT = 8092
TEST_ROOT = "test_workspace_visual"

class TestVisualRendering(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Setup workspace
        if os.path.exists(TEST_ROOT):
            shutil.rmtree(TEST_ROOT)
        os.makedirs(TEST_ROOT)
        
        with open(os.path.join(TEST_ROOT, "visual_test.py"), "w") as f:
            f.write("print('Hello Visual World')\n# This should be highlighted")

        # Configure server
        md_server.PORT = TEST_PORT
        md_server.WEB_ROOT = TEST_ROOT
        
        # Start server
        cls.server_thread = threading.Thread(target=cls.run_server)
        cls.server_thread.daemon = True
        cls.server_thread.start()
        time.sleep(2) # Wait for startup

    @classmethod
    def run_server(cls):
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

    def check_image_not_blank(self, path):
        """Returns True if image is not a solid color (blank)."""
        img = Image.open(path).convert("L") # Convert to grayscale
        stat = ImageStat.Stat(img)
        variance = stat.var[0]
        mean = stat.mean[0]
        
        print(f"Image {path}: Mean={mean:.2f}, Variance={variance:.2f}")
        
        # A solid white image has Mean=255 and Variance=0
        # A solid black image has Mean=0 and Variance=0
        # A real page will have significant variance
        if variance < 5.0:
            return False # Too uniform (likely blank)
        return True

    def test_screenshots(self):
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            
            # 1. Test Listing Page
            page.goto(f"http://localhost:{TEST_PORT}/")
            page.screenshot(path="screenshot_list.png")
            self.assertTrue(self.check_image_not_blank("screenshot_list.png"), "Listing page screenshot is blank/uniform!")
            
            # 2. Test Code Viewer
            page.goto(f"http://localhost:{TEST_PORT}/visual_test.py")
            # Wait for highlight.js (it runs on load)
            page.wait_for_selector("code.hljs")
            page.screenshot(path="screenshot_code.png")
            self.assertTrue(self.check_image_not_blank("screenshot_code.png"), "Code viewer screenshot is blank/uniform!")
            
            browser.close()
            
            # Cleanup
            if os.path.exists("screenshot_list.png"): os.remove("screenshot_list.png")
            if os.path.exists("screenshot_code.png"): os.remove("screenshot_code.png")

if __name__ == '__main__':
    unittest.main()
