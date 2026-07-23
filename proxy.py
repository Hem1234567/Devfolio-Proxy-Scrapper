#!/usr/bin/env python3
"""
Local proxy for the PEC Hacks control-room dashboard.

WHY THIS EXISTS
Devfolio's organizer API authenticates via a session COOKIE, and browsers
will not let a webpage (like the dashboard HTML file) attach a Cookie header
to its own requests, or send devfolio.co's cookies to a page hosted anywhere
else. Running this script on your own machine sidesteps that: it makes the
request server-side (Python, not a browser), attaches your cookie itself,
and hands the JSON back to the dashboard over localhost.

SETUP
1. Paste your cookie value into COOKIE below.
   Get it from DevTools -> Network -> click any api.devfolio.co request ->
   Headers -> Request Headers -> "cookie" -> copy the FULL value.
2. Run:  python3 proxy.py
3. Leave this terminal open. In the dashboard's connect bar, choose
   "Route through local proxy" and leave the default URL (http://localhost:8787).

SECURITY NOTE
Your cookie is a live login session. This script only ever sends it to
api.devfolio.co and only listens on 127.0.0.1 (not reachable from other
machines on your network). Still, treat this file like a password -- don't
share it, and don't commit it anywhere.
"""

import json
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

# ---- paste your cookie header value between the quotes ----
COOKIE = "rl_page_init_referrer=RudderEncrypt%3AU2FsdGVkX1%2F6fA5%2BDlgv6zd7x%2FWLtudQDZDYsmKxo1E%3D; rl_page_init_referring_domain=RudderEncrypt%3AU2FsdGVkX1%2BIweko4PgRqmXsqo0Z9UQ9esusr0h1ZcY%3D; rl_trait=RudderEncrypt%3AU2FsdGVkX1%2B7avwDwqhjex0onBYTWUOxq1GUxnz6K0k%3D; rl_group_id=RudderEncrypt%3AU2FsdGVkX19qRlOl3seSkpfBlGBEW%2FYhwC9%2BCpxf%2Fxk%3D; rl_group_trait=RudderEncrypt%3AU2FsdGVkX18zPAT1uEnvqQdM1Euuk2XcfZqwR3nn1lc%3D; rl_anonymous_id=RudderEncrypt%3AU2FsdGVkX18NqsH05MzuembDNDsFp3cbQ%2BJb8g437ufbopxFrckwb4MUzekZ4b4B2a4O0qT7VCF%2BxZ0HFaXing%3D%3D; rl_user_id=RudderEncrypt%3AU2FsdGVkX1%2FPPepbWDQsVWy%2Bf0jhdPUeGD3V%2FmP9mpCYsHoHestIYUg1TpimOaA1uEBm9vB%2Fr%2B6oXo%2FbwW6JcA%3D%3D; rl_session=RudderEncrypt%3AU2FsdGVkX1%2F2VCzgiKBiGEHWoxljRRJuBn6tmp7z9a8b4y6dMAbyHrfOJBZDixm9v8akOtxIsBzsy6yJQLks28AjGeqhUxRwo5TqslYOeHGuVXpQFKaTr6VmXuN2DHKC9S4j5aT9ji%2BjrpKMsYIWjA%3D%3D; devfolio_user=eyJpZCI6MTUzMjk4MywidXVpZCI6ImZlZDc2ZjIxZGQzZjRhMzRiZTE3MzY1YTUwOGNjMDJmIiwicm9sZXMiOlt7ImlkIjoyLCJ1dWlkIjoiOTExN2I2NGU3NWFlNGQyOWIwMjE0YzBjNDdkY2EwYjgiLCJuYW1lIjoidXNlciIsImRlc2MiOiJEZWZhdWx0IHJvbGUgZm9yIHVzZXJzIiwiY3JlYXRlZF9hdCI6IjIwMTgtMDYtMDdUMTc6Mzg6MDYuMDAwWiIsInVwZGF0ZWRfYXQiOiIyMDE4LTA2LTA3VDE3OjM4OjA2LjAwMFoifV19; devfolio_auth=s%3AeyJhY2Nlc3NfdG9rZW4iOiJleUpoYkdjaU9pSklVekkxTmlJc0luUjVjQ0k2SWtwWFZDSjkuZXlKMWRXbGtJam9pWm1Wa056Wm1NakZrWkRObU5HRXpOR0psTVRjek5qVmhOVEE0WTJNd01tWWlMQ0owZVhCbElqb2lZV05qWlhOelgzUnZhMlZ1SWl3aWFXRjBJam94Tnpnek9URTBPVGs0TENKbGVIQWlPakUzT0RRd01ERXpPVGg5LjFtVTFiTmVZZXA3OU9MYzJONUliQnFMVEphNWtUUWdvWC1PUnM3Nmlxb2siLCJyZWZyZXNoX3Rva2VuIjoiZXlKaGJHY2lPaUpJVXpJMU5pSXNJblI1Y0NJNklrcFhWQ0o5LmV5SjFkV2xrSWpvaVptVmtOelptTWpGa1pETm1OR0V6TkdKbE1UY3pOalZoTlRBNFkyTXdNbVlpTENKMGVYQmxJam9pY21WbWNtVnphRjkwYjJ0bGJpSXNJbWxoZENJNk1UYzRNamc1TmpjNE1Td2laWGh3SWpveE9ERTBORE15TnpneGZRLlp6bW1CbjRSanNqRkV5bjAwUzJtY1Y2dTVyaUJvSnU1V19feU8zUnpWVlUifQ.lDMaa57sX%2B48zJIVbFXEYv%2FP6E04tVMvUdNul9YlQ54; ph_BB8GD3buLMoHZ_CfLSGVYZ2wdzYuJ7XMWF7oeKAc4Ro_posthog=%7B%22distinct_id%22%3A%22fed76f21dd3f4a34be17365a508cc02f%22%2C%22%24sesid%22%3A%5B1783939623991%2C%22019f5b16-22c9-7cbe-905e-ad8680e2b1ed%22%2C1783939605193%5D%2C%22%24epp%22%3Atrue%2C%22%24initial_person_info%22%3A%7B%22r%22%3A%22%24direct%22%2C%22u%22%3A%22https%3A%2F%2Fdevfolio.co%2Fhackathons%22%7D%7D; cf_clearance=lzHNMVumYZKrKlP.4tlV4vMZ8eibKXX46LFurFG1jEo-1783940363-1.2.1.1-4xotKTCTT56PyYakNM91RRy03w5tRtJh2_wq9y3D8yvc7rxQpGabWeq7Vcx2EN7Xfx5v_6QP0IIDTiKVNtiUO5vhC79SBozL0OY_Wny6hNg89.fgsTwWiKF8AbE3vhpRi5ujF4kx6LEExLbmgcCCnygS5zT24s9JXMXZz1KwNheDxPVlZ9.ZDjjd7RDQTMmQWo39XZ5XC8lIPpFKqXiKQkPjM9f6OgDNKzKaNRRi2tKTGc24NXoIJNALwFZfEsvJ_Nfung_yGB.PPD8yIFZwwTnn7jM9L8XgchVLSi3nW3i4KkJBYvVxokrfojsU5Upvna6NoE.BQUX2SGlWpKS6rQ"
# -------------------------------------------------------------

PORT = 8787
UPSTREAM = "https://api.devfolio.co"


class ProxyHandler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_GET(self):
        if COOKIE.startswith("PASTE_"):
            self.send_response(500)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "error": "Open proxy.py and paste your real cookie value into COOKIE, then restart this script."
            }).encode())
            return

        if not self.path.startswith("/api/"):
            self.send_response(404)
            self._cors()
            self.end_headers()
            return

        target = UPSTREAM + self.path
        req = urllib.request.Request(target, headers={
            "Accept": "application/json",
            "Cookie": COOKIE,
            "Origin": "https://org.devfolio.co",
            "Referer": "https://org.devfolio.co/",
            "User-Agent": "Mozilla/5.0 (compatible; local-dashboard-proxy)",
        })

        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                body = resp.read()
                self.send_response(resp.status)
                self._cors()
                self.send_header("Content-Type", resp.headers.get("Content-Type", "application/json"))
                self.end_headers()
                self.wfile.write(body)
                print(f"[proxy] {resp.status}  {self.path}")
        except urllib.error.HTTPError as e:
            body = e.read()
            self.send_response(e.code)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
            print(f"[proxy] {e.code}  {self.path}")
        except Exception as e:
            self.send_response(502)
            self._cors()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
            print(f"[proxy] ERROR  {self.path}  {e}")

    def log_message(self, format, *args):
        pass  # quiet default logging; we print our own lines above


if __name__ == "__main__":
    print(f"Proxy running at http://localhost:{PORT}  ->  {UPSTREAM}")
    print("Leave this window open while you use the dashboard. Ctrl+C to stop.")
    HTTPServer(("127.0.0.1", PORT), ProxyHandler).serve_forever()
