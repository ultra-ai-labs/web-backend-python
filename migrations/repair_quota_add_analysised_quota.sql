-- Repair migration for environments where `add_analysised_quota_to_quota_table.sql`
-- was recorded as executed but the column was not actually added.
ALTER TABLE `quota`
ADD COLUMN `analysised_quota` bigint NOT NULL DEFAULT 0 COMMENT '已分析额度' AFTER `used_quota`;
