# Migrations 规范

本目录下的 `.sql` 文件只用于安全的数据库增量变更。

## 必须遵守

1. 只要数据库结构有变更，就必须新增一个新的 migration 文件。
2. 不要修改历史 migration 文件，已经提交过的文件只允许新增，不允许重写。
3. migration 文件名要能表达本次变更内容，例如：
   - `add_phone_to_users.sql`
   - `create_shop_order_table.sql`
   - `add_amount_to_shop_order.sql`

## 允许的操作

- `CREATE TABLE IF NOT EXISTS`
- `ALTER TABLE ... ADD COLUMN`
- `ALTER TABLE ... MODIFY COLUMN`
- `ALTER TABLE ... ADD INDEX`
- 其他不会删除线上现有数据的增量变更

## 严禁的操作

以下语句禁止放进自动部署使用的 migration 文件：

- `DROP TABLE`
- `TRUNCATE TABLE`
- `DROP DATABASE`
- `DROP SCHEMA`
- 任何会删除线上现有表或清空线上现有数据的 SQL

这些操作如果确实需要执行，必须：

1. 先完整备份数据库
2. 单独评审
3. 由人工在明确窗口执行
4. 不要混入普通自动部署 migration

## 推荐流程

1. 先改代码
2. 同时新增对应 migration 文件
3. 本地执行 `python3 migrate.py`
4. 验证接口和表结构
5. 再 push 部署

## 特别说明

以后新增字段、索引、表结构调整，都只能通过“新增 migration 文件”的方式处理。

不要再出现以下情况：

- 改了 model/repo/controller，但没有新增 migration 文件
- 为了图省事，直接在 migration 里写删表 SQL
- 为了修复线上，手工改库后不把对应 SQL 补回仓库
