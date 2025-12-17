# 深度求索
from openai import OpenAI


def handle_deepseek(messages):
    model = "deepseek-chat"

    client = OpenAI(api_key="sk-6a91a7a0009548a5a53990ddb76b28d8",
                    base_url="https://api.deepseek.com/")
    # 针对OpenAI GPT-4的处理逻辑
    return client.chat.completions.create(
        model=model,
        messages=messages,
    )

def create_prompt(comment, ip_location, user_signature, nickname):
    prompt = f"""
    评论：{comment}
    用户昵称：{nickname}
    用户签名：{user_signature}
    IP地址位置：{ip_location}
    """
    return prompt

output_fields = {"留学意向": "表示是否为有留学意向的潜在用户（是、否、不确定）", "分析理由": "提供简短的分析理由不超过50字"}
# 修改此行代码以正确遍历字典的键和值
output_fields_str = "\n".join([f"{key}: {value}" for key, value in output_fields.items()])
# output_fields_str = "\n".join([f"{field.key}: {field.explanation}" for field in output_fields])

system_prompt = f"""
    #背景
    现在需要帮一个白俄罗斯留学机构来分析用户在抖音上介绍白俄罗斯留学的视频下面的评论，判断这个用户是否可以成为留学机构的客户

    #任务
    结合上面背景信息，基于提供的用户评论与该用户的信息，分析该用户是否为潜在客户

    # 结果
    请输出一个包含以下键的JSON对象：
    {output_fields_str}
    """

user_prompt = create_prompt("老乡啊，我现在白俄留学呢", "广东", "无", "十月野")

messages = [ {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}]

response = handle_deepseek(messages)
print(response)
