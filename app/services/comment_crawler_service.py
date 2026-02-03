import asyncio
import os
import threading
from datetime import datetime, timedelta
import time

import bcrypt
from flask import Flask, copy_current_request_context, current_app
import jwt
import config
import db
from app.constants import TaskStepStatus, TaskStepType
from app.model import DouyinAwemeComment, BilibiliVideoComment, XhsNoteComment, KuaishouVideoComment
from app.repo.task_repo import TaskRepo
from app.repo.task_step_repo import TaskStepRepo
from base.base_crawler import AbstractCrawler
from media_platform.bilibili import BilibiliCrawler
from media_platform.douyin import DouYinCrawler
from media_platform.kuaishou import KuaishouCrawler
from media_platform.weibo import WeiboCrawler
from media_platform.xhs import XiaoHongShuCrawler

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
JWT_EXPIRATION_DELTA = timedelta(days=90)


class CrawlerFactory:
    CRAWLERS = {
        "xhs": XiaoHongShuCrawler,
        "dy": DouYinCrawler,
        "ks": KuaishouCrawler,
        "bili": BilibiliCrawler,
        "wb": WeiboCrawler
    }

    @staticmethod
    def create_crawler(platform: str) -> AbstractCrawler:
        crawler_class = CrawlerFactory.CRAWLERS.get(platform)
        if not crawler_class:
            raise ValueError("Invalid Media Platform Currently only supported xhs or dy or ks or bili ...")
        return crawler_class()

class CommentCrawlerService:
    @staticmethod
    def get_comment_model_by_platform(platform):
        if platform == 'dy':
            return DouyinAwemeComment
        elif platform == 'bili':
            return BilibiliVideoComment
        elif platform == 'xhs':
            return XhsNoteComment
        elif platform == 'ks':
            return KuaishouVideoComment
        else:
            return ValueError(f"Unsupported platform: {platform}")

    @staticmethod
    async def run_crawler(task_id, user_id, platform, lt, crawler_type, start_page, keyword, id_list, task_step_service,
                          douyin_comment_repo, xhs_comment_repo):
        if config.SAVE_DATA_OPTION == "db":
            await db.init_db()

        crawler = CrawlerFactory.create_crawler(platform=platform)
        crawler.ninit_config(
            platform=platform,
            login_type=lt,
            crawler_type=crawler_type,
            start_page=start_page,
            keyword=keyword,
            task_id=task_id,
            user_id=user_id
        )
        task_step_service.update_task_step_status(task_id, TaskStepType.CRAWLER, TaskStepStatus.RUNNING)

        stop_event = threading.Event()

        @copy_current_request_context
        def update_progress_thread(task_id, platform, task_step_service):
            while not stop_event.is_set():
                with current_app.app_context():
                    if platform == "dy":
                        n_comments = douyin_comment_repo.get_comments_by_task_id(task_id)
                    else:
                        n_comments = xhs_comment_repo.get_comments_by_task_id(task_id)

                    completed_count = len(n_comments)
                    task_step_service.update_task_step_status(
                        task_id, TaskStepType.CRAWLER, TaskStepStatus.RUNNING, completed_count
                    )
                    time.sleep(1)

            # Ensure final update after stop_event is set
            with current_app.app_context():
                if platform == "dy":
                    n_comments = douyin_comment_repo.get_comments_by_task_id(task_id)
                else:
                    n_comments = xhs_comment_repo.get_comments_by_task_id(task_id)

                completed_count = len(n_comments)
                task_step_service.update_task_step_status(
                    task_id, TaskStepType.CRAWLER, TaskStepStatus.RUNNING, completed_count
                )

        progress_thread = threading.Thread(
            target=update_progress_thread, args=(task_id, platform, task_step_service)
        )
        progress_thread.start()

        try:
            utils.logger.info(f"[run_crawler] Starting crawler for task {task_id}, platform: {platform}")
            await crawler.nstart(id_list=id_list)
        except Exception as e:
            utils.logger.error(f"[run_crawler] Crawler failed for task {task_id}: {e}", exc_info=True)
            # Signal the progress thread to stop
            stop_event.set()
            progress_thread.join()
            task_step_service.update_task_step_status(task_id, TaskStepType.CRAWLER, TaskStepStatus.FINISH)

            if config.SAVE_DATA_OPTION == "db":
                await db.close()
            return
        stop_event.set()
        progress_thread.join()
        task_step_service.update_task_step_status(task_id, TaskStepType.CRAWLER, TaskStepStatus.FINISH)

        if config.SAVE_DATA_OPTION == "db":
            await db.close()


    @staticmethod
    def run_crawler_in_thread(task_id, user_id, platform, lt, crawler_type, start_page, keyword, id_list, task_step_service, douyin_comment_repo, xhs_comment_repo):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        # Use app_context to properly access Flask elements
        loop.run_until_complete(CommentCrawlerService.run_crawler(task_id, user_id, platform, lt, crawler_type, start_page, keyword, id_list, task_step_service, douyin_comment_repo, xhs_comment_repo))


    @staticmethod
    def generate_password_hash(password):
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        print(hashed_password)
        return hashed_password

    @staticmethod
    def generate_token(user_id):
        payload = {
            'userid': user_id,
            'exp': datetime.utcnow() + JWT_EXPIRATION_DELTA
        }
        token = jwt.encode(payload, JWT_SECRET_KEY, algorithm='HS256')
        bearer_token = f"Bearer {token}"
        return bearer_token

    @staticmethod
    def check_password_hash(password, hashed_password):
        return bcrypt.checkpw(password.encode('utf-8'), hashed_password)




