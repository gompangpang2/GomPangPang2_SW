-- 곰팡팡이 DB 초기화: mysql -u root -p < schema.sql
CREATE DATABASE IF NOT EXISTS gompang DEFAULT CHARACTER SET utf8mb4;
USE gompang;

CREATE TABLE IF NOT EXISTS users (
  id            INT AUTO_INCREMENT PRIMARY KEY,
  username      VARCHAR(30)  NOT NULL UNIQUE,
  password_hash VARCHAR(255) NOT NULL,
  created_at    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP
);
