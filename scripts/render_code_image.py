from __future__ import annotations
import argparse
import asyncio
import contextlib
import http.server
import socketserver
import threading
from pathlib import Path
from typing import Iterator
from playwright.async_api import async_playwright

RATIO_ALIASES = {"youtube": (1920, 1080), "shorts": (1080, 1920), "portrait": (1080, 1920), "square": (1080, 1080)}

def normalize_ratio(value: str) -> tuple[int, int]:
    ratio_key = value.strip().lower()
    if ratio_key in RATIO_ALIASES: return RATIO_ALIASES[ratio_key]
    left, right = ratio_key.split(":", 1)
    width_ratio, height_ratio = int(left), int(right)
    if width_ratio <= height_ratio:
        return 1080, round(1080 * height_ratio / width_ratio)
    else:
        return round(1920 * width_ratio / height_ratio), 1920

class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args: object) -> None: return

@contextlib.contextmanager
def local_server(root: Path) -> Iterator[str]:
    handler = lambda *args, **kwargs: QuietHTTPRequestHandler(*args, directory=str(root), **kwargs)
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as server:
        server.allow_reuse_address = True
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try: yield f"http://127.0.0.1:{server.server_address[1]}"
        finally: server.shutdown(); thread.join()

async def render_code_image(code_path: Path, ratio: str, output_path: Path, delay_ms: int, selector: str):
    width, height = normalize_ratio(ratio)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with local_server(code_path.parent) as server_url:
        target_url = f"{server_url}/{code_path.name}"
        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch()
            page = await browser.new_page(viewport={"width": width, "height": height})
            await page.goto(target_url, wait_until="networkidle")
            if delay_ms > 0: await page.wait_for_timeout(delay_ms)
            await page.locator(selector).first.screenshot(path=str(output_path))
            await browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("code_path")
    parser.add_argument("ratio")
    parser.add_argument("output_path")
    parser.add_argument("--delay-ms", type=int, default=1500)
    parser.add_argument("--selector", default="body")
    args = parser.parse_args()
    asyncio.run(render_code_image(Path(args.code_path).resolve(), args.ratio, Path(args.output_path).resolve(), args.delay_ms, args.selector))
