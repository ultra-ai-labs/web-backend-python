import rpa as r
import os
import platform
import pandas as pd
import pyperclip
import time

# 获取桌面路径和Excel文件路径
# desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')
# excel_file = os.path.join(".", '986.xlsx')
excel_file = "./分析-白俄留学-抖音-2024-07-01-17-40-27-462915380218822656.xlsx"

# tagui_path = r'D:\\TagUI_Windows'
# os.environ['tagui_path'] = tagui_path
# r.tagui_location(tagui_path)
# os.environ['http_proxy'] = 'http://127.0.0.1:7890'
# os.environ['https_proxy'] = 'http://127.0.0.1:7890'
# 设置TagUI的安装路径为项目目录下的tagui文件夹（假设TagUI放在项目目录的tagui文件夹下）
tagui_path = r'C:/Users/Eric/PycharmProjects/MediaCrawler/tagui'
# tagui_path = os.environ.get('tagui_location')
# print(tagui_path)
# 设置环境变量
os.environ['tagui_location'] = tagui_path
r.tagui_location(tagui_path)

# 初始化RPA并启用视觉自动化
print("Initializing RPA...")
# 初始化RPA并启用视觉自动化
r.init(visual_automation=True)
print("RPA initialized.")

# if not r.status():
#     raise Exception("RPA initialization failed.")

print("test1")

# 读取Excel文件
df = pd.read_excel(excel_file, sheet_name='Sheet1')
user_link_column = '用户链接'
status_column = '私信结果'

# 确保所有字符串列使用UTF-8编码
for column in df.select_dtypes(include=[object]).columns:
    df[column] = df[column].apply(lambda x: x.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore') if isinstance(x, str) else x)


# 如果没有“私信结果”列，添加该列并初始化为字符串类型
if status_column not in df.columns:
    df[status_column] = ''
else:
    # 将“私信结果”列转换为字符串类型
    df[status_column] = df[status_column].astype(str)

# 过滤未私信、未标记异常以及未标记为“私信失败”的用户
df_to_message = df[(df[status_column] != '已私信') &
                   (df[status_column] != '用户不存在') &
                   (df[status_column] != '私信失败')]

# 私信内容
# message_text = """
# 同学您好！
#
# 我是广州中山大学新华学院国际教育学院的招生办老师。我们学院今年推出了与俄罗斯、白俄罗斯顶尖大学合作的本科项目。参与项目可以获得 QS 排名 78 的莫斯科国立大学和 QS 排名 288 的白俄罗斯国立大学的文凭，且都经过中国留学服务中心认证。
#
# 我们的项目只需每年学费 2.98 万元，宿舍费 2980 元，无其他额外费用（如申请费、推荐费、文书费等）。特别值得一提的是，我们采用国外面试笔试制度，不侧重高考分数。
#
# 如果您对继续升学并获得国际文凭感兴趣，请私信我了解详细内容和获取招生简章！
#
# 期待您的回复！
# """
message_text = """你好！
"""

print(message_text)

# 将私信内容复制到剪贴板
# pyperclip.copy(message_text)
pyperclip.copy(message_text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore'))

# 定义一个函数用于粘贴内容
def paste_text():
    if platform.system() == 'Darwin':  # macOS
        r.keyboard('[cmd]v')
    else:  # Windows or others
        r.keyboard('[ctrl]v')

# 确保用户链接列存在
if user_link_column not in df.columns:
    print(f"Excel文件中未找到列: {user_link_column}")
else:
    total_users = len(df_to_message)
    success_count = 0

    # 将浏览器窗口最大化
    r.keyboard('[alt][space]')
    time.sleep(0.5)
    r.keyboard('x')
    time.sleep(2)  # 等待窗口最大化

    # 遍历每一行并发送私信
    for index, row in df_to_message.iterrows():
        user_link = row[user_link_column]

        # 打开抖音用户页面
        r.url(user_link)
        print(user_link)

        # 移动焦点到页面上的一个不可见元素以避免地址栏被选中
        # 点击页面中的空白区域以绕过地址栏选中
        # r.dom('document.body.click();')
        # 点击页面中的空白区域以绕过地址栏选中
        r.click(100, 100)

        # 检查用户是否存在
        user_not_exist_selector = '//div[contains(@class, "FV0BvoOn") and text()="用户不存在"]'
        if r.exist(user_not_exist_selector):
            df.at[row.name, status_column] = '用户不存在'
            df.to_excel(excel_file, sheet_name='Sheet1', index=False)
            print(f"用户不存在: {user_link}")
            continue

        # 检查是否已关注
        follow_button_selector = '//button[@data-e2e="user-info-follow-btn"]//span[text()="已关注"]'
        if r.exist(follow_button_selector):
            df.at[row.name, status_column] = '已私信'
            df.to_excel(excel_file, sheet_name='Sheet1', index=False)
            print(f"用户已关注，跳过私信: {user_link}")
            continue

        # # 使用鼠标点击坐标来操作
        # button_x = 1255  # 替换为实际的x坐标
        # button_y = 315  # 替换为实际的y坐标
        # r.hover(button_x, button_y)
        # r.dclick(button_x, button_y)
        # print("点击私信按钮")

        # 使用DOM操作来点击私信按钮
        message_button_selector = '#douyin-right-container > div.parent-route-container.route-scroll-container.h5AVrOfS > div > div > div > div.o1w0tvbC.F3jJ1P9_.InbPGkRv > div.SwoeMAEU.nWLhWdOv > div.ty_H89Vr > button.semi-button.semi-button-secondary.RH8TCnaE.z0c5Gipx.I4tJiW0Q'
        r.dom(f'document.querySelector("{message_button_selector}").click()')
        print("点击私信按钮")



        # 确保对话框元素出现
        dialog_selector = '//span[contains(text(), "退出会话")]'
        follow_button_selector = '//div[contains(@class, "SHV6n6VV") and text()="关注"]'
        timeout = 30  # 设置超时时间为30秒
        start_time = time.time()

        while not r.exist(dialog_selector):
            if time.time() - start_time > timeout:
                print("等待对话框出现超时")
                break
            # r.click(button_x, button_y)
            r.dom(f'document.querySelector("{message_button_selector}").click()')
            print("再次点击私信按钮")

        # 检查页面上是否有关注按钮
        # if r.exist(follow_button_selector):
        #     r.hover(1220, 225)
        #     r.click(1220, 225)
        #     print("点击关注按钮")

        if r.exist(follow_button_selector):
            # follow_button_dom_selector = "#douyin-right-container > div.parent-route-container.route-scroll-container.h5AVrOfS > div > div > div > div.o1w0tvbC.F3jJ1P9_.InbPGkRv > div.SwoeMAEU.nWLhWdOv > div.ty_H89Vr > button.semi-button.semi-button-primary.ajC8cNxV.I4tJiW0Q"
            follow_button_dom_selector = "#island_b69f5 > div > ul:nth-child(6) > div > li > div > div > div._KdFHyuW.qUPEUtT4 > div > div > div.D1sCEUWq.ojRAo7V9 > div > div.azu4pICV > div.SHV6n6VV"
            r.dom(f'document.querySelector("{follow_button_dom_selector}").click()')
            print("点击关注按钮")

        # 查找输入框并粘贴内容
        input_box_selector = '//div[@data-offset-key]'
        if r.exist(input_box_selector):
            # r.hover(input_box_selector)
            # r.click(input_box_selector)
            input_box_dom_selector = "#island_b69f5 > div > ul:nth-child(6) > div > li > div > div > div._KdFHyuW.qUPEUtT4 > div > div > div.D1sCEUWq.ojRAo7V9 > div > div.c8uBfaOs > div > div > div.IaCaREVo > div.MgaCB9du > div > div > div.DraftEditor-editorContainer > div > div > div > div"
            r.dom(f'document.querySelector("{input_box_dom_selector}").focus()')

            # 粘贴内容
            paste_text()
            print("粘贴内容")

            # 发送回车键
            r.keyboard('[enter]')
            print("发送消息")

            # # 发送消息后移动鼠标
            # r.hover(1220, 700)
            # print("移动鼠标到 (1220, 700)")

            # 检查是否由于隐私设置无法发送消息
            privacy_error_selector = '//div[contains(@class, "hI145Goj") and text()="由于对方的隐私设置，你无法发送消息"]'
            if r.exist(privacy_error_selector):
                df.at[row.name, status_column] = '私信失败'
                df.to_excel(excel_file, sheet_name='Sheet1', index=False)
                print(f"由于对方的隐私设置，无法发送消息: {user_link}")
                continue

            # 更新数据框中的“私信结果”列
            df.at[row.name, status_column] = '已私信'
            success_count += 1
            percent_complete = (success_count / total_users) * 100
            print(f"已私信{success_count}个，共{total_users}个，完成{percent_complete:.2f}%")

            # 保存更新后的Excel文件
            df.to_excel(excel_file, sheet_name='Sheet1', index=False)

        else:
            print("未找到输入框")

    print("所有私信完成")