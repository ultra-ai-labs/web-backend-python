import json
import os
import re

import pandas as pd

import config


def convert_analysis_to_xlsx(file_path):
    # 读取CSV文件
    df = pd.read_csv(file_path)

    # 创建新列
    df['内容链接'] = "https://www.douyin.com/discover?modal_id=" + df['aweme_id'].astype(str)
    df['用户链接'] = "https://www.douyin.com/user/" + df['sec_uid']

    # 过滤留学意向为'是'的用户
    filtered_df = df[df['留学意向'] == '是']

    # 重命名列
    filtered_df.rename(columns={
        '内容链接': '内容链接',
        '用户链接': '用户链接',
        'nickname': '用户昵称',
        'ip_location': 'IP地址',
        'user_signature': '用户签名',
        'create_time': '评论时间',
        'content': '评论内容',
        '留学意向': '留学意向',
        '分析理由': '分析理由'
    }, inplace=True)

    # 转换评论时间格式
    filtered_df['评论时间'] = pd.to_datetime(filtered_df['评论时间'], unit='s').dt.strftime('%Y-%m-%d')

    # 选择所需列
    final_df = filtered_df[
        ['内容链接', '用户链接', '用户昵称', 'IP地址', '用户签名', '评论时间', '评论内容', '留学意向', '分析理由']]

    # 保存为Excel文件
    new_file_path = file_path.replace('.csv', '.xlsx')
    final_df.to_excel(new_file_path, index=False)
    return new_file_path

# 这个函数用于仅处理csv转换成xlsx，并不包括筛选某列效果
def convert_analysis_to_xlsx2(file_path, output_fields):
    # 读取CSV文件
    df = pd.read_csv(file_path)

    # 创建新列
    df['内容链接'] = "https://www.douyin.com/discover?modal_id=" + df['aweme_id'].astype(str)
    df['用户链接'] = "https://www.douyin.com/user/" + df['sec_uid']

    filtered_df = df

    # 重命名列
    rename_dict = {
        '内容链接': '内容链接',
        '用户链接': '用户链接',
        'nickname': '用户昵称',
        'ip_location': 'IP地址',
        'user_signature': '用户签名',
        'create_time': '评论时间',
        'content': '评论内容',
    }

    # 重命名 output_fields 中的列
    for field in output_fields:
        if field.key in df.columns:
            rename_dict[field.key] = field.key

    filtered_df.rename(columns=rename_dict, inplace=True)

    final_columns = ['内容链接', '用户链接', '用户昵称', 'IP地址', '用户签名', '评论时间', '评论内容']
    final_columns.extend([field.key for field in output_fields])

    # 转换评论时间格式（假设 create_time 字段存在）
    if '评论时间' in filtered_df.columns:
        # 调试：打印出该列的前几行以检查数据
        print(filtered_df['评论时间'].head())

        # 处理缺失或无效数据
        filtered_df['评论时间'] = pd.to_datetime(filtered_df['评论时间'], errors='coerce', format='%Y-%m-%d')
        if filtered_df['评论时间'].isnull().any():
            print("警告：某些时间戳无法转换，将设置为 NaT")

        filtered_df['评论时间'] = filtered_df['评论时间'].dt.strftime('%Y-%m-%d')

        # 创建最终的 DataFrame
    final_df = filtered_df[final_columns]

    # 保存为Excel文件
    new_file_path = file_path.replace('.csv', '.xlsx')
    final_df.to_excel(new_file_path, index=False)
    return new_file_path

def extract_keywords_and_platform(file_path):
    file_name = os.path.basename(file_path)
    match = re.match(r'(.*?)-(.*?)-(.*?)-.*', file_name)
    if match:
        keyword = match.group(2)
        platform = match.group(3)
        return keyword, platform
    else:
        raise ValueError("Filename format is incorrect. Expected format: {keyword}_{platform}_...")

def extract_keywords_from_file_path(file_path):
    # 使用正则表达式匹配关键词
    match = re.search(r'[^/]+-([^/]+)-抖音-\d{4}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2}\.csv$', file_path)
    if match:
        return match.group(1)
    return config.KEYWORDS

class OutputField:
    def __init__(self, key, explanation):
        self.key = key
        self.explanation = explanation

test_file_path = "D:/Coding/Zgent/MediaCrawler/test/分析-植发-抖音-2024-07-02-19-08-57-463300043097636864(1).csv"
# test_file_path = "C:/Users/Lenovo/Desktop/数据分析/分析-祛痘-抖音-2024-07-09-19-41-51-465845035921965056.csv"
output_fields = [
    OutputField(key='植发意向', explanation='表示是否为有植发意向的潜在用户（是、否、不确定）'),
    OutputField(key='分析理由', explanation='提供简短的分析理由不超过50字')
]

# output_fields = [{'key': '祛痘意向', 'explanation': '表示是否为有祛痘意向的潜在用户（是、否、不确定）'}, {'key': '分析理由', 'explanation': '提供简短的分析理由不超过50字'}]

# convert_analysis_to_xlsx2(test_file_path, output_fields)

# test_file_path = "D:/Coding/Zgent\MediaCrawler/test/分析-植发-抖音-2024-07-02-19-08-57-463300043097636864(1).csv"
# output_fields = [{'key': '植发意向', 'explanation': '表示是否为有植发意向的潜在用户（是、否、不确定）'}, {'key': '分析理由', 'explanation': '提供简短的分析理由不超过50字'}]


# convert_analysis_to_xlsx2(test_file_path, output_fields)