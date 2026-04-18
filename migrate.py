#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移管理脚本
用法：python3 migrate.py [migration_file.sql]
- 不带参数：执行所有未执行的迁移
- 带参数：执行指定的迁移文件
"""

import sys
import os
from pathlib import Path
import pymysql
from dotenv import load_dotenv
import time
import re

# 加载环境变量
load_dotenv('.env.prod.local')
load_dotenv()

SCHEMA_REPAIRS = [
    {
        'name': 'quota.analysised_quota',
        'table': 'quota',
        'column': 'analysised_quota',
        'alter_sql': (
            "ALTER TABLE `quota` "
            "ADD COLUMN `analysised_quota` bigint NOT NULL DEFAULT 0 "
            "COMMENT '已分析额度' AFTER `used_quota`"
        ),
    },
    {
        'name': 'shop_order.amount',
        'table': 'shop_order',
        'column': 'amount',
        'alter_sql': (
            "ALTER TABLE `shop_order` "
            "ADD COLUMN `amount` decimal(10,2) DEFAULT NULL "
            "COMMENT '订单金额' AFTER `user_id`"
        ),
    },
]

LEGACY_BOOTSTRAP_MIGRATIONS = {
    'add_quota.sql': {
        'guard_tables': ['users', 'quota'],
        'reason': 'legacy bootstrap migration with destructive DROP TABLE statements',
    }
}

DESTRUCTIVE_SQL_PATTERNS = [
    re.compile(r'^\s*DROP\s+TABLE\b', re.IGNORECASE),
    re.compile(r'^\s*TRUNCATE\s+TABLE\b', re.IGNORECASE),
    re.compile(r'^\s*DROP\s+DATABASE\b', re.IGNORECASE),
    re.compile(r'^\s*DROP\s+SCHEMA\b', re.IGNORECASE),
]

def get_db_connection():
    """获取数据库连接"""
    # 尝试从环境变量获取配置
    host = os.getenv('PROD_DB_URI', 'localhost')
    port = int(os.getenv('PROD_DB_PORT', 3306))
    user = os.getenv('PROD_DB_USER', 'root')
    password = os.getenv('PROD_DB_PWD', '')
    database = os.getenv('PROD_DB_NAME', 'media_crawler')
    
    return pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset='utf8mb4'
    )

def ensure_migrations_table(conn):
    """确保迁移记录表存在"""
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS `schema_migrations` (
                `id` int NOT NULL AUTO_INCREMENT,
                `migration_name` varchar(255) NOT NULL,
                `executed_at` bigint NOT NULL,
                PRIMARY KEY (`id`),
                UNIQUE KEY `unique_migration_name` (`migration_name`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='迁移记录表'
        """)
        conn.commit()
    finally:
        cursor.close()

def is_migration_executed(conn, migration_name):
    """检查迁移是否已执行"""
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT COUNT(*) FROM schema_migrations WHERE migration_name = %s",
            (migration_name,)
        )
        count = cursor.fetchone()[0]
        return count > 0
    finally:
        cursor.close()

def should_skip_legacy_bootstrap_migration(conn, migration_name, force=False):
    if force or migration_name not in LEGACY_BOOTSTRAP_MIGRATIONS:
        return False

    config = LEGACY_BOOTSTRAP_MIGRATIONS[migration_name]
    existing_tables = [table for table in config['guard_tables'] if table_exists(conn, table)]
    if not existing_tables:
        return False

    print(
        f"⏭️  Skip legacy bootstrap migration: {migration_name} "
        f"({config['reason']}; existing tables: {', '.join(existing_tables)})"
    )

    if not is_migration_executed(conn, migration_name):
        record_migration(conn, migration_name)
        print(f"   📝 Recorded skipped migration: {migration_name}")

    return True

def record_migration(conn, migration_name):
    """记录已执行的迁移"""
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO schema_migrations (migration_name, executed_at) VALUES (%s, %s)",
            (migration_name, int(time.time()))
        )
        conn.commit()
    finally:
        cursor.close()

def table_exists(conn, table_name):
    cursor = conn.cursor()
    try:
        cursor.execute("SHOW TABLES LIKE %s", (table_name,))
        return cursor.fetchone() is not None
    finally:
        cursor.close()

def column_exists(conn, table_name, column_name):
    cursor = conn.cursor()
    try:
        cursor.execute(f"SHOW COLUMNS FROM `{table_name}` LIKE %s", (column_name,))
        return cursor.fetchone() is not None
    finally:
        cursor.close()

def repair_required_schema(conn):
    print("\n🔍 Validating critical schema...")
    repaired_count = 0

    for repair in SCHEMA_REPAIRS:
        table_name = repair['table']
        column_name = repair['column']
        label = repair['name']

        if not table_exists(conn, table_name):
            print(f"   ⏭️  Skip repair for {label}: table `{table_name}` does not exist yet")
            continue

        if column_exists(conn, table_name, column_name):
            print(f"   ✅ OK: {label}")
            continue

        print(f"   ⚠️  Missing column detected: {label}")
        cursor = conn.cursor()
        try:
            cursor.execute(repair['alter_sql'])
            conn.commit()
            repaired_count += 1
            print(f"   🔧 Repaired: {label}")
        except pymysql.Error as e:
            conn.rollback()
            error_msg = str(e)
            if 'Duplicate column' in error_msg or 'already exists' in error_msg:
                print(f"   ℹ️  Column already exists while repairing {label}")
            else:
                print(f"   ❌ Failed to repair {label}: {error_msg}")
                return False
        finally:
            cursor.close()

    print(f"✅ Schema validation finished, repaired {repaired_count} item(s)\n")
    return True

def is_destructive_statement(statement):
    return any(pattern.search(statement) for pattern in DESTRUCTIVE_SQL_PATTERNS)

def should_skip_destructive_migration(conn, migration_name, statements, force=False):
    if force:
        return False

    destructive_statements = [stmt for stmt in statements if is_destructive_statement(stmt)]
    if not destructive_statements:
        return False

    print(
        f"⏭️  Skip destructive migration: {migration_name} "
        f"(automatic deploy does not allow DROP/TRUNCATE statements)"
    )
    for stmt in destructive_statements:
        preview = " ".join(stmt.split())
        print(f"   ⚠️  blocked statement: {preview[:120]}")

    if not is_migration_executed(conn, migration_name):
        record_migration(conn, migration_name)
        print(f"   📝 Recorded skipped destructive migration: {migration_name}")

    return True

def execute_migration(conn, sql_file, force=False):
    """执行单个迁移文件"""
    migration_name = sql_file.name
    
    # 检查是否已执行
    if not force and is_migration_executed(conn, migration_name):
        print(f"⏭️  Skipped (already executed): {migration_name}")
        return True
    
    print(f"⏳ Executing: {migration_name}")
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # 去掉纯注释行后再分割 SQL，避免“文件以注释开头导致整段 SQL 被跳过”
    cleaned_lines = []
    for line in sql_content.splitlines():
        stripped = line.strip()
        if stripped.startswith('--'):
            continue
        cleaned_lines.append(line)

    cleaned_sql = '\n'.join(cleaned_lines)
    statements = [s.strip() for s in cleaned_sql.split(';') if s.strip()]
    if not statements:
        print(f"   ❌ No executable SQL statements found in: {migration_name}")
        return False

    if should_skip_destructive_migration(conn, migration_name, statements, force):
        return True
    
    cursor = conn.cursor()
    success_count = 0
    has_error = False
    
    for statement in statements:
        try:
            cursor.execute(statement)
            conn.commit()
            success_count += 1
        except pymysql.Error as e:
            error_msg = str(e)
            # 忽略已存在的错误
            if 'Duplicate column' in error_msg or 'already exists' in error_msg:
                print(f"   ℹ️  Info: {error_msg[:60]}...")
            else:
                print(f"   ⚠️  Error: {error_msg}")
                has_error = True
    
    cursor.close()
    
    # 记录迁移
    if not has_error:
        try:
            record_migration(conn, migration_name)
            print(f"   ✅ Completed and recorded: {success_count} statement(s) executed\n")
        except pymysql.Error as e:
            # 如果已经记录过（UNIQUE 约束），忽略
            if 'Duplicate entry' in str(e):
                print(f"   ✅ Completed: {success_count} statement(s) executed\n")
            else:
                raise
    else:
        print(f"   ⚠️  Completed with warnings: {success_count} statement(s) executed\n")
    
    return True

def main():
    """主函数"""
    try:
        # 连接数据库
        print("🔗 Connecting to database...")
        conn = get_db_connection()
        print("✅ Database connected\n")
        
        # 确保迁移记录表存在
        ensure_migrations_table(conn)
        
        print("-" * 60)
        
        migrations_dir = Path('migrations')
        force = '--force' in sys.argv
        
        # 检查是否指定了特定文件
        migration_file_arg = None
        for arg in sys.argv[1:]:
            if not arg.startswith('--'):
                migration_file_arg = arg
                break
        
        if migration_file_arg:
            # 执行指定的迁移文件
            migration_file = migrations_dir / migration_file_arg
            if not migration_file.exists():
                print(f"❌ Migration file not found: {migration_file}")
                return 1

            ok = execute_migration(conn, migration_file, force)
            if not ok:
                return 1
        else:
            # 执行所有迁移文件
            migration_files = sorted(migrations_dir.glob('*.sql'))

            if not migration_files:
                print("❌ No migration files found in 'migrations' directory")
                return 1

            print(f"📁 Found {len(migration_files)} migration file(s)\n")

            executed_count = 0
            skipped_count = 0

            for migration_file in migration_files:
                migration_name = migration_file.name
                if not force and is_migration_executed(conn, migration_name):
                    print(f"⏭️  Skipped (already executed): {migration_name}")
                    skipped_count += 1
                elif should_skip_legacy_bootstrap_migration(conn, migration_name, force):
                    skipped_count += 1
                else:
                    ok = execute_migration(conn, migration_file, force)
                    if not ok:
                        return 1
                    executed_count += 1

            print(f"\n📊 Summary: {executed_count} executed, {skipped_count} skipped")

        schema_ok = repair_required_schema(conn)
        if not schema_ok:
            return 1
        
        conn.close()
        print("-" * 60)
        print("✅ Migration process completed successfully!")
        return 0
        
    except pymysql.Error as e:
        print(f"❌ Database error: {e}")
        return 1
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
