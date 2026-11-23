from dataclasses import dataclass



@dataclass
class AgentContext:
    agent_user_id: int  # agent 用户ID
    saleor_user_id: str  # saleor 用户ID
    role: str  # 用户权限