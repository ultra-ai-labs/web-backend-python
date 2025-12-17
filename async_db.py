# -*- coding: utf-8 -*-
# @Author  : relakkes@gmail.com
# @Time    : 2024/4/6 14:21
# @Desc    : 异步Aiomysql的增删改查封装
import json
from typing import Any, Dict, List, Union

import aiomysql


class AsyncMysqlDB:
    def __init__(self, pool: aiomysql.Pool) -> None:
        self.__pool = pool

    async def query(self, sql: str, *args: Union[str, int]) -> List[Dict[str, Any]]:
        """
        从给定的 SQL 中查询记录，返回的是一个列表
        :param sql: 查询的sql
        :param args: sql中传递动态参数列表
        :return:
        """
        async with self.__pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql, args)
                data = await cur.fetchall()
                return data or []

    async def get_first(self, sql: str, *args: Union[str, int]) -> Union[Dict[str, Any], None]:
        """
        从给定的 SQL 中查询记录，返回的是符合条件的第一个结果
        :param sql: 查询的sql
        :param args:sql中传递动态参数列表
        :return:
        """
        async with self.__pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql, args)
                data = await cur.fetchone()
                return data

    async def item_to_table(self, table_name: str, item: Dict[str, Any]) -> int:
        """
        表中插入数据
        :param table_name: 表名
        :param item: 一条记录的字典信息
        :return:
        """
        fields = list(item.keys())
        values = list(item.values())
        fields = [f'`{field}`' for field in fields]
        fieldstr = ','.join(fields)
        valstr = ','.join(['%s'] * len(item))
        sql = "INSERT INTO %s (%s) VALUES(%s)" % (table_name, fieldstr, valstr)
        async with self.__pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql, values)
                lastrowid = cur.lastrowid
                return lastrowid

    async def n_item_to_table(self, table_name: str, item: Dict[str, Any]) -> int:
        """
        表中插入数据
        :param table_name: 表名
        :param item: 一条记录的字典信息
        :return:
        """
        fields = list(item.keys())
        values = list(item.values())
        fields = [f'`{field}`' for field in fields]
        fieldstr = ','.join(fields)
        valstr = ','.join(['%s'] * len(item))
        sql = "INSERT INTO %s (%s) VALUES(%s)" % (table_name, fieldstr, valstr)
        async with self.__pool.acquire() as conn:
            async with conn.cursor(aiomysql.DictCursor) as cur:
                await cur.execute(sql, values)
                lastrowid = cur.lastrowid
                return lastrowid

    async def update_table(self, table_name: str, updates: Dict[str, Any], field_where: str,
                           value_where: Union[str, int, float]) -> int:
        """
        更新指定表的记录
        :param table_name: 表名
        :param updates: 需要更新的字段和值的 key - value 映射
        :param field_where: update 语句 where 条件中的字段名
        :param value_where: update 语句 where 条件中的字段值
        :return:
        """
        upsets = []
        values = []
        for k, v in updates.items():
            s = '`%s`=%%s' % k
            upsets.append(s)
            values.append(v)
        upsets = ','.join(upsets)
        sql = 'UPDATE %s SET %s WHERE %s="%s"' % (
            table_name,
            upsets,
            field_where, value_where,
        )
        async with self.__pool.acquire() as conn:
            async with conn.cursor() as cur:
                rows = await cur.execute(sql, values)
                return rows

    async def multi_update_table(self, table_name: str, updates: Dict[str, Any], where_conditions: Dict[str, Union[str, int, float]]) -> int:
        """
                更新指定表的记录
                :param table_name: 表名
                :param updates: 需要更新的字段和值的 key - value 映射
                :param where_conditions: update 语句 where 条件中的字段名和值的 key - value 映射
                :return: 更新的行数
                """
        upsets = []
        values = []
        for k, v in updates.items():
            s = '`%s`=%%s' % k
            upsets.append(s)
            values.append(v)
        upsets = ','.join(upsets)

        where_clauses = []
        for k, v in where_conditions.items():
            s = '`%s`=%%s' % k
            where_clauses.append(s)
            values.append(v)
        where_clauses = ' AND '.join(where_clauses)

        sql = 'UPDATE %s SET %s WHERE %s' % (
            table_name,
            upsets,
            where_clauses,
        )
        async with self.__pool.acquire() as conn:
            async with conn.cursor() as cur:
                rows = await cur.execute(sql, values)
                return rows

    async def execute(self, sql: str, *args: Union[str, int]) -> int:
        """
        需要更新、写入等操作的 excute 执行语句
        :param sql:
        :param args:
        :return:
        """
        async with self.__pool.acquire() as conn:
            async with conn.cursor() as cur:
                rows = await cur.execute(sql, args)
                return rows
