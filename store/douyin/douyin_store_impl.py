# -*- coding: utf-8 -*-
# @Author  : relakkes@gmail.com
# @Time    : 2024/1/14 18:46
# @Desc    : 抖音存储实现类
import asyncio
import csv
import json
import os
import pathlib
from typing import Dict

import aiofiles

from base.base_crawler import AbstractStore
from tools import utils
from var import crawler_type_var
from store.douyin.douyin_store_sql import update_comment_by_comment_id_and_task_id

# def calculatet_number_of_files(file_store_path: str) -> int:
#     """计算数据保存文件的前部分排序数字，支持每次运行代码不写到同一个文件中
#     Args:
#         file_store_path;
#     Returns:
#         file nums
#     """
#     if not os.path.exists(file_store_path):
#         return 1
#     return max([int(file_name.split("_")[0])for file_name in os.listdir(file_store_path)])+1
def calculatet_number_of_files(file_store_path: str) -> int:
    """计算数据保存文件的前部分排序数字，支持每次运行代码不写到同一个文件中
    Args:
        file_store_path: 文件存储路径
    Returns:
        文件的数量
    """
    if not os.path.exists(file_store_path):
        return 1

    max_num = 0
    for file_name in os.listdir(file_store_path):
        try:
            num = int(file_name.split("_")[0])
            max_num = max(max_num, num)
        except ValueError:
            continue

    return max_num + 1


class DouyinCsvStoreImplement(AbstractStore):
    csv_store_path: str = "data/douyin"
    file_count:int=calculatet_number_of_files(csv_store_path)

    def make_save_file_name(self, store_type: str) -> str:
        """
        make save file name by store type
        Args:
            store_type: contents or comments

        Returns: eg: data/douyin/search_comments_20240114.csv ...

        """
        return f"{self.csv_store_path}/{self.file_count}_{crawler_type_var.get()}_{store_type}_{utils.get_current_date()}.csv"

    def n_make_save_file_name(self, store_type: str, task_id: str) -> str:
        return f"{self.csv_store_path}/{task_id}_{crawler_type_var.get()}_{store_type}_{utils.get_current_date()}.csv"

    async def n_save_data_to_csv(self, save_item: Dict, store_type: str, task_id: str) -> None:
        """
                Below is a simple way to save it in CSV format.
                Args:
                    save_item:  save content dict info
                    store_type: Save type contains content and comments（contents | comments）

                Returns: no returns

                """
        pathlib.Path(self.csv_store_path).mkdir(parents=True, exist_ok=True)
        save_file_name = self.n_make_save_file_name(store_type=store_type, task_id=task_id)
        async with aiofiles.open(save_file_name, mode='a+', encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)
            utils.logger.info(f"aweme_id: {save_item.get('aweme_id')}")
            if await f.tell() == 0:
                await writer.writerow(save_item.keys())
            await writer.writerow(save_item.values())


    async def save_data_to_csv(self, save_item: Dict, store_type: str):
        """
        Below is a simple way to save it in CSV format.
        Args:
            save_item:  save content dict info
            store_type: Save type contains content and comments（contents | comments）

        Returns: no returns

        """
        pathlib.Path(self.csv_store_path).mkdir(parents=True, exist_ok=True)
        save_file_name = self.make_save_file_name(store_type=store_type)
        async with aiofiles.open(save_file_name, mode='a+', encoding="utf-8-sig", newline="") as f:

            writer = csv.writer(f)
            utils.logger.info(f"aweme_id: {save_item.get('aweme_id')}")
            if await f.tell() == 0:
                await writer.writerow(save_item.keys())
            await writer.writerow(save_item.values())

            # Use csv.DictWriter for more convenience
            # Create a csv writer object
            # writer = csv.writer(f)
            #
            # # Log the aweme_id
            # utils.logger.info(f"aweme_id: {save_item.get('aweme_id')}")
            #
            # # Check if file is empty to write headers
            # if await f.tell() == 0:
            #     await writer.writerow(save_item.keys())
            #
            # # Convert all values to strings and wrap them with '=' and quotes
            # save_item_str = {
            #     key: f'="{value}"' if isinstance(value, (int, float)) and len(str(value)) > 11 else str(value) for
            #     key, value in save_item.items()}
            #
            # # Write the row
            # await writer.writerow(save_item_str.values())

    async def store_content(self, content_item: Dict):
        """
        Xiaohongshu content CSV storage implementation
        Args:
            content_item: note item dict

        Returns:

        """
        await self.save_data_to_csv(save_item=content_item, store_type="contents")

    async def store_comment(self, comment_item: Dict):
        """
        Xiaohongshu comment CSV storage implementation
        Args:
            comment_item: comment item dict

        Returns:

        """
        await self.save_data_to_csv(save_item=comment_item, store_type="comments")

    async def n_store_content(self, content_item: Dict, task_id: str):
        await self.n_save_data_to_csv(save_item=content_item, store_type="contents", task_id=task_id)

    async def n_store_comment(self, comment_item: Dict, task_id: str):
        await self.n_save_data_to_csv(save_item=comment_item, store_type="comments", task_id=task_id)

class DouyinDbStoreImplement(AbstractStore):
    async def store_content(self, content_item: Dict):
        """
        Douyin content DB storage implementation
        Args:
            content_item: content item dict

        Returns:

        """

        from .douyin_store_sql import (add_new_content,
                                       query_content_by_content_id,
                                       update_content_by_content_id)
        aweme_id = content_item.get("aweme_id")
        aweme_detail: Dict = await query_content_by_content_id(content_id=aweme_id)
        if not aweme_detail:
            content_item["add_ts"] = utils.get_current_timestamp()
            if content_item.get("title"):
                await add_new_content(content_item)
        else:
            await update_content_by_content_id(aweme_id, content_item=content_item)


    async def store_comment(self, comment_item: Dict):
        """
        Douyin content DB storage implementation
        Args:
            comment_item: comment item dict

        Returns:

        """
        from .douyin_store_sql import (add_new_comment,
                                       query_comment_by_comment_id,
                                       update_comment_by_comment_id)
        comment_id = comment_item.get("comment_id")
        comment_detail: Dict = await query_comment_by_comment_id(comment_id=comment_id)
        if not comment_detail:
            comment_item["add_ts"] = utils.get_current_timestamp()
            await add_new_comment(comment_item)
        else:
            await update_comment_by_comment_id(comment_id, comment_item=comment_item)

    async def n_store_comment(self, comment_item: Dict, task_id: str, user_id: str):
        """
                Douyin content DB storage implementation
                Args:
                    comment_item: comment item dict

                Returns:

                """
        from .douyin_store_sql import (n_add_new_comment,
                                       query_comment_by_comment_id,
                                       update_comment_by_comment_id,
                                       query_comment_by_comment_id_and_task_id,
                                       check_user_owns_comment_for_task)
        comment_id = comment_item.get("comment_id")
        # comment_detail: Dict = await query_comment_by_comment_id_and_task_id(comment_id=comment_id, task_id=task_id)
        comment_detail = await check_user_owns_comment_for_task(user_id=user_id, comment_id=comment_id, task_id=task_id)
        print(comment_detail)

        if not comment_detail:
            comment_item["add_ts"] = utils.get_current_timestamp()
            await n_add_new_comment(comment_item)
        else:
            print(f"User {user_id} already owns the comment {comment_id} for task {task_id}, skipping insert.")
            # await update_comment_by_comment_id_and_task_id(comment_id, comment_item=comment_item, task_id=task_id)


class DouyinJsonStoreImplement(AbstractStore):
    json_store_path: str = "data/douyin"
    lock = asyncio.Lock()
    file_count:int=calculatet_number_of_files(json_store_path)

    def make_save_file_name(self, store_type: str) -> str:
        """
        make save file name by store type
        Args:
            store_type: Save type contains content and comments（contents | comments）

        Returns:

        """


        return f"{self.json_store_path}/{self.file_count}_{crawler_type_var.get()}_{store_type}_{utils.get_current_date()}.json"

    async def save_data_to_json(self, save_item: Dict, store_type: str):
        """
        Below is a simple way to save it in json format.
        Args:
            save_item: save content dict info
            store_type: Save type contains content and comments（contents | comments）

        Returns:

        """
        pathlib.Path(self.json_store_path).mkdir(parents=True, exist_ok=True)
        save_file_name = self.make_save_file_name(store_type=store_type)
        save_data = []

        async with self.lock:
            if os.path.exists(save_file_name):
                async with aiofiles.open(save_file_name, 'r', encoding='utf-8') as file:
                    save_data = json.loads(await file.read())

            save_data.append(save_item)
            async with aiofiles.open(save_file_name, 'w', encoding='utf-8') as file:
                await file.write(json.dumps(save_data, ensure_ascii=False))

    async def store_content(self, content_item: Dict):
        """
        content JSON storage implementation
        Args:
            content_item:

        Returns:

        """
        await self.save_data_to_json(content_item, "contents")

    async def store_comment(self, comment_item: Dict):
        """
        comment JSON storage implementatio
        Args:
            comment_item:

        Returns:

        """
        await self.save_data_to_json(comment_item, "comments")
