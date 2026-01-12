/*
 Navicat Premium Data Transfer

 Source Server         : media_crawler
 Source Server Type    : MySQL
 Source Server Version : 90200 (9.2.0)
 Source Host           : localhost:3307
 Source Schema         : media_crawler

 Target Server Type    : MySQL
 Target Server Version : 90200 (9.2.0)
 File Encoding         : 65001

 Date: 23/12/2025 11:12:00
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for bilibili_up_info
-- ----------------------------
DROP TABLE IF EXISTS `bilibili_up_info`;
CREATE TABLE `bilibili_up_info`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户ID',
  `nickname` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户昵称',
  `sex` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户性别',
  `sign` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户签名',
  `avatar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户头像地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `total_fans` bigint NULL DEFAULT NULL COMMENT '粉丝数',
  `total_liked` bigint NULL DEFAULT NULL COMMENT '总获赞数',
  `user_rank` int NULL DEFAULT NULL COMMENT '用户等级',
  `is_official` int NULL DEFAULT NULL COMMENT '是否官号',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_bilibili_vi_user_123456`(`user_id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'B 站UP主信息' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for bilibili_video
-- ----------------------------
DROP TABLE IF EXISTS `bilibili_video`;
CREATE TABLE `bilibili_video`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户ID',
  `nickname` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户头像地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `video_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '视频ID',
  `video_type` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '视频类型',
  `title` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '视频标题',
  `desc` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '视频描述',
  `create_time` bigint NOT NULL COMMENT '视频发布时间戳',
  `liked_count` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '视频点赞数',
  `disliked_count` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '视频点踩数',
  `video_play_count` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '视频播放数量',
  `video_favorite_count` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '视频收藏数量',
  `video_share_count` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '视频分享数量',
  `video_coin_count` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '视频投币数量',
  `video_danmaku` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '视频弹幕数量',
  `video_comment` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '视频评论数量',
  `video_url` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '视频详情URL',
  `video_cover_url` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '视频封面图 URL',
  `source_keyword` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '搜索来源关键字',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_bilibili_vi_video_i_31c36e`(`video_id` ASC) USING BTREE,
  INDEX `idx_bilibili_vi_create__73e0ec`(`create_time` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'B站视频' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for bilibili_video_comment
-- ----------------------------
DROP TABLE IF EXISTS `bilibili_video_comment`;
CREATE TABLE `bilibili_video_comment`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户ID',
  `nickname` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户昵称',
  `sex` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户性别',
  `sign` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户签名',
  `avatar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户头像地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `comment_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '评论ID',
  `video_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '视频ID',
  `content` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '评论内容',
  `create_time` bigint NOT NULL COMMENT '评论时间戳',
  `sub_comment_count` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '评论回复数',
  `parent_comment_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '父评论ID',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_bilibili_vi_comment_41c34e`(`comment_id` ASC) USING BTREE,
  INDEX `idx_bilibili_vi_video_i_f22873`(`video_id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = 'B 站视频评论' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for douyin_aweme
-- ----------------------------
DROP TABLE IF EXISTS `douyin_aweme`;
CREATE TABLE `douyin_aweme`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户ID',
  `sec_uid` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户sec_uid',
  `short_user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户短ID',
  `user_unique_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户唯一ID',
  `nickname` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户头像地址',
  `user_signature` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户签名',
  `ip_location` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '评论时的IP地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `aweme_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '视频ID',
  `aweme_type` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '视频类型',
  `title` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '视频标题',
  `desc` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '视频描述',
  `create_time` bigint NOT NULL COMMENT '视频发布时间戳',
  `liked_count` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '视频点赞数',
  `comment_count` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '视频评论数',
  `share_count` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '视频分享数',
  `collected_count` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '视频收藏数',
  `aweme_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '视频详情页URL',
  `source_keyword` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '搜索来源关键字',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_douyin_awem_aweme_i_6f7bc6`(`aweme_id` ASC) USING BTREE,
  INDEX `idx_douyin_awem_create__299dfe`(`create_time` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '抖音视频' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for douyin_aweme_comment
-- ----------------------------
DROP TABLE IF EXISTS `douyin_aweme_comment`;
CREATE TABLE `douyin_aweme_comment`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户ID',
  `sec_uid` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户sec_uid',
  `short_user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户短ID',
  `user_unique_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户唯一ID',
  `nickname` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户头像地址',
  `user_signature` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户签名',
  `ip_location` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '评论时的IP地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `comment_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '评论ID',
  `aweme_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '视频ID',
  `content` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '评论内容',
  `create_time` bigint NOT NULL COMMENT '评论时间戳',
  `sub_comment_count` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '评论回复数',
  `extra_data` json NULL COMMENT '额外的动态字段',
  `task_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '任务ID',
  `market_result` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '私信结果',
  `intent_customer` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '意向客户',
  `parent_comment_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '父评论ID',
  `like_count` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '0' COMMENT '点赞数',
  `pictures` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL DEFAULT '' COMMENT '评论图片列表',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_douyin_awem_comment_fcd7e4`(`comment_id` ASC) USING BTREE,
  INDEX `idx_douyin_awem_aweme_i_c50049`(`aweme_id` ASC) USING BTREE,
  INDEX `idx_douyin_task_id_1`(`task_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 593 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '抖音视频评论' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for dy_creator
-- ----------------------------
DROP TABLE IF EXISTS `dy_creator`;
CREATE TABLE `dy_creator`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户ID',
  `nickname` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户头像地址',
  `ip_location` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '评论时的IP地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `desc` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '用户描述',
  `gender` varchar(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '性别',
  `follows` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '关注数',
  `fans` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '粉丝数',
  `interaction` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '获赞数',
  `videos_count` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '作品数',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '抖音博主信息' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for kuaishou_video
-- ----------------------------
DROP TABLE IF EXISTS `kuaishou_video`;
CREATE TABLE `kuaishou_video`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户ID',
  `nickname` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户头像地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `video_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '视频ID',
  `video_type` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '视频类型',
  `title` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '视频标题',
  `desc` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '视频描述',
  `create_time` bigint NOT NULL COMMENT '视频发布时间戳',
  `liked_count` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '视频点赞数',
  `viewd_count` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '视频浏览数量',
  `video_url` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '视频详情URL',
  `video_cover_url` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '视频封面图 URL',
  `video_play_url` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '视频播放 URL',
  `source_keyword` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '搜索来源关键字',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_kuaishou_vi_video_i_c5c6a6`(`video_id` ASC) USING BTREE,
  INDEX `idx_kuaishou_vi_create__a10dee`(`create_time` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '快手视频' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for kuaishou_video_comment
-- ----------------------------
DROP TABLE IF EXISTS `kuaishou_video_comment`;
CREATE TABLE `kuaishou_video_comment`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户ID',
  `nickname` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户头像地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `comment_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '评论ID',
  `video_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '视频ID',
  `content` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '评论内容',
  `create_time` bigint NOT NULL COMMENT '评论时间戳',
  `sub_comment_count` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '评论回复数',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_kuaishou_vi_comment_ed48fa`(`comment_id` ASC) USING BTREE,
  INDEX `idx_kuaishou_vi_video_i_e50914`(`video_id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '快手视频评论' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for task
-- ----------------------------
DROP TABLE IF EXISTS `task`;
CREATE TABLE `task`  (
  `task_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务ID',
  `keyword` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '关键词',
  `platform` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '抓取平台',
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '使用的用户ID',
  `project_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '项目ID',
  `create_time` bigint NOT NULL COMMENT '创建时间戳',
  `update_time` bigint NULL DEFAULT NULL COMMENT '更新时间戳',
  `delete_time` bigint NULL DEFAULT NULL COMMENT '删除时间戳',
  PRIMARY KEY (`task_id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for task_step
-- ----------------------------
DROP TABLE IF EXISTS `task_step`;
CREATE TABLE `task_step`  (
  `step_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '步骤ID',
  `task_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '任务ID',
  `step_type` int NOT NULL COMMENT '步骤类型',
  `state` int NOT NULL COMMENT '步骤状态',
  `progress` int NOT NULL COMMENT '步骤进度',
  `url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci NULL DEFAULT NULL COMMENT '生成的文件路径',
  `create_time` bigint NOT NULL COMMENT '创建时间戳',
  `update_time` bigint NULL DEFAULT NULL COMMENT '更新时间戳',
  PRIMARY KEY (`step_id`) USING BTREE,
  INDEX `fk_task_step_task`(`task_id` ASC) USING BTREE,
  CONSTRAINT `fk_task_step_task` FOREIGN KEY (`task_id`) REFERENCES `task` (`task_id`) ON DELETE RESTRICT ON UPDATE RESTRICT
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_unicode_ci ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for tieba_comment
-- ----------------------------
DROP TABLE IF EXISTS `tieba_comment`;
CREATE TABLE `tieba_comment`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `comment_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '评论ID',
  `parent_comment_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '父评论ID',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '评论内容',
  `user_link` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '用户主页链接',
  `user_nickname` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '用户昵称',
  `user_avatar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '用户头像地址',
  `tieba_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '贴吧ID',
  `tieba_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '贴吧名称',
  `tieba_link` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '贴吧链接',
  `publish_time` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '发布时间',
  `ip_location` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT 'IP地理位置',
  `sub_comment_count` int NULL DEFAULT 0 COMMENT '子评论数',
  `note_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '帖子ID',
  `note_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '帖子链接',
  `add_ts` bigint NOT NULL COMMENT '添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '最后修改时间戳',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_tieba_comment_comment_id`(`note_id` ASC) USING BTREE,
  INDEX `idx_tieba_comment_note_id`(`note_id` ASC) USING BTREE,
  INDEX `idx_tieba_comment_publish_time`(`publish_time` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '贴吧评论表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for tieba_creator
-- ----------------------------
DROP TABLE IF EXISTS `tieba_creator`;
CREATE TABLE `tieba_creator`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户ID',
  `user_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户名',
  `nickname` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户头像地址',
  `ip_location` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '评论时的IP地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `gender` varchar(2) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '性别',
  `follows` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '关注数',
  `fans` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '粉丝数',
  `registration_duration` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '吧龄',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '贴吧创作者' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for tieba_note
-- ----------------------------
DROP TABLE IF EXISTS `tieba_note`;
CREATE TABLE `tieba_note`  (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `note_id` varchar(644) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '帖子ID',
  `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '帖子标题',
  `desc` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '帖子描述',
  `note_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '帖子链接',
  `publish_time` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '发布时间',
  `user_link` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '用户主页链接',
  `user_nickname` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '用户昵称',
  `user_avatar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '用户头像地址',
  `tieba_id` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '贴吧ID',
  `tieba_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '贴吧名称',
  `tieba_link` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '贴吧链接',
  `total_replay_num` int NULL DEFAULT 0 COMMENT '帖子回复总数',
  `total_replay_page` int NULL DEFAULT 0 COMMENT '帖子回复总页数',
  `ip_location` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT 'IP地理位置',
  `add_ts` bigint NOT NULL COMMENT '添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '最后修改时间戳',
  `source_keyword` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '搜索来源关键字',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_tieba_note_note_id`(`note_id` ASC) USING BTREE,
  INDEX `idx_tieba_note_publish_time`(`publish_time` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '贴吧帖子表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for users
-- ----------------------------
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users`  (
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户ID',
  `username` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户名',
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '密码',
  `email` varchar(128) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '邮箱',
  `expire_time` bigint NULL DEFAULT NULL COMMENT '账号过期时间戳',
  `create_time` bigint NOT NULL COMMENT '创建时间戳',
  `update_time` bigint NULL DEFAULT NULL COMMENT '更新时间戳',
  PRIMARY KEY (`user_id`) USING BTREE,
  UNIQUE INDEX `username`(`username` ASC) USING BTREE,
  UNIQUE INDEX `email`(`email` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '用户表' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for weibo_creator
-- ----------------------------
DROP TABLE IF EXISTS `weibo_creator`;
CREATE TABLE `weibo_creator`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户ID',
  `nickname` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户头像地址',
  `ip_location` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '评论时的IP地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `desc` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '用户描述',
  `gender` varchar(2) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '性别',
  `follows` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '关注数',
  `fans` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '粉丝数',
  `tag_list` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '标签列表',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '微博博主' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for weibo_note
-- ----------------------------
DROP TABLE IF EXISTS `weibo_note`;
CREATE TABLE `weibo_note`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户ID',
  `nickname` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户头像地址',
  `gender` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户性别',
  `profile_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户主页地址',
  `ip_location` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '发布微博的地理信息',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `note_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '帖子ID',
  `content` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '帖子正文内容',
  `create_time` bigint NOT NULL COMMENT '帖子发布时间戳',
  `create_date_time` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '帖子发布日期时间',
  `liked_count` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '帖子点赞数',
  `comments_count` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '帖子评论数量',
  `shared_count` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '帖子转发数量',
  `note_url` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '帖子详情URL',
  `source_keyword` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '搜索来源关键字',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_weibo_note_note_id_f95b1a`(`note_id` ASC) USING BTREE,
  INDEX `idx_weibo_note_create__692709`(`create_time` ASC) USING BTREE,
  INDEX `idx_weibo_note_create__d05ed2`(`create_date_time` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '微博帖子' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for weibo_note_comment
-- ----------------------------
DROP TABLE IF EXISTS `weibo_note_comment`;
CREATE TABLE `weibo_note_comment`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户ID',
  `nickname` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户头像地址',
  `gender` varchar(12) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户性别',
  `profile_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户主页地址',
  `ip_location` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '发布微博的地理信息',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `comment_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '评论ID',
  `note_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '帖子ID',
  `content` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '评论内容',
  `create_time` bigint NOT NULL COMMENT '评论时间戳',
  `create_date_time` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '评论日期时间',
  `comment_like_count` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '评论点赞数量',
  `sub_comment_count` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '评论回复数',
  `parent_comment_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '父评论ID',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_weibo_note__comment_c7611c`(`comment_id` ASC) USING BTREE,
  INDEX `idx_weibo_note__note_id_24f108`(`note_id` ASC) USING BTREE,
  INDEX `idx_weibo_note__create__667fe3`(`create_date_time` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '微博帖子评论' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for xhs_creator
-- ----------------------------
DROP TABLE IF EXISTS `xhs_creator`;
CREATE TABLE `xhs_creator`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户ID',
  `nickname` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户头像地址',
  `ip_location` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '评论时的IP地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `desc` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '用户描述',
  `gender` varchar(1) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '性别',
  `follows` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '关注数',
  `fans` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '粉丝数',
  `interaction` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '获赞和收藏数',
  `tag_list` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '标签列表',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '小红书博主' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for xhs_note
-- ----------------------------
DROP TABLE IF EXISTS `xhs_note`;
CREATE TABLE `xhs_note`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户ID',
  `nickname` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户头像地址',
  `ip_location` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '评论时的IP地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `note_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '笔记ID',
  `type` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '笔记类型(normal | video)',
  `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '笔记标题',
  `desc` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '笔记描述',
  `video_url` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '视频地址',
  `time` bigint NOT NULL COMMENT '笔记发布时间戳',
  `last_update_time` bigint NOT NULL COMMENT '笔记最后更新时间戳',
  `liked_count` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '笔记点赞数',
  `collected_count` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '笔记收藏数',
  `comment_count` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '笔记评论数',
  `share_count` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '笔记分享数',
  `image_list` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '笔记封面图片列表',
  `tag_list` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '标签列表',
  `note_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '笔记详情页的URL',
  `source_keyword` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT '' COMMENT '搜索来源关键字',
  `xsec_token` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '签名算法',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_xhs_note_note_id_209457`(`note_id` ASC) USING BTREE,
  INDEX `idx_xhs_note_time_eaa910`(`time` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 2 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '小红书笔记' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for xhs_note_comment
-- ----------------------------
DROP TABLE IF EXISTS `xhs_note_comment`;
CREATE TABLE `xhs_note_comment`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户ID',
  `nickname` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户昵称',
  `avatar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户头像地址',
  `ip_location` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '评论时的IP地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  `comment_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '评论ID',
  `create_time` bigint NOT NULL COMMENT '评论时间戳',
  `note_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '笔记ID',
  `content` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '评论内容',
  `sub_comment_count` int NOT NULL COMMENT '子评论数量',
  `pictures` varchar(512) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL,
  `task_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '所属任务ID',
  `extra_data` json NULL COMMENT '额外的动态字段',
  `market_result` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '私信结果',
  `intent_customer` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '意向客户',
  `parent_comment_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '父评论ID',
  `like_count` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '评论点赞数量',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_xhs_note_co_comment_8e8349`(`comment_id` ASC) USING BTREE,
  INDEX `idx_xhs_note_co_create__204f8d`(`create_time` ASC) USING BTREE,
  INDEX `idx_xhs_task_id_1`(`task_id` ASC) USING BTREE
) ENGINE = InnoDB AUTO_INCREMENT = 349 CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '小红书笔记评论' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for zhihu_comment
-- ----------------------------
DROP TABLE IF EXISTS `zhihu_comment`;
CREATE TABLE `zhihu_comment`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `comment_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '评论ID',
  `parent_comment_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '父评论ID',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '评论内容',
  `publish_time` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '发布时间',
  `ip_location` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'IP地理位置',
  `sub_comment_count` int NOT NULL DEFAULT 0 COMMENT '子评论数',
  `like_count` int NOT NULL DEFAULT 0 COMMENT '点赞数',
  `dislike_count` int NOT NULL DEFAULT 0 COMMENT '踩数',
  `content_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '内容ID',
  `content_type` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '内容类型(article | answer | zvideo)',
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户ID',
  `user_link` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户主页链接',
  `user_nickname` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户昵称',
  `user_avatar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户头像地址',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_zhihu_comment_comment_id`(`comment_id` ASC) USING BTREE,
  INDEX `idx_zhihu_comment_content_id`(`content_id` ASC) USING BTREE,
  INDEX `idx_zhihu_comment_publish_time`(`publish_time` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '知乎评论' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for zhihu_content
-- ----------------------------
DROP TABLE IF EXISTS `zhihu_content`;
CREATE TABLE `zhihu_content`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `content_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '内容ID',
  `content_type` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '内容类型(article | answer | zvideo)',
  `content_text` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '内容文本, 如果是视频类型这里为空',
  `content_url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '内容落地链接',
  `question_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '问题ID, type为answer时有值',
  `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '内容标题',
  `desc` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '内容描述',
  `created_time` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '创建时间',
  `updated_time` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '更新时间',
  `voteup_count` int NOT NULL DEFAULT 0 COMMENT '赞同人数',
  `comment_count` int NOT NULL DEFAULT 0 COMMENT '评论数量',
  `source_keyword` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '来源关键词',
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户ID',
  `user_link` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户主页链接',
  `user_nickname` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户昵称',
  `user_avatar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户头像地址',
  `user_url_token` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户url_token',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_zhihu_content_content_id`(`content_id` ASC) USING BTREE,
  INDEX `idx_zhihu_content_created_time`(`created_time` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '知乎内容（回答、文章、视频）' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for zhihu_creator
-- ----------------------------
DROP TABLE IF EXISTS `zhihu_creator`;
CREATE TABLE `zhihu_creator`  (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户ID',
  `user_link` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户主页链接',
  `user_nickname` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户昵称',
  `user_avatar` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户头像地址',
  `url_token` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '用户URL Token',
  `gender` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT '用户性别',
  `ip_location` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL DEFAULT NULL COMMENT 'IP地理位置',
  `follows` int NOT NULL DEFAULT 0 COMMENT '关注数',
  `fans` int NOT NULL DEFAULT 0 COMMENT '粉丝数',
  `anwser_count` int NOT NULL DEFAULT 0 COMMENT '回答数',
  `video_count` int NOT NULL DEFAULT 0 COMMENT '视频数',
  `question_count` int NOT NULL DEFAULT 0 COMMENT '问题数',
  `article_count` int NOT NULL DEFAULT 0 COMMENT '文章数',
  `column_count` int NOT NULL DEFAULT 0 COMMENT '专栏数',
  `get_voteup_count` int NOT NULL DEFAULT 0 COMMENT '获得的赞同数',
  `add_ts` bigint NOT NULL COMMENT '记录添加时间戳',
  `last_modify_ts` bigint NOT NULL COMMENT '记录最后修改时间戳',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `idx_zhihu_creator_user_id`(`user_id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '知乎创作者' ROW_FORMAT = Dynamic;

SET FOREIGN_KEY_CHECKS = 1;

-- ----------------------------
-- Table structure for analysis_module
-- ----------------------------
DROP TABLE IF EXISTS `analysis_module`;
CREATE TABLE `analysis_module` (
  `id` int NOT NULL AUTO_INCREMENT COMMENT '自增ID',
  `task_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '关联的任务ID',
  `user_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NOT NULL COMMENT '使用的用户ID',
  `service_introduction` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '分析描述模板的服务介绍',
  `customer_description` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci NULL COMMENT '分析描述模板的客户描述',
  `default` int NOT NULL DEFAULT 0 COMMENT '默认值',
  `create_time` bigint NOT NULL COMMENT '创建时间戳',
  `update_time` bigint NULL DEFAULT NULL COMMENT '更新时间戳',
  `delete_time` bigint NULL DEFAULT NULL COMMENT '删除时间戳',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_analysis_module_user_id`(`user_id` ASC) USING BTREE,
  INDEX `idx_analysis_module_task_user`(`task_id` ASC, `user_id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_0900_ai_ci COMMENT = '分析模块' ROW_FORMAT = Dynamic;

-- ----------------------------
-- Table structure for quota
-- ----------------------------
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
