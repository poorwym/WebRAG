import os
import sys
import utils.config_loader as ConfigLoader

# 获取项目根目录
PROJECT_ROOT = ConfigLoader.project_root
os.mkdir(os.path.join(PROJECT_ROOT, 'data', 'database'))
os.mkdir(os.path.join(PROJECT_ROOT, 'data', 'conversations'))
os.mkdir(os.path.join(PROJECT_ROOT, 'data', 'logs'))





