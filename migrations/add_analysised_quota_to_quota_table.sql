-- Migration: Add analysised_quota field to quota table
-- Date: 2026-03-02
-- Description: 
-- - Add analysised_quota field to track comment analysis consumption
-- - used_quota field will track crawler consumption
-- - analysised_quota field will track comment analysis consumption

-- Add analysised_quota column to quota table
ALTER TABLE `quota` ADD COLUMN `analysised_quota` bigint NOT NULL DEFAULT 0 COMMENT '已分析额度' AFTER `used_quota`;
