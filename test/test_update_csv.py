import pandas as pd
from datetime import datetime
import os

# 定义文件名和路径
file_path = "458286943634063360_detail_comments_2024-06-18.csv"
# desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
# file_path = os.path.join(desktop_path, file_name)

# 读取CSV文件
df = pd.read_csv(file_path, encoding='utf-8-sig', on_bad_lines='skip')

# 筛选出留学意向为'是'的用户
filtered_df = df

# 创建用户链接列
filtered_df['用户链接'] = 'https://www.douyin.com/user/' + filtered_df['sec_uid']
# 创建内容链接列
filtered_df['内容链接'] = 'https://www.douyin.com/discover?modal_id=' + filtered_df['aweme_id']

# 定义安全的日期解析函数
def safe_date_parse(date_str):
    try:
        return datetime.fromtimestamp(int(date_str)).strftime('%Y-%m-%d')
    except (ValueError, OverflowError):
        return '无效日期'

# 格式化评论时间
filtered_df['评论时间'] = filtered_df['create_time'].apply(safe_date_parse)


# 筛选并重命名所需的列，并调整列顺序
output_df = filtered_df[
    ['内容链接', '用户链接', 'nickname', 'ip_location', '评论时间', 'content']
]
output_df.columns = ['内容链接', '用户链接', '用户昵称', 'IP地址', '评论时间', '评论内容']

# 获取行数
row_count = output_df.shape[0]

# 生成带行数和时间戳的文件名并保存为Excel文件
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
backup_file_name = f"{row_count}_{timestamp}.xlsx"
output_file_path = os.path.join(".", backup_file_name)
output_df.to_excel(output_file_path, index=False)

print(f"共筛选出 {row_count} 条线索，已保存到: {output_file_path}")