# 临时写一个脚本测试
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, args=["--ignore-certificate-errors"])
    context = browser.new_context(ignore_https_errors=True)
    page = context.new_page()
    page.goto("https://10.235.2.96:31080")

    # 这里你手动在弹出的浏览器里输入账号密码登录成功
    input("请在浏览器中手动登录成功，然后回到这里按回车...")

    # 登录成功后，打印出此时所有的 localStorage
    print("当前的 LocalStorage 是：")
    print(page.evaluate("JSON.stringify(localStorage, null, 2)"))

    # 把它保存成完美的状态文件
    context.storage_state(path="auth_state_manual.json")
    browser.close()