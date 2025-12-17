from app.model import DouyinAwemeComment, XhsNoteComment
from app.repo.douyin_aweme_comment_repo import DouyinAwemeCommentRepo
from app.repo.xhs_note_comment_repo import XhsNoteCommentRepo

douyin_comment_repo = DouyinAwemeCommentRepo()
xhs_comment_repo = XhsNoteCommentRepo()

class UnifiedComment:
    def __init__(self, comment):
        self.comment_id = comment.comment_id
        self.create_time = comment.create_time
        self.ip_location = getattr(comment, 'ip_location', '')
        self.aweme_id = getattr(comment, 'aweme_id', '')
        self.note_id = getattr(comment, 'note_id', '')
        self.content = comment.content
        self.user_id = comment.user_id
        self.sec_uid = getattr(comment, 'sec_uid', '')
        self.short_user_id = getattr(comment, 'short_user_id', '')
        self.user_unique_id = getattr(comment, 'user_unique_id', '')
        self.user_signature = getattr(comment, 'user_signature', '')
        self.nickname = comment.nickname
        self.avatar = getattr(comment, 'avatar', '')
        self.sub_comment_count = comment.sub_comment_count
        self.last_modify_ts = comment.last_modify_ts

def get_comments_by_task_id(task_id, platform):
    if platform == 'dy':
        comments = douyin_comment_repo.get_comments_by_task_id(task_id)
    elif platform == 'xhs':
        comments = xhs_comment_repo.get_comments_by_task_id(task_id)
    else:
        comments = []

    unified_comments = [UnifiedComment(comment) for comment in comments]
    return unified_comments

def get_comment_by_comment_id(comment_id, platform, task_id):
    if platform == "dy":
        comment = douyin_comment_repo.get_comment_by_comment_id(comment_id, task_id)
    elif platform == "xhs":
        comment = xhs_comment_repo.get_comment_by_comment_id(comment_id, task_id)
    else:
        comment = None

    unified_comment = UnifiedComment(comment)
    return unified_comment