from app.memory.retrieval.long_agent import LongAgent
from app.memory.retrieval.profile_agent  import ProfileAgent
from app.memory.retrieval.summary_agent import SummaryAgent



"""
记忆管理
"""
class MemoryManager:
    def __init__(self,conversion):
        # 创建长期记忆智能体
        self.long_agent = LongAgent(conversion.long_memory)
        # 创建摘要记忆智能体
        self.summary_agent = SummaryAgent(conversion.summary_memory)
        # 创建画像记忆智能体
        self.profile_agent = ProfileAgent(conversion.profile_memory)
        #创建窗口记忆
        self.window = conversion.window_memory
        #用户id
        self.agent_user_id = conversion.agent_user_id
        #会话id
        self.history_id =conversion.history_id

     #更新所有记忆
    #三类记忆互相独立，单个失败不影响其他记忆的更新
    def update(self,question):
        #更新画像记忆
        try:
            self.profile_agent.update(question)
        except Exception as e:
            print(f"更新画像记忆出现异常:{e}")
        #更新长期记忆
        try:
            self.long_agent.update(self.agent_user_id, question)
        except Exception as e:
            print(f"更新长期记忆出现异常:{e}")
        #更新摘要记忆
        try:
            self.summary_agent.update(self.history_id,self.window.load())
        except Exception as e:
            print(f"更新摘要记忆出现异常:{e}")


