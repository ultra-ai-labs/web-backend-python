# -*- coding: utf-8 -*-
# @Author  : relakkes@gmail.com
# @Time    : 2024/4/6 15:30
# @Desc    : sql接口集合

from typing import Dict, List

from db import AsyncMysqlDB
from var import media_crawler_db_var


async def query_content_by_content_id(content_id: str) -> Dict:
    """
    查询一条内容记录（xhs的帖子 ｜ 抖音的视频 ｜ 微博 ｜ 快手视频 ...）
    Args:
        content_id:

    Returns:

    """
    async_db_conn: AsyncMysqlDB = media_crawler_db_var.get()
    sql: str = f"select * from xhs_note where note_id = '{content_id}'"
    rows: List[Dict] = await async_db_conn.query(sql)
    if len(rows) > 0:
        return rows[0]
    return dict()


async def add_new_content(content_item: Dict) -> int:
    """
    新增一条内容记录（xhs的帖子 ｜ 抖音的视频 ｜ 微博 ｜ 快手视频 ...）
    Args:
        content_item:

    Returns:

    """
    async_db_conn: AsyncMysqlDB = media_crawler_db_var.get()
    last_row_id: int = await async_db_conn.item_to_table("xhs_note", content_item)
    return last_row_id


async def update_content_by_content_id(content_id: str, content_item: Dict) -> int:
    """
    更新一条记录（xhs的帖子 ｜ 抖音的视频 ｜ 微博 ｜ 快手视频 ...）
    Args:
        content_id:
        content_item:

    Returns:

    """
    async_db_conn: AsyncMysqlDB = media_crawler_db_var.get()
    effect_row: int = await async_db_conn.update_table("xhs_note", content_item, "note_id", content_id)
    return effect_row



async def query_comment_by_comment_id(comment_id: str) -> Dict:
    """
    查询一条评论内容
    Args:
        comment_id:

    Returns:

    """
    async_db_conn: AsyncMysqlDB = media_crawler_db_var.get()
    sql: str = f"select * from xhs_note_comment where comment_id = '{comment_id}'"
    rows: List[Dict] = await async_db_conn.query(sql)
    if len(rows) > 0:
        return rows[0]
    return dict()

async def n_query_comment_by_comment_id(comment_id: str, task_id: str) -> Dict:
    """
    查询一条评论内容
    Args:
        comment_id:

    Returns:

    """
    async_db_conn: AsyncMysqlDB = media_crawler_db_var.get()
    sql: str = f"select * from xhs_note_comment where comment_id = '{comment_id}' and task_id = '{task_id}'"
    rows: List[Dict] = await async_db_conn.query(sql)
    if len(rows) > 0:
        return rows[0]
    return dict()

async def check_user_owns_comment_for_task(user_id: str, comment_id: str, task_id: str) -> bool:
    """
            Check if the user owns the comment for the given task
            Args:
                user_id:
                comment_id:
                task_id:
            Returns:
                bool
        """
    async_db_conn: AsyncMysqlDB = media_crawler_db_var.get()
    sql: str = f"""
        SELECT 1 FROM xhs_note_comment
        WHERE comment_id = '{comment_id}' AND task_id = '{task_id}'
        LIMIT 1
        """
    rows: List[Dict] = await async_db_conn.query(sql)

    return len(rows) > 0

async def add_new_comment(comment_item: Dict) -> int:
    """
    新增一条评论记录
    Args:
        comment_item:

    Returns:

    """
    async_db_conn: AsyncMysqlDB = media_crawler_db_var.get()
    last_row_id: int = await async_db_conn.item_to_table("xhs_note_comment", comment_item)
    return last_row_id


async def update_comment_by_comment_id(comment_id: str, comment_item: Dict) -> int:
    """
    更新增一条评论记录
    Args:
        comment_id:
        comment_item:

    Returns:

    """
    async_db_conn: AsyncMysqlDB = media_crawler_db_var.get()
    effect_row: int = await async_db_conn.update_table("xhs_note_comment", comment_item, "comment_id", comment_id)
    return effect_row

async def update_comment_by_comment_id_and_task_id(comment_id: str, comment_item: Dict, task_id: str) -> int:
    """

    Args:
        comment_id:
        comment_item:
        task_id:

    Returns:

    """
    async_db_conn: AsyncMysqlDB = media_crawler_db_var.get()
    where_conditions = {"comment_id": comment_id, "task_id": task_id}
    effect_row: int = await async_db_conn.multi_update_table("xhs_note_comment", comment_item, where_conditions)
    return effect_row

async def query_creator_by_user_id(user_id: str) -> Dict:
    """
    查询一条创作者记录
    Args:
        user_id:

    Returns:

    """
    async_db_conn: AsyncMysqlDB = media_crawler_db_var.get()
    sql: str = f"select * from xhs_creator where user_id = '{user_id}'"
    rows: List[Dict] = await async_db_conn.query(sql)
    if len(rows) > 0:
        return rows[0]
    return dict()


async def add_new_creator(creator_item: Dict) -> int:
    """
    新增一条创作者信息
    Args:
        creator_item:

    Returns:

    """
    async_db_conn: AsyncMysqlDB = media_crawler_db_var.get()
    last_row_id: int = await async_db_conn.item_to_table("xhs_creator", creator_item)
    return last_row_id


async def update_creator_by_user_id(user_id: str, creator_item: Dict) -> int:
    """
    更新一条创作者信息
    Args:
        user_id:
        creator_item:

    Returns:

    """
    async_db_conn: AsyncMysqlDB = media_crawler_db_var.get()
    effect_row: int = await async_db_conn.update_table("xhs_creator", creator_item, "user_id", user_id)
    return effect_row
