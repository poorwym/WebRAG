import os
import time
import queue
import urllib3
import requests

from bs4 import BeautifulSoup
from urllib.parse import urljoin
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from threading import Thread, Lock
from typing import List, Set
from utils.config_loader import ConfigLoader

# 禁用SSL验证警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 全局常量：更完整的浏览器请求头
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

# 全局锁，用于线程安全
file_lock = Lock()
visited_lock = Lock()
links_lock = Lock()

def create_session() -> requests.Session:
    """
    创建一个带有重试机制的会话（Session），避免网络波动导致爬取中断。
    """
    session = requests.Session()
    retry_strategy = Retry(
        total=3,                # 最多重试3次
        backoff_factor=1,       # 重试间隔
        status_forcelist=[403, 429, 500, 502, 503, 504]  # 重试的状态码
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    session.headers.update(HEADERS)
    session.verify = False  # 禁用SSL验证
    return session

def get_unvisited_urls(links: Set[str], visited_urls: Set[str]) -> List[str]:
    """
    从给定的链接集合中筛选尚未访问的链接，并标记为已访问。
    """
    unvisited = []
    with visited_lock:
        for link in links:
            if link not in visited_urls:
                unvisited.append(link)
                visited_urls.add(link)  # 立即标记，防止其他线程重复处理
    return unvisited

def process_page(
    url: str,
    session: requests.Session,
    output_file: str,
    error_file: str,
    existing_links: Set[str],
    required_prefix: str
) -> Set[str]:
    """
    处理单个页面：获取其内容、提取符合前缀的链接并写入结果文件。

    返回：当前页面中提取到的所有符合要求的链接集合。
    """
    try:
        print(f'正在处理: {url}')
        response = session.get(url, timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')
        found_links = set()
        new_links_count = 0

        for a in soup.find_all('a'):
            href = a.get('href')
            if not href or href.startswith('javascript:') or href.startswith('#'):
                continue

            absolute_url = urljoin(url, href).split('#')[0]  # 去除片段标识符
            if absolute_url.startswith(required_prefix):
                found_links.add(absolute_url)
                # 将新的链接写入文件（线程安全）
                with file_lock:
                    if absolute_url not in existing_links:
                        existing_links.add(absolute_url)
                        new_links_count += 1
                        with open(output_file, 'a', encoding='utf-8') as f:
                            f.write(f'{absolute_url}\n')

        print(f'在 {url} 中找到 {len(found_links)} 个链接，其中 {new_links_count} 个为新链接')
        return found_links

    except Exception as e:
        error_message = f'处理失败: {e}'
        print(f'处理失败 {url}: {error_message}')
        with file_lock:
            with open(error_file, 'a', encoding='utf-8') as f:
                f.write(f'{url}\t{error_message}\n')
        return set()

def worker(
    task_queue: queue.Queue,
    visited_urls: Set[str],
    session: requests.Session,
    output_file: str,
    error_file: str,
    max_depth: int,
    existing_links: Set[str],
    all_links: Set[str],
    required_prefix: str
):
    """
    工作线程函数：从任务队列中获取 (URL, 深度)，爬取页面并提取链接。
    当深度超过 max_depth 时，不再向队列添加新链接。
    """
    while True:
        try:
            url, depth = task_queue.get(timeout=5)
            if depth > max_depth:
                task_queue.task_done()
                continue

            links = process_page(url, session, output_file, error_file, existing_links, required_prefix)
            with links_lock:
                all_links.update(links)

            if depth < max_depth:  # 只有在深度允许时才继续爬
                unvisited = get_unvisited_urls(links, visited_urls)
                for link in unvisited:
                    task_queue.put((link, depth + 1))
                print(f'处理 {url} 完成，深度: {depth}，新增 {len(unvisited)} 个链接到队列')
            else:
                print(f'处理 {url} 完成，达到最大深度 {depth}，不再继续爬取')

            task_queue.task_done()
            time.sleep(0.5)  # 防止请求过快

        except queue.Empty:
            # 队列空，线程退出
            break
        except Exception as e:
            print(f"工作线程发生错误: {e}")
            task_queue.task_done()

def parallel_bfs_crawler(
    start_urls: List[str],
    visited_urls: Set[str],
    output_file: str,
    error_file: str,
    max_depth: int,
    existing_links: Set[str],
    required_prefix: str,
    num_threads: int = 20
) -> Set[str]:
    """
    并行 BFS 策略的爬虫入口。
    参数：
      - start_urls: 初始 URL 列表
      - visited_urls: 已访问的 URL 集合
      - output_file: 结果链接写入文件路径
      - error_file: 错误日志写入文件路径
      - max_depth: 最大爬取深度
      - existing_links: 已有链接集合，避免重复写入
      - required_prefix: 仅爬取符合此前缀的链接
      - num_threads: 并发线程数
    返回：最终发现的所有符合要求的链接集合
    """
    all_links = set()
    task_queue = queue.Queue()

    # 创建带重试的会话池
    sessions = [create_session() for _ in range(num_threads)]

    # 将初始URL放入队列
    to_visit = get_unvisited_urls(set(start_urls), visited_urls)
    for url in to_visit:
        task_queue.put((url, 1))
    print(f"已添加 {task_queue.qsize()} 个起始URL到队列")

    # 启动工作线程
    threads = []
    for i in range(num_threads):
        t = Thread(
            target=worker,
            args=(
                task_queue,
                visited_urls,
                sessions[i],
                output_file,
                error_file,
                max_depth,
                existing_links,
                all_links,
                required_prefix
            ),
            name=f"Worker-{i+1}",
            daemon=True
        )
        t.start()
        threads.append(t)
        print(f"启动工作线程 #{i+1}")

    # 等待任务结束，并显示进度
    last_count = 0
    last_time = time.time()

    try:
        while not task_queue.empty():
            pending = task_queue.qsize()
            visited_count = len(visited_urls)
            links_count = len(existing_links)

            current_time = time.time()
            time_diff = current_time - last_time
            if time_diff >= 5:  # 每隔5秒显示一次爬取速率
                rate = (links_count - last_count) / time_diff
                last_count = links_count
                last_time = current_time
                active_threads = sum(1 for t in threads if t.is_alive())

                print(
                    f"当前状态: 待处理URL: {pending}, "
                    f"已访问URL: {visited_count}, "
                    f"已发现链接: {links_count}, "
                    f"爬取速率: {rate:.2f} 链接/秒, "
                    f"活跃线程: {active_threads}/{num_threads}"
                )

            if pending == 0:
                break
            time.sleep(1)

        task_queue.join()
        print("所有URL处理完毕")
    except KeyboardInterrupt:
        print("接收到中断信号，正在停止...")

    # 等待所有线程（已在 daemon 模式下），可主动 join
    for t in threads:
        if t.is_alive():
            t.join(1)

    return all_links

def main():
    # 读取项目根目录
    config = ConfigLoader()
    data_dir = config.project_root

    # 设置文件路径
    urls_dir = os.path.join(data_dir, 'data', 'urls')
    urls_file = os.path.join(urls_dir, 'urls_to_extract.txt')
    output_file = os.path.join(urls_dir, "extracted_links.txt")
    error_file = os.path.join(urls_dir, "error_links.txt")

    # 基本检查
    if not os.path.exists(urls_dir):
        print(f'错误：路径不存在: {urls_dir}')
        return
    if not os.path.exists(urls_file):
        print(f'错误：路径不存在: {urls_file}')
        return

    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # 参数设置
    MAX_DEPTH = 3
    NUM_THREADS = 20
    required_prefix = "https://cesium.com/learn/"
    # required_prefix = "https://pro.arcgis.com/en/pro-app/3.4/"

    # 如果输出文件存在，则读取已有链接避免重复
    existing_links = set()
    if os.path.exists(output_file):
        print('发现已存在的输出文件，正在读取以避免重复...')
        with open(output_file, 'r', encoding='utf-8') as f:
            for line in f:
                existing_links.add(line.strip())
        print(f'已读取 {len(existing_links)} 个现有链接')

    # 清空/创建错误文件
    open(error_file, 'w', encoding='utf-8').close()

    # 如果 output_file 不存在则创建
    if not os.path.exists(output_file):
        open(output_file, 'w', encoding='utf-8').close()

    # 读取起始URL
    start_urls = []
    with open(urls_file, 'r', encoding='utf-8') as f:
        for line in f:
            url = line.strip()
            if url:
                start_urls.append(url)

    visited_urls = set()
    print(f'最大递归深度: {MAX_DEPTH}')
    print(f'线程数: {NUM_THREADS}')
    print(f'只提取前缀: {required_prefix}')
    print(f'起始URL数量: {len(start_urls)}')

    start_time = time.time()
    try:
        all_links = parallel_bfs_crawler(
            start_urls,
            visited_urls,
            output_file,
            error_file,
            MAX_DEPTH,
            existing_links,
            required_prefix,
            NUM_THREADS
        )
        end_time = time.time()

        valid_links_count = len(existing_links)
        error_links_count = sum(1 for _ in open(error_file, 'r', encoding='utf-8'))

        print(f'爬取完成，耗时: {end_time - start_time:.2f} 秒')
        print(f'共找到 {valid_links_count} 个有效链接（前缀: {required_prefix}），已保存至: {output_file}')
        if error_links_count > 0:
            print(f'有 {error_links_count} 个错误链接，详情见: {error_file}')
    except KeyboardInterrupt:
        end_time = time.time()
        print(f'\n爬取被中断，运行时间: {end_time - start_time:.2f} 秒')
        print(f'已爬取 {len(visited_urls)} 个URL，找到 {len(existing_links)} 个符合条件的链接')
        print('部分结果已保存')

if __name__ == '__main__':
    main()
