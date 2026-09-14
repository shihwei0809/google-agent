import asyncio
from pyppeteer import launch

async def main():
    browser = await launch(headless=True, executablePath='C:/Program Files/Google/Chrome/Application/chrome.exe')
    page = await browser.newPage()
    
    page.on('console', lambda msg: print(f'CONSOLE: {msg.text}'))
    page.on('pageerror', lambda err: print(f'PAGE ERROR: {err}'))
    
    await page.goto('http://localhost:18082/index.html')
    await asyncio.sleep(2)
    await browser.close()

asyncio.get_event_loop().run_until_complete(main())
