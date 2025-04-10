import os
import json
import re
from dotenv import load_dotenv
from .logger import Logger

def singleton(cls):
    instances = {}
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance

@singleton
class ConfigLoader:
    def __init__(self, config_path=None):
        self.project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.logger = Logger("config_loader")
        # 加载 .env 文件
        env_path = os.path.join(self.project_root, 'configs', '.env')
        load_dotenv(env_path)
        try:
            self.logger.info(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY')}")
            pass
        except Exception as e:
            self.logger.error(f"加载 .env 文件失败: {e}")

        # 加载 embedding_model_list.json
        embedding_model_path = os.path.join(self.project_root, 'configs', 'embedding_model_list.json')

        self.embedding_model_list = self._load_config(embedding_model_path)
        # 加载 llm_list.json
        llm_model_path = os.path.join(self.project_root, 'configs', 'llm_list.json')
        self.llm_model_list = self._load_config(llm_model_path)

        # 加载 config.json
        if config_path is None:
            config_path = os.path.join(self.project_root, 'configs', 'config.json')
        else:
            config_path = os.path.join(self.project_root, config_path)
            
        self.config = self._load_config(config_path)

    def _load_config(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        return self._resolve_env_vars(raw)

    def _resolve_env_vars(self, obj):
        """递归解析所有 ${ENV_VAR} 环境变量"""
        if isinstance(obj, dict):
            return {k: self._resolve_env_vars(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._resolve_env_vars(i) for i in obj]
        elif isinstance(obj, str):
            return re.sub(r"\$\{([^}^{]+)\}", lambda m: os.getenv(m.group(1), ""), obj)
        else:
            return obj

    def get(self, key, default=None):
        """ 支持通过点号路径访问嵌套字段，如 'llm.model' """
        parts = key.split(".")
        val = self.config
        for part in parts:
            if isinstance(val, dict) and part in val:
                val = val[part]
            else:
                return default
        return val

    def get_path(self, key, default=None):
        """专门用于获取路径类配置，返回以项目根目录为基准的绝对路径"""
        rel_path = self.get(key, default)
        if rel_path is None:
            return None
        return os.path.join(self.project_root, rel_path)