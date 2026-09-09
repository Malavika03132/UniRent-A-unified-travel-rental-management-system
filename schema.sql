-- ========================================================
-- UNIRENT: Heritage Stays & Vehicle Rental Management System
-- Relational Database Schema (MySQL 8.0+)
-- Kerala Operations: Ernakulam & Thrissur
-- ========================================================

CREATE DATABASE IF NOT EXISTS `unirent_db` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `unirent_db`;

-- Drop tables in reverse order of foreign key dependency
DROP TABLE IF EXISTS `complaints`;
DROP TABLE IF EXISTS `reviews`;
DROP TABLE IF EXISTS `payments`;
DROP TABLE IF EXISTS `bookings`;
DROP TABLE IF EXISTS `vehicles`;
DROP TABLE IF EXISTS `properties`;
DROP TABLE IF EXISTS `admins`;
DROP TABLE IF EXISTS `owners`;
DROP TABLE IF EXISTS `users`;

-- --------------------------------------------------------
-- 1. USERS TABLE
-- --------------------------------------------------------
CREATE TABLE `users` (
    `user_id` INT AUTO_INCREMENT PRIMARY KEY,
    `full_name` VARCHAR(120) NOT NULL,
    `email` VARCHAR(150) NOT NULL UNIQUE,
    `phone` VARCHAR(20) NOT NULL,
    `password_hash` VARCHAR(255) NOT NULL,
    `role` ENUM('traveler', 'owner', 'admin') NOT NULL DEFAULT 'traveler',
    `status` ENUM('active', 'suspended') NOT NULL DEFAULT 'active',
    `profile_image` VARCHAR(255) DEFAULT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_users_role` (`role`),
    INDEX `idx_users_email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 2. OWNERS TABLE
-- --------------------------------------------------------
CREATE TABLE `owners` (
    `owner_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL UNIQUE,
    `business_name` VARCHAR(150) DEFAULT NULL,
    `district` VARCHAR(50) NOT NULL DEFAULT 'Ernakulam',
    `kyc_status` ENUM('pending', 'verified', 'rejected') NOT NULL DEFAULT 'verified',
    `bank_account` VARCHAR(100) DEFAULT NULL,
    `bio` TEXT DEFAULT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_owners_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 3. ADMINS TABLE
-- --------------------------------------------------------
CREATE TABLE `admins` (
    `admin_id` INT AUTO_INCREMENT PRIMARY KEY,
    `user_id` INT NOT NULL UNIQUE,
    `admin_level` VARCHAR(50) NOT NULL DEFAULT 'Super Admin',
    `department` VARCHAR(100) NOT NULL DEFAULT 'Operations',
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_admins_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 4. PROPERTIES TABLE
-- --------------------------------------------------------
CREATE TABLE `properties` (
    `property_id` INT AUTO_INCREMENT PRIMARY KEY,
    `owner_id` INT NOT NULL,
    `property_name` VARCHAR(160) NOT NULL,
    `slug` VARCHAR(180) NOT NULL UNIQUE,
    `property_type` VARCHAR(80) NOT NULL,
    `description` TEXT NOT NULL,
    `address` VARCHAR(255) NOT NULL,
    `district` ENUM('Ernakulam', 'Thrissur') NOT NULL,
    `latitude` DECIMAL(10, 7) NOT NULL,
    `longitude` DECIMAL(10, 7) NOT NULL,
    `price_per_night` DECIMAL(10, 2) NOT NULL,
    `guest_capacity` INT NOT NULL DEFAULT 2,
    `bedrooms` INT NOT NULL DEFAULT 1,
    `bathrooms` INT NOT NULL DEFAULT 1,
    `amenities` TEXT DEFAULT NULL,
    `images` TEXT DEFAULT NULL,
    `featured_image` VARCHAR(255) DEFAULT NULL,
    `approval_status` ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
    `rejection_reason` TEXT DEFAULT NULL,
    `availability_status` ENUM('available', 'booked', 'maintenance') NOT NULL DEFAULT 'available',
    `featured` BOOLEAN NOT NULL DEFAULT FALSE,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_properties_owner` FOREIGN KEY (`owner_id`) REFERENCES `owners` (`owner_id`) ON DELETE CASCADE,
    INDEX `idx_prop_district` (`district`),
    INDEX `idx_prop_approval` (`approval_status`),
    INDEX `idx_prop_price` (`price_per_night`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 5. VEHICLES TABLE
-- --------------------------------------------------------
CREATE TABLE `vehicles` (
    `vehicle_id` INT AUTO_INCREMENT PRIMARY KEY,
    `owner_id` INT NOT NULL,
    `vehicle_name` VARCHAR(160) NOT NULL,
    `model` VARCHAR(100) NOT NULL,
    `vehicle_type` ENUM('car', 'bike', 'scooter') NOT NULL,
    `description` TEXT NOT NULL,
    `price_per_day` DECIMAL(10, 2) NOT NULL,
    `district` ENUM('Ernakulam', 'Thrissur') NOT NULL,
    `pickup_location` VARCHAR(255) NOT NULL,
    `latitude` DECIMAL(10, 7) NOT NULL,
    `longitude` DECIMAL(10, 7) NOT NULL,
    `delivery_available` BOOLEAN NOT NULL DEFAULT TRUE,
    `specifications` TEXT DEFAULT NULL,
    `images` TEXT DEFAULT NULL,
    `featured_image` VARCHAR(255) DEFAULT NULL,
    `approval_status` ENUM('pending', 'approved', 'rejected') NOT NULL DEFAULT 'pending',
    `rejection_reason` TEXT DEFAULT NULL,
    `availability_status` ENUM('available', 'rented', 'maintenance') NOT NULL DEFAULT 'available',
    `featured` BOOLEAN NOT NULL DEFAULT FALSE,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_vehicles_owner` FOREIGN KEY (`owner_id`) REFERENCES `owners` (`owner_id`) ON DELETE CASCADE,
    INDEX `idx_veh_district` (`district`),
    INDEX `idx_veh_type` (`vehicle_type`),
    INDEX `idx_veh_approval` (`approval_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 6. BOOKINGS TABLE
-- --------------------------------------------------------
CREATE TABLE `bookings` (
    `booking_id` INT AUTO_INCREMENT PRIMARY KEY,
    `booking_reference` VARCHAR(50) NOT NULL UNIQUE,
    `user_id` INT NOT NULL,
    `owner_id` INT NOT NULL,
    `listing_type` ENUM('property', 'vehicle') NOT NULL,
    `property_id` INT DEFAULT NULL,
    `vehicle_id` INT DEFAULT NULL,
    `start_date` DATE NOT NULL,
    `end_date` DATE NOT NULL,
    `total_days` INT NOT NULL DEFAULT 1,
    `daily_rate` DECIMAL(10, 2) NOT NULL,
    `service_fee` DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    `tax_amount` DECIMAL(10, 2) NOT NULL DEFAULT 0.00,
    `total_amount` DECIMAL(10, 2) NOT NULL,
    `booking_status` ENUM('pending', 'confirmed', 'active', 'completed', 'cancelled') NOT NULL DEFAULT 'confirmed',
    `special_requests` TEXT DEFAULT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_bookings_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_bookings_owner` FOREIGN KEY (`owner_id`) REFERENCES `owners` (`owner_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_bookings_property` FOREIGN KEY (`property_id`) REFERENCES `properties` (`property_id`) ON DELETE SET NULL,
    CONSTRAINT `fk_bookings_vehicle` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`vehicle_id`) ON DELETE SET NULL,
    INDEX `idx_bookings_status` (`booking_status`),
    INDEX `idx_bookings_dates` (`start_date`, `end_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 7. PAYMENTS TABLE
-- --------------------------------------------------------
CREATE TABLE `payments` (
    `payment_id` INT AUTO_INCREMENT PRIMARY KEY,
    `booking_id` INT NOT NULL UNIQUE,
    `amount` DECIMAL(10, 2) NOT NULL,
    `payment_method` VARCHAR(50) NOT NULL DEFAULT 'card',
    `transaction_reference` VARCHAR(100) NOT NULL UNIQUE,
    `payment_status` ENUM('pending', 'successful', 'failed', 'refunded') NOT NULL DEFAULT 'successful',
    `gateway_response` TEXT DEFAULT NULL,
    `payment_date` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_payments_booking` FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`booking_id`) ON DELETE CASCADE,
    INDEX `idx_payments_status` (`payment_status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 8. REVIEWS TABLE
-- --------------------------------------------------------
CREATE TABLE `reviews` (
    `review_id` INT AUTO_INCREMENT PRIMARY KEY,
    `booking_id` INT NOT NULL UNIQUE,
    `user_id` INT NOT NULL,
    `listing_type` ENUM('property', 'vehicle') NOT NULL,
    `property_id` INT DEFAULT NULL,
    `vehicle_id` INT DEFAULT NULL,
    `rating` INT NOT NULL CHECK (`rating` BETWEEN 1 AND 5),
    `review_title` VARCHAR(150) DEFAULT NULL,
    `review_text` TEXT NOT NULL,
    `image_url` VARCHAR(255) DEFAULT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_reviews_booking` FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`booking_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_reviews_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_reviews_property` FOREIGN KEY (`property_id`) REFERENCES `properties` (`property_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_reviews_vehicle` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`vehicle_id`) ON DELETE CASCADE,
    INDEX `idx_reviews_rating` (`rating`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- 9. COMPLAINTS TABLE
-- --------------------------------------------------------
CREATE TABLE `complaints` (
    `complaint_id` INT AUTO_INCREMENT PRIMARY KEY,
    `complaint_reference` VARCHAR(50) NOT NULL UNIQUE,
    `booking_id` INT NOT NULL,
    `user_id` INT NOT NULL,
    `owner_id` INT NOT NULL,
    `category` VARCHAR(60) NOT NULL,
    `description` TEXT NOT NULL,
    `evidence_image` VARCHAR(255) DEFAULT NULL,
    `status` ENUM('open', 'under_review', 'owner_responded', 'resolved', 'rejected') NOT NULL DEFAULT 'open',
    `owner_response` TEXT DEFAULT NULL,
    `admin_response` TEXT DEFAULT NULL,
    `created_at` TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `resolved_at` TIMESTAMP NULL DEFAULT NULL,
    CONSTRAINT `fk_complaints_booking` FOREIGN KEY (`booking_id`) REFERENCES `bookings` (`booking_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_complaints_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`) ON DELETE CASCADE,
    CONSTRAINT `fk_complaints_owner` FOREIGN KEY (`owner_id`) REFERENCES `owners` (`owner_id`) ON DELETE CASCADE,
    INDEX `idx_complaints_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
