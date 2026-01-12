-- 为 analysis_module 表添加 task_id 字段
-- 执行时间: 2026-01-12
-- 说明: 添加 task_id 字段用于关联任务

ALTER TABLE analysis_module 
ADD COLUMN task_id VARCHAR(64) NOT NULL COMMENT '关联的任务ID' AFTER id;

-- 可选：为 task_id 添加索引以提高查询性能
CREATE INDEX idx_task_id_user_id ON analysis_module(task_id, user_id);

-- 如果表中已有数据，需要先设置一个默认值，然后再执行上述语句
-- UPDATE analysis_module SET task_id = 'default_task_id' WHERE task_id IS NULL OR task_id = '';
