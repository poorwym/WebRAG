import os
import sys

# 添加项目根目录到系统路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)
from src.utils.config_loader import ConfigLoader

def init_db(db_name: str):
    config = ConfigLoader()
    db_dir = os.path.join(config.project_root, 'data', 'database', db_name)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    if not os.path.exists(os.path.join(db_dir, 'downloaded_sites')):
        os.makedirs(os.path.join(db_dir, 'downloaded_sites'))
    if not os.path.exists(os.path.join(db_dir, 'curated')):
        os.makedirs(os.path.join(db_dir, 'curated'))
    if not os.path.exists(os.path.join(db_dir, 'chroma_openai')):
        os.makedirs(os.path.join(db_dir, 'chroma_openai'))
    if not os.path.exists(os.path.join(db_dir, 'urls')):
        os.makedirs(os.path.join(db_dir, 'urls'))
    if not os.path.exists(os.path.join(db_dir, 'urls', 'extracted_links.txt')):
        open(os.path.join(db_dir, 'urls', 'extracted_links.txt'), 'w').close()
    if not os.path.exists(os.path.join(db_dir, 'urls', 'error_links.txt')):
        open(os.path.join(db_dir, 'urls', 'error_links.txt'), 'w').close()
    if not os.path.exists(os.path.join(db_dir, 'urls', 'urls_to_extract.txt')):
        open(os.path.join(db_dir, 'urls', 'urls_to_extract.txt'), 'w').close()
    return db_dir

def process(db_name: str):
    init_db(db_name)

if __name__ == '__main__':
    process("cesium")



