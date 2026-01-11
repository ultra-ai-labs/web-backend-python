from app.repo.quota_repo import QuotaRepo

quota_repo = QuotaRepo()

def check_user_quota(user_id):
    """
    检查用户的额度是否已满
    :param user_id: 用户 ID
    :return: (bool, str) -> (是否允许继续, 提示信息)
    """
    if user_id == "super_admin":
        return True, "Success"
    
    quota = quota_repo.get_quota_by_user_id(user_id)
    if not quota:
        # 如果没有额度记录，可以视业务情况而定，这里默认返回 False 或 True
        # 考虑到安全性，通常如果没有记录应该提示额度不足或初始额度为 0
        return False, "未找到额度记录，请联系管理员或前往订阅页面"
    
    if quota.used_quota >= quota.total_quota:
        return False, f"额度已用尽 ({quota.used_quota}/{quota.total_quota})，请前往订阅页面充值"
    
    return True, "Success"
