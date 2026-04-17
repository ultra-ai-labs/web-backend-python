-- Add shop order table for mall recharge callbacks
CREATE TABLE IF NOT EXISTS `shop_order` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `order_no` varchar(128) NOT NULL COMMENT '商城订单号',
  `phone` varchar(32) NOT NULL COMMENT '手机号',
  `username` varchar(64) NOT NULL COMMENT '系统用户名',
  `user_id` varchar(64) NOT NULL COMMENT '系统用户ID',
  `amount` decimal(10,2) DEFAULT NULL COMMENT '订单金额',
  `quota` bigint NOT NULL DEFAULT 0 COMMENT '购买额度',
  `is_new_user` tinyint(1) NOT NULL DEFAULT 0 COMMENT '商城标记是否新用户',
  `status` varchar(32) NOT NULL DEFAULT 'success' COMMENT '处理状态',
  `remark` varchar(255) DEFAULT NULL COMMENT '备注',
  `raw_payload` longtext COMMENT '原始请求体',
  `create_time` bigint NOT NULL COMMENT '创建时间戳',
  `update_time` bigint DEFAULT NULL COMMENT '更新时间戳',
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_shop_order_order_no` (`order_no`),
  KEY `idx_shop_order_username` (`username`),
  KEY `idx_shop_order_user_id` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='商城订单记录表';
