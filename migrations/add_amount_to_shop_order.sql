-- Migration: Add amount field to shop_order table
-- Date: 2026-04-18
-- Description:
-- - Add amount column to record order payment amount
-- - Used by mall recharge callback records only

ALTER TABLE `shop_order`
ADD COLUMN `amount` decimal(10,2) DEFAULT NULL COMMENT '订单金额' AFTER `user_id`;
