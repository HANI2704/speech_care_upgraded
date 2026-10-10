-- Run this script to create the MySQL database before running Django migrations
-- Usage: mysql -u root -p < setup_mysql.sql

CREATE DATABASE IF NOT EXISTS speech_care_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER IF NOT EXISTS 'speechcare_user'@'localhost' IDENTIFIED BY 'SpeechCare@2024';
GRANT ALL PRIVILEGES ON speech_care_db.* TO 'speechcare_user'@'localhost';
FLUSH PRIVILEGES;

SELECT 'Database speech_care_db created successfully!' AS Status;
