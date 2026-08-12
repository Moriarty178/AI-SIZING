CREATE TABLE IF NOT EXISTS notifications (
    id VARCHAR(191) NOT NULL,
    project_id VARCHAR(191) NOT NULL,
    actor_user_id VARCHAR(191) NULL,
    recipient_user_id VARCHAR(191) NULL,
    recipient_phone VARCHAR(20) NULL,
    message_type VARCHAR(50) NOT NULL,
    message_content LONGTEXT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    sent_at DATETIME(6) NULL,
    created_at DATETIME(6) NULL,
    error_message LONGTEXT NULL,
    retry_count INT NULL DEFAULT 0,
    PRIMARY KEY (id),
    KEY idx_notifications_project_id (project_id),
    KEY idx_notifications_recipient_user_id (recipient_user_id),
    KEY idx_notifications_status (status),
    KEY idx_notifications_message_type (message_type)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;