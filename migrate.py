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

# 加载环境变量
load_dotenv('.env.prod.local')
load_dotenv()

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
    
    # 分割 SQL 语句
    statements = [s.strip() for s in sql_content.split(';') if s.strip() and not s.strip().startswith('--')]
    
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
            
            execute_migration(conn, migration_file, force)
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
                else:
                    execute_migration(conn, migration_file, force)
                    executed_count += 1
            
            print(f"\n📊 Summary: {executed_count} executed, {skipped_count} skipped")
        
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
