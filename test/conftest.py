import os
import pickle
import cv2
import pytest
from playwright.sync_api import sync_playwright
import glob

import config.config


@pytest.fixture(scope="session")
def playwright():
    with sync_playwright() as p:
        yield p

@pytest.fixture(scope="function")
def browser(playwright):
    # 启动浏览器（可选择 headless=False 方便调试）
    browser = playwright.chromium.launch(headless=True)
    yield browser
    browser.close()

@pytest.fixture(scope="function")
def page(browser):
    context = browser.new_context(viewport={"width": 1920, "height": 1080})
    page = context.new_page()
    yield page
    context.close()

@pytest.fixture(scope="session")
def initialize_icon(self,folder_path, extensions=('.png', '.jpg', '.jpeg', '.bmp', '.tiff')):
    for filename in os.listdir(folder_path):
        if filename.lower().endswith(extensions):
            img_path = os.path.join(folder_path, filename)
            # 读取模板图像，得到 numpy 数组
            template = cv2.imread(img_path)

             # 序列化为 bytes
            template_bytes = pickle.dumps(template)

             # 存入 Redis，key 为图标名（如 'icon_login'）
            self.redis.set(filename, template_bytes)