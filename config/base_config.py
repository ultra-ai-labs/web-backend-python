# 基础配置
import os

PLATFORM = "xhs"
KEYWORDS = "橙子网络"
LOGIN_TYPE = "qrcode"  # qrcode or phone or cookie
COOKIES = ""
SORT_TYPE = "popularity_descending"  # 具体值参见media_platform.xxx.field下的枚举值，展示只支持小红书
CRAWLER_TYPE = "search"  # 爬取类型，search(关键词搜索) | detail(帖子详情)| creator(创作者主页数据)

# 是否开启 IP 代理
ENABLE_IP_PROXY = False

# 代理IP池数量
IP_PROXY_POOL_COUNT = 2

# 代理IP提供商名称
IP_PROXY_PROVIDER_NAME = "kuaidaili"

# 设置为True不会打开浏览器（无头浏览器），设置False会打开一个浏览器（小红书如果一直扫码登录不通过，打开浏览器手动过一下滑动验证码）
HEADLESS = True

# 是否保存登录状态
SAVE_LOGIN_STATE = True

# 数据保存类型选项配置,支持三种类型：csv、db、json

SAVE_DATA_OPTION = "db"  # csv or db or json

# 用户浏览器缓存的浏览器文件配置
USER_DATA_DIR = "%s_user_data_dir"  # %s will be replaced by platform name

# 爬取开始页数 默认从第一页开始
START_PAGE = 1

# 爬取视频/帖子的数量控制
CRAWLER_MAX_NOTES_COUNT = 20

# 并发爬虫数量控制
MAX_CONCURRENCY_NUM = 4

# 是否开启爬图片模式, 默认不开启爬图片
ENABLE_GET_IMAGES = False

# 是否开启爬评论模式, 默认不开启爬评论
ENABLE_GET_COMMENTS = True

# 是否开启爬二级评论模式, 默认不开启爬二级评论, 目前仅支持 xhs
# 老版本项目使用了 db, 则需参考 schema/tables.sql line 287 增加表字段
ENABLE_GET_SUB_COMMENTS = True

# 七牛云存储配置
AccessKey = os.getenv("QINIU_ACCESS_KEY", "")
SecretKey = os.getenv("QINIU_SECRET_KEY", "")
BucketName = os.getenv("QINIU_BUCKET_NAME", "")
CDNTestDomain = os.getenv("QINIU_CDN_DOMAIN", "")

# 腾讯云存储配置
TencentSecretId = os.getenv("TENCENT_SECRET_ID", "")
TencentSecretKey = os.getenv("TENCENT_SECRET_KEY", "")
TencentBucketName = os.getenv("TENCENT_BUCKET_NAME", "")
# TencentCdnDomain = "zcloud-1256349444.cos.ap-guangzhou.myqcloud.com"
TencentRegion = os.getenv("TENCENT_REGION", "")
# TencentSecretId = "AKIDYa3eCd25FWlIgAVcZN5cw68EHKOI7264"
# TencentSecretKey = "teFh1CEFkDj9QYVNQSafDpXcfCc8nW8u"
# TencentBucketName = "zcloud-1256349444"
# TencentCdnDomain = "zcloud-1256349444.cos.ap-guangzhou.myqcloud.com"
# TencentRegion = "ap-guangzhou"

# OPENAI配置
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# DEEPSEEK 配置
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

# ANALYSIS_THREAD 分析线程数
ANALYSIS_THREAD_NUM = int(os.getenv("ANALYSIS_THREAD_NUM", 6))


# 指定小红书需要爬虫的笔记ID列表
XHS_SPECIFIED_ID_LIST = [
    "624fddd2000000000102f2f7",
    "645516cc00000000270000e3",
    "66154cab000000001b010310",
    # ........................
]

# 指定抖音需要爬取的ID列表
DY_SPECIFIED_ID_LIST = [
    "7280854932641664319",
    "7202432992642387233"
    # ........................
]

# 指定快手平台需要爬取的ID列表
KS_SPECIFIED_ID_LIST = [
    "3xf8enb8dbj6uig",
    "3x6zz972bchmvqe"
]

# 指定B站平台需要爬取的视频bvid列表
BILI_SPECIFIED_ID_LIST = [
    "BV1d54y1g7db",
    "BV1Sz4y1U77N",
    "BV14Q4y1n7jz",
    # ........................
]

# 指定微博平台需要爬取的帖子列表
WEIBO_SPECIFIED_ID_LIST = [
    "4982041758140155",
    # ........................
]

# 指定小红书创作者ID列表
XHS_CREATOR_ID_LIST = [
    "63e36c9a000000002703502b",
    # ........................
]
