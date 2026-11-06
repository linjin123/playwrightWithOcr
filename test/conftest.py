import os
import pickle
import cv2
import pytest
from playwright.sync_api import sync_playwright
import glob

from config import config

BASE_URL = "https://10.235.2.96:31080"
API_LOGIN_URL = f"{BASE_URL}/api/admin-api/system/auth/token"
USERNAME = "Q5DaKKzhj7TAnjOLmlgNlXIckf3i7RGjTUiKJ7CiLwIieFOWAVeRYJROA9O1lBUORmk8mHQX03W9Ie2gh0zhyVOzE1UIatWYQeIC1ucTl5Tie7FFosKBQhSS/o5GQXycRcqhjGg1R+O95QR880kaUhfxg8vsOkcG7WSwR4uzk7s="
PASSWORD = "i+uaG+JozGS+USJTiR6fmo/eGktOl46He2qaKQ6NKHBEAYx5KyZNvvSAD4VV1AqQWKwWkKIdtFH+mKf7Sg22JkJsqKeL39haE8VCTSV8uGBWPJzteZlYjGhgU1zt9n7P1G/Rfx54+n7q/o5uzqRRJHq51ga3SmdoxGhYUizZOZQ="
AUTH_FILE = "auth_state.json"

@pytest.fixture(scope="session")
def playwright():
    with sync_playwright() as p:
        yield p

@pytest.fixture(scope="session")
def browser(playwright):
    # 启动浏览器（可选择 headless=False 方便调试）
    browser = playwright.chromium.launch(headless=False)
    yield browser
    browser.close()


#  Function 级 Context，复用登录态
@pytest.fixture(scope="function")
def context(browser, auth_state: str):
    """
    每个用例仍然使用全新的 Context（保证隔离），但创建时直接加载已经保存的登录态。
    这样既不需要重新请求登录接口，又保证了用例之间互不影响。
    """
    # 加载保存的 auth_state.json 文件，瞬间完成登录注入
    context = browser.new_context(storage_state=auth_state)

    # 如果你的系统是纯 Token 机制，且存在 localStorage 中，可以在这里额外注入
    # context.add_init_script("window.localStorage.setItem('token', 'xxxxx')")

    yield context
    context.close()
@pytest.fixture(scope="function")
def page(context):
    page = context.new_page()
    yield page
    page.close()


@pytest.fixture(scope="session")
def auth_state(browser):
    """
    整个测试会话只执行一次接口登录，拿到凭证并保存为文件。
    """
    # 如果已经存在保存的状态文件（且未过期），也可以直接跳过登录
    # if os.path.exists(AUTH_FILE): return AUTH_FILE

    print("\n>>> 正在执行全局前置登录...")
    context = browser.new_context(viewport={"width": 1920, "height": 1080},device_scale_factor=1,ignore_https_errors=True)

    # 请求登录接口
    response = context.request.post(API_LOGIN_URL, data={
        "username": USERNAME,
        "password": PASSWORD,
        "clientId": "iotplatform"
    })
    # assert response.ok, f"登录失败: {response.text()}"

    # 如果系统是 Token 机制（非 Cookie）
    token = response.json().get("data", {}).get("accessToken")
    assert token is not None, f"响应中未找到 accessToken，响应: {response.text()}"

        # 将当前的 Cookie、LocalStorage 等状态保存到本地文件
    context.storage_state(path=AUTH_FILE)
    context.close()
    return AUTH_FILE


@pytest.fixture(scope="session")
def initialize_icon(folder_path, extensions=('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(extensions):
            img_path = os.path.join(folder_path, filename)
            # 读取模板图像，得到 numpy 数组
            template = cv2.imread(img_path)

             # 序列化为 bytes
            template_bytes = pickle.dumps(template)

             # 存入 Redis，key 为图标名（如 'icon_login'）
            config.redis.set(filename, template_bytes)