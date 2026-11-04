# config.py
# 数据库配置
import os
import redis
from redis.cluster import RedisCluster, ClusterNode

URL = "https://tieba.baidu.com/"  # 替换为实际地址
DATABASE_URL = "sqlite:///app.db"
# API密钥
API_KEY = "your-api-key"
# 调试模式
DEBUG = True
# 路径配置 os.path.dirname上一级
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
TEMPLATE_PATH = os.path.join(root_dir, "modelPage","fujian.png")
SCREENSHOTS_PATH = os.path.join(root_dir, "test","screenshots")
#redis单例
redis = redis.Redis(
    host="localhost",
    port=6379,
    db=0,
    decode_responses=True,
    max_connections=20,      # 连接池上限
)
#redis集群
# nodes = [
#     ClusterNode('172.23.1.152', 7001),
#     ClusterNode('172.23.1.153', 7001),
#     ClusterNode('172.23.1.154', 7001),
# ]
# redis = RedisCluster(startup_nodes=nodes, decode_responses=True,password="unipower123")

if __name__ == "__main__":
    print(f"路径1: %d",root_dir)

    print(f"路径2: %d", TEMPLATE_PATH)
