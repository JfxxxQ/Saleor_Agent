import redis
from dotenv import load_dotenv

#读取配置
load_dotenv()
"""
用户画像记忆，记录用户的结构化数据
"""
class ProfileMemory:

    def __init__(self,agent_user_id:int):
        self.client = redis.StrictRedis(host="localhost",port=6379,db=2)
        #设置key
        self.key = f"chat_profile:{agent_user_id}"
    #添加或者更新记忆
    def add(self,hash_key,value):
        self.client.hset(self.key,hash_key,value)
    #查询记忆
    def load(self):
        msg = self.client.hgetall(self.key)
        data=""
        for col,value in msg.items():
            data +=f"{col.decode()}:{self.client.hget(self.key,col).decode()}\n"
        return data


if __name__ =="__main__":
    p = ProfileMemory(1)
    p.add("name","张三")
    p.add("age", 40)
    p.add("job", "程序员")
    rs = p.load()
    print(rs)