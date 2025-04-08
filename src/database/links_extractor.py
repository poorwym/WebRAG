import os
import time
import queue
import urllib3
import requests
import sys

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)

from bs4 import BeautifulSoup
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from threading import Thread, Lock
from typing import List, Set
from src.utils.config_loader import ConfigLoader
from src.utils.logger import Logger

# 禁用SSL验证警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class LinksExtractor:
    # 类常量：更完整的浏览器请求头
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }

    def __init__(self, db_name: str, max_depth: int = 3, num_threads: int = 20, file_path: str = None):
        """
        初始化链接提取器
        :param db_name: 数据库名称
        :param max_depth: 最大爬取深度
        :param num_threads: 并发线程数
        """
        self.config = ConfigLoader()
        self.data_dir = os.path.join(self.config.project_root, 'data', 'database', db_name)
        self.max_depth = max_depth
        self.num_threads = num_threads
        self.logger = Logger("links_extractor")
        
        # 设置文件路径
        self.urls_dir = os.path.join(self.data_dir, 'urls')
        self.urls_file = os.path.join(self.urls_dir, 'urls_to_extract.txt')
        self.output_file = os.path.join(self.urls_dir, "extracted_links.txt")
        self.error_file = os.path.join(self.urls_dir, "error_links.txt")
        
        # 初始化锁
        self.file_lock = Lock()
        self.visited_lock = Lock()
        self.links_lock = Lock()
        
        # 初始化集合
        self.visited_urls = set()
        self.existing_links = set()
        self.all_links = set()
        
        # 确保目录存在
        os.makedirs(self.urls_dir, exist_ok=True)
        
        # 如果file_path存在，则将file_path中的URL写入urls_to_extract.txt文件
        if file_path:
            self._write_urls_to_extract(file_path)

    def _write_urls_to_extract(self, file_path: str):
        """
        将file_path中的URL写入urls_to_extract.txt文件
        :param file_path: 包含URL的文件路径
        """
        if not os.path.exists(file_path):
            self.logger.error(f"文件不存在: {file_path}")
            return
            
        # 读取源文件中的URL
        with open(file_path, 'r', encoding='utf-8') as source:
            urls = [line.strip() for line in source if line.strip()]
            
        # 写入urls_to_extract.txt
        with open(self.urls_file, 'w', encoding='utf-8') as target:
            for url in urls:
                target.write(f"{url}\n")
                
        self.logger.info(f"已将 {len(urls)} 个URL写入: {self.urls_file}")

    def create_session(self) -> requests.Session:
        """
        创建一个带有重试机制的会话（Session）
        """
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[403, 429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update(self.HEADERS)
        session.verify = False
        return session

    def get_unvisited_urls(self, links: Set[str]) -> List[str]:
        """
        从给定的链接集合中筛选尚未访问的链接
        """
        unvisited = []
        with self.visited_lock:
            for link in links:
                if link not in self.visited_urls:
                    unvisited.append(link)
                    self.visited_urls.add(link)
        return unvisited

    def process_page(
        self,
        url: str,
        session: requests.Session,
        required_prefix: str
    ) -> Set[str]:
        """
        处理单个页面并提取链接
        """
        try:
            self.logger.info(f'正在处理: {url}')
            response = session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            found_links = set()
            new_links_count = 0

            for a in soup.find_all('a'):
                href = a.get('href')
                if not href or href.startswith('javascript:') or href.startswith('#'):
                    continue

                absolute_url = urljoin(url, href).split('#')[0]
                if absolute_url.startswith(required_prefix):
                    found_links.add(absolute_url)
                    with self.file_lock:
                        if absolute_url not in self.existing_links:
                            self.existing_links.add(absolute_url)
                            new_links_count += 1
                            with open(self.output_file, 'a', encoding='utf-8') as f:
                                f.write(f'{absolute_url}\n')

            self.logger.info(f'在 {url} 中找到 {len(found_links)} 个链接，其中 {new_links_count} 个为新链接')
            return found_links

        except Exception as e:
            error_message = f'处理失败: {e}'
            self.logger.error(f'处理失败 {url}: {error_message}')
            with self.file_lock:
                with open(self.error_file, 'a', encoding='utf-8') as f:
                    f.write(f'{url}\t{error_message}\n')
            return set()

    def worker(
        self,
        task_queue: queue.Queue,
        session: requests.Session,
        required_prefix: str
    ):
        """
        工作线程函数
        """
        while True:
            try:
                url, depth = task_queue.get(timeout=5)
                if depth > self.max_depth:
                    task_queue.task_done()
                    continue

                links = self.process_page(url, session, required_prefix)
                with self.links_lock:
                    self.all_links.update(links)

                if depth < self.max_depth:
                    unvisited = self.get_unvisited_urls(links)
                    for link in unvisited:
                        task_queue.put((link, depth + 1))
                    self.logger.info(f'处理 {url} 完成，深度: {depth}，新增 {len(unvisited)} 个链接到队列')
                else:
                    self.logger.info(f'处理 {url} 完成，达到最大深度 {depth}，不再继续爬取')

                task_queue.task_done()
                time.sleep(0.5)

            except queue.Empty:
                break
            except Exception as e:
                self.logger.error(f"工作线程发生错误: {e}")
                task_queue.task_done()

    def parallel_bfs_crawler(
        self,
        start_urls: List[str],
        required_prefix: str
    ) -> Set[str]:
        """
        并行BFS爬虫主函数
        """
        task_queue = queue.Queue()
        sessions = [self.create_session() for _ in range(self.num_threads)]

        # 将初始URL放入队列
        to_visit = self.get_unvisited_urls(set(start_urls))
        for url in to_visit:
            task_queue.put((url, 1))
        self.logger.info(f"已添加 {task_queue.qsize()} 个起始URL到队列")

        # 启动工作线程
        threads = []
        for i in range(self.num_threads):
            t = Thread(
                target=self.worker,
                args=(task_queue, sessions[i], required_prefix),
                name=f"Worker-{i+1}",
                daemon=True
            )
            t.start()
            threads.append(t)
            self.logger.info(f"启动工作线程 #{i+1}")

        # 等待任务结束，并显示进度
        last_count = 0
        last_time = time.time()

        try:
            while not task_queue.empty():
                pending = task_queue.qsize()
                visited_count = len(self.visited_urls)
                links_count = len(self.existing_links)

                current_time = time.time()
                time_diff = current_time - last_time
                if time_diff >= 5:
                    rate = (links_count - last_count) / time_diff
                    last_count = links_count
                    last_time = current_time
                    active_threads = sum(1 for t in threads if t.is_alive())

                    self.logger.info(
                        f"当前状态: 待处理URL: {pending}, "
                        f"已访问URL: {visited_count}, "
                        f"已发现链接: {links_count}, "
                        f"爬取速率: {rate:.2f} 链接/秒, "
                        f"活跃线程: {active_threads}/{self.num_threads}"
                    )

                if pending == 0:
                    break
                time.sleep(1)

            task_queue.join()
            self.logger.info("所有URL处理完毕")
        except KeyboardInterrupt:
            self.logger.warning("接收到中断信号，正在停止...")

        # 等待所有线程
        for t in threads:
            if t.is_alive():
                t.join(1)

        return self.all_links

    def process(self, required_prefix: str = "https://cesium.com/learn/"):
        """
        处理入口函数
        """
        # 基本检查
        if not os.path.exists(self.urls_dir):
            self.logger.error(f'错误：路径不存在: {self.urls_dir}')
            return
        if not os.path.exists(self.urls_file):
            self.logger.error(f'错误：路径不存在: {self.urls_file}')
            return

        # 如果输出文件存在，则读取已有链接避免重复
        if os.path.exists(self.output_file):
            self.logger.info('发现已存在的输出文件，正在读取以避免重复...')
            with open(self.output_file, 'r', encoding='utf-8') as f:
                for line in f:
                    self.existing_links.add(line.strip())
            self.logger.info(f'已读取 {len(self.existing_links)} 个现有链接')

        # 清空/创建错误文件
        open(self.error_file, 'w', encoding='utf-8').close()

        # 如果 output_file 不存在则创建
        if not os.path.exists(self.output_file):
            open(self.output_file, 'w', encoding='utf-8').close()

        # 读取起始URL
        start_urls = []
        with open(self.urls_file, 'r', encoding='utf-8') as f:
            for line in f:
                url = line.strip()
                if url:
                    start_urls.append(url)

        self.logger.info(f'最大递归深度: {self.max_depth}')
        self.logger.info(f'线程数: {self.num_threads}')
        self.logger.info(f'只提取前缀: {required_prefix}')
        self.logger.info(f'起始URL数量: {len(start_urls)}')

        start_time = time.time()
        try:
            self.all_links = self.parallel_bfs_crawler(start_urls, required_prefix)
            end_time = time.time()

            valid_links_count = len(self.existing_links)
            error_links_count = sum(1 for _ in open(self.error_file, 'r', encoding='utf-8'))

            self.logger.info(f'爬取完成，耗时: {end_time - start_time:.2f} 秒')
            self.logger.info(f'共找到 {valid_links_count} 个有效链接（前缀: {required_prefix}），已保存至: {self.output_file}')
            if error_links_count > 0:
                self.logger.warning(f'有 {error_links_count} 个错误链接，详情见: {self.error_file}')
        except KeyboardInterrupt:
            end_time = time.time()
            self.logger.warning(f'\n爬取被中断，运行时间: {end_time - start_time:.2f} 秒')
            self.logger.info(f'已爬取 {len(self.visited_urls)} 个URL，找到 {len(self.existing_links)} 个符合条件的链接')
            self.logger.info('部分结果已保存')

if __name__ == '__main__':
    extractor = LinksExtractor("cesium")
    extractor.process()
