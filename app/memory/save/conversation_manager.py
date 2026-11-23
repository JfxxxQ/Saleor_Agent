from app.memory.save.profile_memory import ProfileMemory
from app.memory.save.window_memory import WindowMemory
from app.memory.save.long_memory import LongMemory
from app.memory.save.summary_memory import SummaryMemory
from app.memory.save.prompt_builder import PromptBuilder
"""
会话记忆管理器
"""
class ConversationManager:

    def __init__(self,history_id:int,agent_user_id:int,question:str):
        self.window_memory = WindowMemory(history_id)
        self.summary_memory = SummaryMemory()
        self.long_memory = LongMemory()
        self.profile_memory =ProfileMemory(agent_user_id)
        self.agent_user_id = agent_user_id
        self.question = question
        self.history_id = history_id

    #添加窗口记忆
    def add_window(self,role,content):
        self.window_memory.add(role,content)
    #添加提示词构造器
    def add_prompt(self):
        builder = PromptBuilder(
            self.window_memory,self.summary_memory,self.long_memory,self.profile_memory,
            self.agent_user_id,self.history_id,self.question
        )
        return builder.builder()
if __name__ == "__main__":
    c = ConversationManager(1,1,"我喜欢什么")
    rs = c.add_prompt()
    print(rs)
    c.add_window("user","你是谁")
    c.add_window("assistant","我是一个助手")