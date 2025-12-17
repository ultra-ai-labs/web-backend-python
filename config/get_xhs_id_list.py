import os

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

options = Options()
user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36"
options.add_argument(f'user-agent={user_agent}')



# 读取Excel文件
# def read_excel(file_path):
#     df = pd.read_excel(file_path, usecols=[0])  # 假设URLs在第一列
#     return df.iloc[1:, 0].tolist()
# 读取文件（支持xlsx和csv）
def read_file(file_path):
    if file_path.endswith('.xlsx'):
        df = pd.read_excel(file_path, usecols=[0])  # 假设URLs在第一列
    elif file_path.endswith('.csv'):
        df = pd.read_csv(file_path, usecols=[0])  # 假设URLs在第一列
    else:
        print("Unsupported file format.")
        return []
    return df.iloc[1:, 0].tolist()


# 配置Selenium WebDriver
def setup_driver():
    driver = webdriver.Chrome(options=options)  # 更新为实际路径
    current_file_dir = os.path.dirname(__file__)
    resource_path = os.path.join(current_file_dir, "./p.js")
    magic_js = open(resource_path, "r").read()
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {"source": magic_js})
    return driver

# 提取URL中的ID
def extract_id_from_url(url):
    return url.split('/')[-1].split('?')[0]

# 将ID列表写入Python文件
def write_ids_to_py_file(id_list, output_file='./xhs_config.py'):
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# 指定小红书需要爬虫的笔记ID列表\n")
        f.write("XHS_SPECIFIED_ID_LIST = [\n")
        for id in id_list:
            f.write(f'"{id}",\n')
        f.write("]\n")

def get_xhs_ids_by_filepath(file_path):
    urls = read_file(file_path)
    ids = []
    for url in urls:
        id = extract_id_from_url(url)
        ids.append(id)
    print(ids)
    return ids

# 主函数
def main():
    file_path = '小红书冰箱的评论区链接.xlsx'  # 更新为实际Excel文件路径
    urls = read_file(file_path)
    driver = setup_driver()

    ids = []
    for url in urls:
        driver.get(url)
        time.sleep(10)  # 等待页面加载
        final_url = driver.current_url  # 获取导航后的URL
        id = extract_id_from_url(final_url)
        ids.append(id)

    driver.quit()  # 关闭浏览器
    write_ids_to_py_file(ids, 'xhs_config.py')  # 输出到指定的文件

if __name__ == "__main__":
    main()