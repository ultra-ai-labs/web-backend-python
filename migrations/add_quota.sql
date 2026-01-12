DROP TABLE IF EXISTS `analysis_module`;
CREATE TABLE `analysis_module` (
	`id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
	`user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '使用的用户ID',
	`service_introduction` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '分析描述模板的服务介绍',
	`customer_description` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '分析描述模板的客户描述',
	`default` int NOT NULL DEFAULT 0 COMMENT '默认值',
	`create_time` bigint NOT NULL COMMENT '创建时间戳',
	`update_time` bigint NULL DEFAULT NULL COMMENT '更新时间戳',
	`delete_time` bigint NULL DEFAULT NULL COMMENT '删除时间戳',
	PRIMARY KEY (`id`) USING BTREE,
	INDEX `idx_analysis_module_user_id`(`user_id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '分析模块' ROW_FORMAT = Dynamic;
-- Add quota table
DROP TABLE IF EXISTS `quota`;
CREATE TABLE `quota` (
	`id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
	`user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户ID',
	`total_quota` bigint NOT NULL DEFAULT 0 COMMENT '总额度',
	`used_quota` bigint NOT NULL DEFAULT 0 COMMENT '已使用额度',
	`period_start` bigint NULL DEFAULT NULL COMMENT '配额周期开始时间戳',
	`period_end` bigint NULL DEFAULT NULL COMMENT '配额周期结束时间戳',
	`create_time` bigint NOT NULL COMMENT '创建时间戳',
	`update_time` bigint NULL DEFAULT NULL COMMENT '更新时间戳',
	PRIMARY KEY (`id`) USING BTREE,
	INDEX `idx_quota_user_id`(`user_id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '配额表' ROW_FORMAT = Dynamic;


-- WARNING: destructive operation. Make a backup before running.
-- Backup command example:
-- mysqldump -u<user> -p -h<host> <database> users > users_backup.sql

DROP TABLE IF EXISTS `users`;

CREATE TABLE `users` (
  `user_id` varchar(64) NOT NULL,
  `username` varchar(64) DEFAULT NULL,
  `email` varchar(128) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `expire_time` bigint DEFAULT NULL,
  `create_time` bigint NOT NULL DEFAULT 0,
  `update_time` bigint DEFAULT 0,
  PRIMARY KEY (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Triggers to populate create_time and update_time with UNIX timestamp
DROP TRIGGER IF EXISTS `users_before_insert`;
DROP TRIGGER IF EXISTS `users_before_update`;

DELIMITER $$
CREATE TRIGGER `users_before_insert` BEFORE INSERT ON `users`
FOR EACH ROW
BEGIN
  IF NEW.create_time IS NULL OR NEW.create_time = 0 THEN
    SET NEW.create_time = UNIX_TIMESTAMP();
  END IF;
  SET NEW.update_time = UNIX_TIMESTAMP();
END$$

CREATE TRIGGER `users_before_update` BEFORE UPDATE ON `users`
FOR EACH ROW
BEGIN
  SET NEW.update_time = UNIX_TIMESTAMP();
END$$
DELIMITER ;

