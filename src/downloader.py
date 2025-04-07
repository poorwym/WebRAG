import os
import aiohttp
import asyncio
import aiofiles
from urllib.parse import urlparse
import time
from utils.config_loader import ConfigLoader

config = ConfigLoader()

class SimpleAsyncDownloader:
    def __init__(self, delay=1.0, max_connections=10, db_name=""):
        self.delay = delay
        self.semaphore = asyncio.Semaphore(max_connections)
        self.last_request_time = {}
        self.total_downloaded = 0
        self.skipped = 0
        self.downloaded_sites_dir = os.path.join(config.project_root, "data", "downloaded_sites", db_name)

    async def fetch_and_save(self, session, url):
        filepath = os.path.join(self.downloaded_sites_dir, url.split("/")[-1])
        if not os.path.exists(filepath):
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # 已存在跳过
        if os.path.exists(filepath):
            print(f"已存在，跳过：{url}")
            self.skipped += 1
            return

        # 限速
        domain = urlparse(url).netloc
        now = time.time()
        last = self.last_request_time.get(domain, 0)
        if now - last < self.delay:
            await asyncio.sleep(self.delay - (now - last))
        self.last_request_time[domain] = time.time()

        try:
            async with self.semaphore:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        content = await resp.read()
                        os.makedirs(os.path.dirname(filepath), exist_ok=True)
                        async with aiofiles.open(filepath, 'wb') as f:
                            await f.write(content)
                        print(f"下载成功：{url}")
                        self.total_downloaded += 1
                    else:
                        print(f"请求失败：{url}，状态码：{resp.status}")
        except Exception as e:
            print(f"下载出错：{url}，错误：{e}")

    async def run(self, url_list_file):
        with open(url_list_file, 'r') as f:
            urls = [line.strip() for line in f if line.strip()]

        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_and_save(session, url) for url in urls]
            await asyncio.gather(*tasks)

        print(f"\n下载完成：共 {self.total_downloaded} 个页面，跳过 {self.skipped} 个")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--delay", "-d", type=float, default=1.0)
    parser.add_argument("--max", "-m", type=int, default=10)
    args = parser.parse_args()

    downloader = SimpleAsyncDownloader(delay=args.delay, max_connections=args.max, db_name="cesium")
    file_path = os.path.join(config.project_root, "data", "urls", "extracted_links.txt")
    if os.path.exists(file_path):
        asyncio.run(downloader.run(file_path))
    else:
        print(f"文件不存在：{file_path}")
