-- ========================================
-- 拾光 · 数据库初始化（MySQL 容器首次启动时自动执行）
-- ========================================

SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

CREATE DATABASE IF NOT EXISTS ai_writer CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE ai_writer;

-- 用户表
CREATE TABLE IF NOT EXISTS `user`
(
    id           BIGINT AUTO_INCREMENT COMMENT 'id' PRIMARY KEY,
    userAccount  VARCHAR(256)                           NOT NULL COMMENT '账号',
    userPassword VARCHAR(512)                           NOT NULL COMMENT '密码',
    userName     VARCHAR(256)                           NULL COMMENT '用户昵称',
    userAvatar   VARCHAR(1024)                          NULL COMMENT '用户头像',
    userProfile  VARCHAR(512)                           NULL COMMENT '用户简介',
    userRole     VARCHAR(256) DEFAULT 'user'            NOT NULL COMMENT '用户角色：user/admin/vip',
    quota        INT          DEFAULT 5                 NOT NULL COMMENT '剩余配额',
    vipTime      DATETIME                               NULL COMMENT '成为会员时间',
    editTime     DATETIME     DEFAULT CURRENT_TIMESTAMP NOT NULL COMMENT '编辑时间',
    createTime   DATETIME     DEFAULT CURRENT_TIMESTAMP NOT NULL COMMENT '创建时间',
    updateTime   DATETIME     DEFAULT CURRENT_TIMESTAMP NOT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    isDelete     TINYINT      DEFAULT 0                 NOT NULL COMMENT '是否删除',
    UNIQUE KEY uk_userAccount (userAccount),
    INDEX idx_userName (userName)
) COMMENT '用户' COLLATE = utf8mb4_unicode_ci;

-- 演示账号：admin / user / test，密码均为 12345678（MD5 + 盐值 yupi）
INSERT INTO `user` (id, userAccount, userPassword, userName, userAvatar, userProfile, userRole, quota) VALUES
(1, 'admin', '10670d38ec32fa8102be6a37f8cb52bf', '管理员', '', '系统管理员', 'admin', 5),
(2, 'user',  '10670d38ec32fa8102be6a37f8cb52bf', '普通用户', '', '我是一个普通用户', 'user', 5),
(3, 'test',  '10670d38ec32fa8102be6a37f8cb52bf', '测试账号', '', '这是一个测试账号', 'user', 5)
ON DUPLICATE KEY UPDATE userName = VALUES(userName);

-- 文章表
CREATE TABLE IF NOT EXISTS article
(
    id                  BIGINT AUTO_INCREMENT COMMENT 'id' PRIMARY KEY,
    taskId              VARCHAR(64)                        NOT NULL COMMENT '任务ID（UUID）',
    userId              BIGINT                             NOT NULL COMMENT '用户ID',
    topic               VARCHAR(500)                       NOT NULL COMMENT '选题',
    userDescription     TEXT                               NULL COMMENT '参考素材 / 用户补充描述',
    enabledImageMethods JSON                               NULL COMMENT '允许的配图方式列表',
    enableImages        TINYINT  DEFAULT 1                 NOT NULL COMMENT '是否生成配图（0=纯文字）',
    style               VARCHAR(20)                        NULL COMMENT '文风：tech/emotional/educational/humorous/wechat_official/marketing/xiaohongshu',
    mainTitle           VARCHAR(200)                       NULL COMMENT '主标题',
    subTitle            VARCHAR(300)                       NULL COMMENT '副标题',
    titleOptions        JSON                               NULL COMMENT '标题方案列表',
    outline             JSON                               NULL COMMENT '大纲（JSON）',
    content             TEXT                               NULL COMMENT '正文（Markdown）',
    fullContent         TEXT                               NULL COMMENT '完整图文（Markdown，含配图）',
    coverImage          VARCHAR(512)                       NULL COMMENT '封面图 URL',
    images              JSON                               NULL COMMENT '配图列表',
    status              VARCHAR(20) DEFAULT 'PENDING'      NOT NULL COMMENT '状态：PENDING/PROCESSING/COMPLETED/FAILED',
    phase               VARCHAR(50) DEFAULT 'PENDING'      NULL COMMENT '当前阶段',
    errorMessage        TEXT                               NULL COMMENT '错误信息',
    createTime          DATETIME    DEFAULT CURRENT_TIMESTAMP NOT NULL COMMENT '创建时间',
    completedTime       DATETIME                           NULL COMMENT '完成时间',
    updateTime          DATETIME    DEFAULT CURRENT_TIMESTAMP NOT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    isDelete            TINYINT     DEFAULT 0              NOT NULL COMMENT '是否删除',
    UNIQUE KEY uk_taskId (taskId),
    INDEX idx_userId (userId),
    INDEX idx_status (status),
    INDEX idx_createTime (createTime),
    INDEX idx_userId_status (userId, status)
) COMMENT '文章表' COLLATE = utf8mb4_unicode_ci;

-- 智能体执行日志表
CREATE TABLE IF NOT EXISTS agent_log
(
    id           BIGINT AUTO_INCREMENT COMMENT 'id' PRIMARY KEY,
    taskId       VARCHAR(64)                        NOT NULL COMMENT '任务ID',
    agentName    VARCHAR(50)                        NOT NULL COMMENT '智能体名称',
    startTime    DATETIME                           NOT NULL COMMENT '开始时间',
    endTime      DATETIME                           NULL COMMENT '结束时间',
    durationMs   INT                                NULL COMMENT '耗时（毫秒）',
    status       VARCHAR(20)                        NOT NULL COMMENT '状态：SUCCESS/FAILED',
    errorMessage TEXT                               NULL COMMENT '错误信息',
    prompt       TEXT                               NULL COMMENT '使用的 Prompt',
    inputData    JSON                               NULL COMMENT '输入数据',
    outputData   JSON                               NULL COMMENT '输出数据',
    createTime   DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL COMMENT '创建时间',
    updateTime   DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    isDelete     TINYINT  DEFAULT 0                 NOT NULL COMMENT '是否删除',
    INDEX idx_taskId (taskId),
    INDEX idx_agentName (agentName),
    INDEX idx_status (status),
    INDEX idx_createTime (createTime)
) COMMENT '智能体执行日志表' COLLATE = utf8mb4_unicode_ci;

-- 支付记录表
CREATE TABLE IF NOT EXISTS payment_record
(
    id                    BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键',
    userId                BIGINT       NOT NULL COMMENT '用户ID',
    stripeSessionId       VARCHAR(128) COMMENT 'Stripe Checkout Session ID',
    stripePaymentIntentId VARCHAR(128) COMMENT 'Stripe 支付意向ID',
    amount                DECIMAL(10, 2) NOT NULL COMMENT '金额（美元）',
    currency              VARCHAR(8)   DEFAULT 'usd' COMMENT '货币',
    status                VARCHAR(32)  NOT NULL COMMENT '状态：PENDING/SUCCEEDED/FAILED/REFUNDED',
    productType           VARCHAR(32)  NOT NULL COMMENT '产品类型：VIP_PERMANENT',
    description           VARCHAR(256) COMMENT '描述',
    refundTime            DATETIME     NULL COMMENT '退款时间',
    refundReason          VARCHAR(512) NULL COMMENT '退款原因',
    createTime            DATETIME     DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updateTime            DATETIME     DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX idx_userId (userId),
    INDEX idx_stripeSessionId (stripeSessionId),
    INDEX idx_status (status),
    INDEX idx_createTime (createTime)
) COMMENT '支付记录表' COLLATE = utf8mb4_unicode_ci;
