import threading
import platform
import time

import pandas as pd
import pyperclip
from dotenv import load_dotenv
from flask import Flask, request, jsonify

from tools import next_id
import rpa as r


# 加载环境变量
load_dotenv()

app = Flask(__name__)


class TaskStatus:
    def __init__(self):
        self.status = "initialized"
        self.num = 0

class TaskManager:
    def __init__(self):
        self.tasks = {}

    def create_task(self, task_type, **kwargs):
        task_id = next_id()
        self.tasks[task_id] = {
            "type": task_type,
            "status": "initialized",
            "progress": 0,
            "result": None,
            "kwargs": kwargs
        }
        return task_id

    def update_task_status(self, task_id, status, progress=None):
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = status
            if progress is not None:
                self.tasks[task_id]["progress"] = progress

    def update_task_result(self, task_id, result):
        if task_id in self.tasks:
            self.tasks[task_id]["result"] = result

    def get_task_status(self, task_id):
        return self.tasks.get(task_id, {})

    def get_task_result(self, task_id):
        return self.tasks.get(task_id, {}).get("result")


task_manager = TaskManager()

@app.route('/start-marketing', methods=['POST'])
def start_market():
    data = request.get_json()
    file_path = data['file_path']
    message_text = data['message_text']
    task_id = task_manager.create_task("marketing", file_path=file_path, message_text=message_text)
    task_thread = threading.Thread(target=marketing_task, args=(task_id, file_path, message_text))
    task_thread.start()
    return jsonify({"status": "success", "task_id": task_id}), 200

def paste_text():
    if platform.system() == 'Darwin':
        r.keyboard('[cmd]v')
    else:
        r.keyboard('[ctrl]v')


def marketing_task(task_id, file_path, message_text):
    r.init(visual_automation=True)

    df = pd.read_excel(file_path, sheet_name='Sheet1')
    user_link_column = '用户链接'
    status_column = '私信结果'
    task_manager.update_task_status(task_id, "running")

    for column in df.select_dtypes(include=[object]).columns:
        df[column] = df[column].apply(
            lambda x: x.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore') if isinstance(x, str) else x)

    if status_column not in df.columns:
        df[status_column] = ''
    else:
        df[status_column] = df[status_column].astype(str)

    df_to_message = df[(df[status_column] != '已私信') &
                       (df[status_column] != '用户不存在') &
                       (df[status_column] != '私信失败')]

    pyperclip.copy(message_text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore'))

    total_users = len(df_to_message)
    success_count = 0

    for index, row in df_to_message.iterrows():
        user_link = row[user_link_column]
        r.url(user_link)

        time.sleep(1)
        r.keyboard('[enter]')

        # 等待特定元素消失
        wait_selector = '#login-pannel > div.login-pannel__header > div.login-pannel__header-title'
        start_time = time.time()
        timeout = 3600
        while r.exist(wait_selector):
            if time.time() - start_time > timeout:
                print("等待登录窗口消失超时")
                break
            time.sleep(1)
            print("等待登录窗口消失")

        pyperclip.copy(message_text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore'))

        user_not_exist_selector = '//div[contains(@class, "FV0BvoOn") and text()="用户不存在"]'
        if r.exist(user_not_exist_selector):
            df.at[row.name, status_column] = '用户不存在'
            df.to_excel(file_path, sheet_name='Sheet1', index=False)
            continue

        follow_button_selector = '//button[@data-e2e="user-info-follow-btn"]//span[text()="已关注"]'
        if r.exist(follow_button_selector):
            df.at[row.name, status_column] = '已私信'
            df.to_excel(file_path, sheet_name='Sheet1', index=False)
            continue

        message_button_xpath = '//*[@id="douyin-right-container"]/div[2]/div/div/div[2]/div[3]/div[3]/div[1]/button[2]'
        n_message = f"document.evaluate('{message_button_xpath}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click()"

        r.dom(n_message)

        print("点击私信按钮")

        dialog_selector = '//span[contains(text(), "退出会话")]'
        follow_button_selector = '//div[contains(@class, "SHV6n6VV") and text()="关注"]'
        timeout = 60
        start_time = time.time()

        while not r.exist(dialog_selector):
            if time.time() - start_time > timeout:
                print("等待对话框出现超时")
                break
            r.dom(n_message)
            print("再次点击私信按钮")


        while not r.exist(follow_button_selector):
            if time.time() - start_time > timeout:
                print("等待关注按钮出现超时")
                break
            time.sleep(0.5)
            print("再次点击私信按钮")

        if r.exist(follow_button_selector):
            follow_button_dom_selector = "#island_b69f5 > div > ul:nth-child(6) > div > li > div > div > div._KdFHyuW.qUPEUtT4 > div > div > div.D1sCEUWq.ojRAo7V9 > div > div.azu4pICV > div.SHV6n6VV"
            r.dom(f'document.querySelector("{follow_button_dom_selector}").click()')
            print("点击关注按钮")
        input_box_selector = '//div[@data-offset-key]'
        if r.exist(input_box_selector):
            input_box_dom_selector = "#island_b69f5 > div > ul:nth-child(6) > div > li > div > div > div._KdFHyuW.qUPEUtT4 > div > div > div.D1sCEUWq.ojRAo7V9 > div > div.c8uBfaOs > div > div > div.IaCaREVo > div.MgaCB9du > div > div > div.DraftEditor-editorContainer > div > div > div > div"
            r.dom(f'document.querySelector("{input_box_dom_selector}").click()')
            paste_text()
            r.keyboard('[enter]')

            privacy_error_selector = '//div[contains(@class, "hI145Goj") and text()="由于对方的隐私设置，你无法发送消息"]'
            if r.exist(privacy_error_selector):
                df.at[row.name, status_column] = '私信失败'
                df.to_excel(file_path, sheet_name='Sheet1', index=False)
                continue

            df.at[row.name, status_column] = '已私信'
            success_count += 1
            percent_complete = (success_count / total_users) * 100
            print(f"已私信{success_count}个，共{total_users}个，完成{percent_complete:.2f}%")
            # tasks[task_id]["progress"] = success_count
            task_manager.update_task_status(task_id, "running", success_count)
            df.to_excel(file_path, sheet_name='Sheet1', index=False)

    task_manager.update_task_status(task_id, "finish")
    task_manager.update_task_result(task_id, file_path)
    r.close()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001)