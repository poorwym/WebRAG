import os
import sys
from utils.config_loader import ConfigLoader

# 获取项目根目录
config = ConfigLoader()
PROJECT_ROOT = config.project_root
try:
    os.mkdir(os.path.join(PROJECT_ROOT, 'data', 'database'))
    os.mkdir(os.path.join(PROJECT_ROOT, 'data', 'conversations'))
    os.mkdir(os.path.join(PROJECT_ROOT, 'data', 'logs'))
except Exception as e:
    print(f"创建目录时出错: {e}")





