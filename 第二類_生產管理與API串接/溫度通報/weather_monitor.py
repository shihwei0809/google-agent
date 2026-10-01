#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import urllib.request
import urllib.error
import datetime

def main():
    print(f"[{datetime.datetime.now()}] Triggering Cloudflare D1 Monitor...")
    try:
        req = urllib.request.Request("https://weather-monitor-pwa.pages.dev/api/check", headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        result = response.read().decode('utf-8')
        print("Cloudflare Response:", result)
    except urllib.error.URLError as e:
        print("Error triggering Cloudflare:", e)

if __name__ == "__main__":
    main()
