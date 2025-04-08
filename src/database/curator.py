#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import argparse
import sys
# 添加项目根目录到系统路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.utils.config_loader import ConfigLoader
from tqdm import tqdm

from src.utils.logger import Logger

try:
    import html2text
    H2T_AVAILABLE = True
except ImportError:
    H2T_AVAILABLE = False

# 初始化Logger
logger = Logger("curator")

class PageCurator:
    def __init__(self, input_dir, config, db_name=""):
        self.input_dir = input_dir
        self.config = config
        self.output_dir = os.path.join(self.config.project_root, "data", "database", db_name, "curated")
        logger.info(f"初始化PageCurator: 输入目录={input_dir}, 输出目录={self.output_dir}")

    def clean_html(self, html):
        logger.debug("开始清理HTML内容")
        html = re.sub(r'[^\x00-\x7F]+', '', html) 
        soup = BeautifulSoup(html, 'html.parser')

        for tag in soup(['script','style','iframe','noscript']):
            tag.decompose()

        selectors = [
            'nav','.nav','.navigation','.navbar','.sidebar','.menu','.header','.footer',
            '.search','.pagination','[role="search"]','[role="navigation"]','.wy-nav-side',
            '.wy-side-scroll','.wy-side-nav-search','.wy-menu','.rst-versions','.wy-nav-top',
            '.toc','.breadcrumb','.toctree','.contents','#table-of-contents','[role="contentinfo"]'
        ]
        for sel in selectors:
            for e in soup.select(sel):
                e.decompose()

        for a in soup.find_all('a'):
            href = a.get('href','')
            txt = a.text.lower()
            nav_keywords = ['search','next','prev','previous','index','home','contact','about']
            if any(k in txt for k in nav_keywords) or any(k in href.lower() for k in nav_keywords) or href.startswith('http'):
                a.replace_with(a.text)

        for t in soup.find_all():
            if t.name not in ['br','img'] and not t.text.strip() and not t.contents:
                t.decompose()

        # 选主内容区域
        main_candidates = ['main','article','#content','.content','.main-content','.document','.section']
        main_content = None
        for c in main_candidates:
            sec = soup.select_one(c)
            if sec:
                main_content = sec
                logger.debug(f"找到主内容区域: {c}")
                break
        
        result = str(main_content) if main_content else str(soup.body or soup)
        logger.debug(f"HTML清理完成，内容大小: {len(result)} 字符")
        return result

    def html_to_markdown(self, cleaned_html):
        logger.debug("开始转换HTML到Markdown")
        if H2T_AVAILABLE:
            h = html2text.HTML2Text()
            h.ignore_links = True
            h.ignore_images = True
            h.ignore_tables = False
            h.ignore_emphasis = True
            result = h.handle(cleaned_html)
            logger.debug(f"使用html2text转换完成，内容大小: {len(result)} 字符")
            return result
        else:
            # 简易备用
            logger.debug("未找到html2text库，使用备用转换方法")
            soup = BeautifulSoup(cleaned_html, 'html.parser')
            lines = []
            for i in range(1,7):
                for heading in soup.find_all(f'h{i}'):
                    lines.append(f"{'#'*i} {heading.text.strip()}\n")
            for p in soup.find_all('p'):
                lines.append(p.text.strip() + "\n\n")
            for ul in soup.find_all('ul'):
                for li in ul.find_all('li'):
                    lines.append(f"* {li.text.strip()}\n")
                lines.append("\n")
            for ol in soup.find_all('ol'):
                for idx, li in enumerate(ol.find_all('li')):
                    lines.append(f"{idx+1}. {li.text.strip()}\n")
                lines.append("\n")
            result = ''.join(lines)
            logger.debug(f"备用方法转换完成，内容大小: {len(result)} 字符")
            return result

    def process_file(self, filepath):
        filename = os.path.basename(filepath)
        try:
            logger.debug(f"开始处理文件: {filepath}")
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
            
            logger.debug(f"文件 {filename} 读取成功，大小: {len(html_content)} 字符")
            cleaned = self.clean_html(html_content)
            markdown = self.html_to_markdown(cleaned)
            
            rel_path = os.path.relpath(filepath, self.input_dir)
            out_path = os.path.join(self.output_dir, rel_path)
            out_path = os.path.splitext(out_path)[0] + '.md'
            os.makedirs(os.path.dirname(out_path), exist_ok=True)
            
            with open(out_path, 'w', encoding='utf-8') as f:
                f.write(markdown)
            
            logger.debug(f"文件 {filename} 处理完成，已保存到: {out_path}")
            return True
        except Exception as e:
            logger.error(f"处理文件 {filename} 失败: {str(e)}")
            return False

    def process_directory(self, max_workers=8):
        logger.info(f"开始处理目录: {self.input_dir}")
        os.makedirs(self.output_dir, exist_ok=True)
        html_files = []
        
        # 获取所有HTML文件
        for root, dirs, files in os.walk(self.input_dir):
            for fn in files:
                if fn.endswith('.html'):
                    html_files.append(os.path.join(root, fn))
        
        total_files = len(html_files)
        logger.info(f"找到 {total_files} 个HTML文件需要处理")
        
        if total_files == 0:
            logger.warning(f"在 {self.input_dir} 中未找到HTML文件")
            return

        processed, failed = 0, 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self.process_file, f) for f in html_files]
            
            # 使用tqdm创建进度条
            with tqdm(total=total_files, desc="处理HTML文件") as pbar:
                for future in as_completed(futures):
                    if future.result():
                        processed += 1
                    else:
                        failed += 1
                    pbar.update(1)

        logger.info(f"目录处理完成: 总共处理 {processed} 个文件, 失败 {failed} 个.")
        print(f"总共处理 {processed} 个文件, 失败 {failed} 个.")

def process(db_name: str):
    config = ConfigLoader()
    data_dir = os.path.join(config.project_root, "data", "database", db_name)
    input_dir = os.path.join(data_dir, "downloaded_sites")

    max_threads = 20
    
    logger.info(f"启动页面整理器，使用 {max_threads} 个线程")
    curator = PageCurator(input_dir, config, db_name=db_name)
    curator.process_directory(max_workers=max_threads)

if __name__ == "__main__":
    process("cesium")
