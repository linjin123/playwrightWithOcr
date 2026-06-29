# config.py
# 数据库配置
import os
import redis

URL = "https://example.com/login"  # 替换为实际地址
DATABASE_URL = "sqlite:///app.db"
# API密钥
API_KEY = "your-api-key"
# 调试模式
DEBUG = True
# 路径配置 os.path.dirname上一级
script_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(script_dir)
TEMPLATE_PATH = os.path.join(root_dir, "modelPage","fujian.png")
def redis():


    # 默认连接本地 Redis（host=localhost, port=6379, db=0）
    r = redis.Redis()

    # 带密码和远程地址
    r = redis.Redis(
        host='127.0.0.1',
        port=6379,
        password='your_password',
        db=0,
        decode_responses=True  # 自动将返回的 bytes 转为 str
    )
    return r

if __name__ == "__main__":
    print(f"路径1: %d",root_dir)

    print(f"路径2: %d", TEMPLATE_PATH)
