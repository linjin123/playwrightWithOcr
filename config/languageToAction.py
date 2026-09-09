import re

def parse_nl_to_actions(nl_text):
    actions = []
    # 规则示例
    # 点击xxx按钮 -> find_and_click("xxx.png")
    scroll_pattern = r"(.+?)滚动"
    click_pattern = r"点击(.+?)(?:按钮|图标|链接|$)"
    input_pattern = r"输入(.+?)为(.+?)结束"

    # 提取点击
    clicks = re.findall(click_pattern, nl_text)
    for target in clicks:
        target = target.strip().replace(" ", "_")
        actions.append({"click", target})

    # 提取输入（简化处理，需配合点击输入框的动作）
    inputs = re.findall(input_pattern, nl_text)
    if inputs:
        # 假设输入前需要点击对应的输入框，由额外规则匹配
        actions.append({f"input|{inputs[0]}", inputs[1]})
    return actions

# 测试
nl = "点击登录按钮，然后输入用户名为 admin，密码 123456，最后点击提交"
# print(parse_nl_to_actions(nl))
# 输出: [('click', '登录'), ('input', 'admin')]


def parse_nl_to_actions_scan(nl_text):
    actions = []
    pos = 0
    length = len(nl_text)
    # 动作模式： (正则, 处理函数)，(?:按钮|图标|链接)?非捕获组，最后？表示前面(?:按钮|图标|链接)可以出现也可以不出现
    patterns = [
        (r'点击(.+?)(?=按钮|图标|链接|,)', 'click'),
        (r'输入(用户名|账号|密码|内容)为\s*(.+?)(?=，|,|结束)', 'input'),
        (r'等待(\d+)(?:秒|秒钟|s)', 'wait'),
    ]
    while pos < length:
        matched = False
        for pattern, action_type in patterns:
            m = re.compile(pattern).search(nl_text, pos)
            if m and m.start() == pos:  # 必须从当前位置开始匹配
                if action_type == 'click':
                    target = m.group(1).strip()
                    actions.append(('click', target))
                elif action_type == 'input':
                    #group根据pattern（）分组
                    field = m.group(1)
                    value = m.group(2).strip()
                    actions.append(('input', field, value))
                elif action_type == 'wait':
                    seconds = int(m.group(1))
                    actions.append(('wait', seconds))
                pos = m.end()
                matched = True
                break
        if not matched:
            # 无法匹配时跳到下一个字符（防止死循环）
            pos += 1
    return actions
if __name__ == '__main__':

    # parse_nl_to_actions_scan(input("请输入需要执行的指令："))
    # word = input("请输入需要执行的指令：")
    print(parse_nl_to_actions_scan("点击登录按钮，然后输入用户名为 admin，输入密码为 123456，最后点击提交按钮"))
