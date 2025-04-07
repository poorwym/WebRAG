import os
import json
from datetime import datetime
from typing import List, Dict, Optional, Union
import uuid

class ConversationsManager:
    def __init__(self, conversations_dir=None):
        # 自动定位项目根目录
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # src/conversation/ --> src/ --> 根目录
        default_dir = os.path.join(project_root, "data", "conversations")

        # 使用传入路径或默认路径
        self.conversations_dir = os.path.abspath(conversations_dir) if conversations_dir else default_dir

        self.conversations: Dict[str, Dict] = {}
        self._ensure_conversations_dir()
        self.load_conversations()

    def _ensure_conversations_dir(self):
        """确保对话目录存在"""
        try:
            os.makedirs(self.conversations_dir, exist_ok=True)
            print(f"对话目录已创建: {self.conversations_dir}")
        except Exception as e:
            raise RuntimeError(f"无法创建对话目录 {self.conversations_dir}: {str(e)}")

    def load_conversations(self):
        """加载所有对话"""
        self.conversations.clear()
        try:
            for filename in os.listdir(self.conversations_dir): 
                if filename.endswith('.json'):
                    file_path = os.path.join(self.conversations_dir, filename)
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            for conv in data.get('conversations', []):
                                self.conversations[conv['id']] = conv
                    except json.JSONDecodeError as e:
                        print(f"警告：无法解析文件 {file_path}: {str(e)}")
                    except Exception as e:
                        print(f"警告：读取文件 {file_path} 时出错: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"加载对话时出错: {str(e)}")

    def save_conversation(self, conversation: Dict):
        """保存单个对话到内存和文件"""
        try:
            temp_file = None
            # 确保对话有ID
            if not conversation.get('id'):
                conversation['id'] = f"conv_{len(self.conversations) + 1:03d}"
            
            # 确保对话有创建时间
            if not conversation.get('created_at'):
                conversation['created_at'] = datetime.now().isoformat()
            
            # 更新内存中的对话
            conversation_id = conversation['id']
            self.conversations[conversation_id] = conversation
            
            # 保存到文件
            file_path = os.path.join(self.conversations_dir, f"{conversation_id}.json")
            temp_file = file_path + '.tmp'
            
            # 先写入临时文件
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump({"conversations": [conversation]}, f, ensure_ascii=False, indent=2)
            
            # 如果写入成功，重命名为正式文件
            os.replace(temp_file, file_path)
            return conversation_id
            
        except Exception as e:
            # 清理临时文件
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)
            raise RuntimeError(f"保存对话时出错: {str(e)}")

    def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """获取指定ID的对话"""
        return self.conversations.get(conversation_id)

    def delete_conversation(self, conversation_id: str) -> bool:
        """删除指定ID的对话"""
        try:
            if conversation_id in self.conversations:
                file_path = os.path.join(self.conversations_dir, f"{conversation_id}.json")
                if os.path.exists(file_path):
                    os.remove(file_path)
                del self.conversations[conversation_id]
                return True
            return False
        except Exception as e:
            raise RuntimeError(f"删除对话时出错: {str(e)}")

    def get_all_conversations(self) -> List[Dict]:
        """获取所有对话"""
        return list(self.conversations.values())

    def get_conversation_by_title(self, title: str) -> List[Dict]:
        """根据标题搜索对话"""
        return [conv for conv in self.conversations.values() 
                if title.lower() in conv.get('title', '').lower()]

    def get_conversation_by_date(self, date: str) -> List[Dict]:
        """根据日期搜索对话"""
        target_date = datetime.fromisoformat(date).date()
        return [conv for conv in self.conversations.values() 
                if datetime.fromisoformat(conv['created_at']).date() == target_date]

    def get_conversation_by_range(self, start_date: str, end_date: str) -> List[Dict]:
        """根据日期范围搜索对话"""
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()
        return [conv for conv in self.conversations.values() 
                if start <= datetime.fromisoformat(conv['created_at']).date() <= end]

    def get_conversation_by_user_query(self, user_query: str) -> List[Dict]:
        """根据用户查询内容搜索对话"""
        results = []
        for conv in self.conversations.values():
            for msg in conv.get('messages', []):
                if msg['role'] == 'user' and user_query.lower() in msg['content'].lower():
                    results.append(conv)
                    break
        return results
    
    def create_new_conversation(self, title: str = None) -> str:
        """创建新对话并返回对话ID"""
        conversation_id = f"conv_{str(uuid.uuid4())}"
        new_conversation = {
            "id": conversation_id,
            "title": title or f"新对话 {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "created_at": datetime.now().isoformat(),
            "messages": []
        }
        # 保存新对话（同时更新内存和文件）
        return self.save_conversation(new_conversation)
    
    def update_conversation(self, conversation_id: str, updates: Dict) -> bool:
        """更新指定ID的对话并保存"""
        if conversation_id in self.conversations:
            current_conversation = self.conversations[conversation_id].copy()
            current_conversation.update(updates)
            self.save_conversation(current_conversation)
            return True
        else:
            raise ValueError(f"对话ID {conversation_id} 不存在")
    
    def add_message_to_conversation(self, conversation_id: str, role: str, content: str) -> bool:
        """向对话添加新消息并保存"""
        if conversation_id not in self.conversations:
            raise ValueError(f"对话ID {conversation_id} 不存在")
            
        conversation = self.conversations[conversation_id].copy()
        if 'messages' not in conversation:
            conversation['messages'] = []
            
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        
        conversation['messages'].append(message)
        self.save_conversation(conversation)
        return True
    
    def change_conversation_title_by_id(self, conversation_id: str, title: str) -> bool:
        """根据ID更新对话标题"""
        if conversation_id in self.conversations:
            self.conversations[conversation_id]['title'] = title
            self.save_conversation(self.conversations[conversation_id])
            return True
        return False
    
    

