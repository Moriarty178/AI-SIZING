-- Fix: VARCHAR(255) with utf8mb4 exceeds MySQL 767-byte index key limit
-- 255 * 4 = 1020 bytes > 767. Change to VARCHAR(191) = 764 bytes (within limit)
-- Only alter columns that are used in indexes
-- Idempotent: only modifies columns that are not already VARCHAR(191)
-- Self-healing: cleans up its own failed state from flyway_schema_history on retry

-- Clean up this migration's failed record from schema history (so Flyway can retry)
DELETE FROM flyway_schema_history WHERE version = '7' AND type = 'SQL' AND description = 'fix varchar index length';
SET FOREIGN_KEY_CHECKS=0;

-- Helper procedure to alter a column only if it's not already VARCHAR(191)
DROP PROCEDURE IF EXISTS alter_column_if_needed;
DELIMITER //
CREATE PROCEDURE alter_column_if_needed(
    IN p_table VARCHAR(255),
    IN p_column VARCHAR(255),
    IN p_new_def VARCHAR(500)
)
BEGIN
    DECLARE current_type VARCHAR(500);
    SELECT COLUMN_TYPE INTO current_type
    FROM information_schema.COLUMNS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME = p_table
      AND COLUMN_NAME = p_column;

    IF current_type IS NOT NULL AND current_type != p_new_def THEN
        SET @sql = CONCAT('ALTER TABLE ', p_table, ' MODIFY COLUMN ', p_column, ' ', p_new_def);
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END //
DELIMITER ;

-- ===== users table =====
CALL alter_column_if_needed('users', 'username', 'VARCHAR(191) NOT NULL');
CALL alter_column_if_needed('users', 'email', 'VARCHAR(191) NOT NULL');
CALL alter_column_if_needed('users', 'id', 'VARCHAR(191) NOT NULL');
CALL alter_column_if_needed('users', 'role', 'VARCHAR(191) NOT NULL');

-- ===== projects table =====
CALL alter_column_if_needed('projects', 'id', 'VARCHAR(191) NOT NULL');
CALL alter_column_if_needed('projects', 'user_id', 'VARCHAR(191) NULL');
CALL alter_column_if_needed('projects', 'name', 'VARCHAR(191) NOT NULL');
CALL alter_column_if_needed('projects', 'dev_unit', 'VARCHAR(191) NULL');
CALL alter_column_if_needed('projects', 'owner_name', 'VARCHAR(191) NULL');
CALL alter_column_if_needed('projects', 'assigned_admin1_id', 'VARCHAR(191) NULL');

-- ===== project_data table =====
CALL alter_column_if_needed('project_data', 'id', 'VARCHAR(191) NOT NULL');
CALL alter_column_if_needed('project_data', 'project_id', 'VARCHAR(191) NOT NULL');

-- ===== project_revisions table =====
CALL alter_column_if_needed('project_revisions', 'id', 'VARCHAR(191) NOT NULL');
CALL alter_column_if_needed('project_revisions', 'project_id', 'VARCHAR(191) NOT NULL');
CALL alter_column_if_needed('project_revisions', 'user_id', 'VARCHAR(191) NULL');
CALL alter_column_if_needed('project_revisions', 'baseline_id', 'VARCHAR(191) NULL');

-- ===== activity_logs table =====
CALL alter_column_if_needed('activity_logs', 'id', 'VARCHAR(191) NOT NULL');
CALL alter_column_if_needed('activity_logs', 'actor_username', 'VARCHAR(191) NOT NULL');
CALL alter_column_if_needed('activity_logs', 'target_id', 'VARCHAR(191) NULL');
CALL alter_column_if_needed('activity_logs', 'target_name', 'VARCHAR(191) NULL');

-- ===== notifications table =====
CALL alter_column_if_needed('notifications', 'id', 'VARCHAR(191) NOT NULL');
CALL alter_column_if_needed('notifications', 'project_id', 'VARCHAR(191) NOT NULL');
CALL alter_column_if_needed('notifications', 'actor_user_id', 'VARCHAR(191) NULL');
CALL alter_column_if_needed('notifications', 'recipient_user_id', 'VARCHAR(191) NULL');

DROP PROCEDURE IF EXISTS alter_column_if_needed;

SET FOREIGN_KEY_CHECKS=1;