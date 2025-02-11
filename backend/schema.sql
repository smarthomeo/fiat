CREATE DATABASE IF NOT EXISTS platform2025;
USE platform2025;


CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    created_at DATETIME NOT NULL,
    is_host BOOLEAN DEFAULT FALSE,
    image VARCHAR(255) DEFAULT NULL,
    INDEX email_idx (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Food experiences table
CREATE TABLE IF NOT EXISTS food_experiences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    host_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    location_name VARCHAR(255) NOT NULL,
    price_per_person DECIMAL(10, 2) NOT NULL,
    cuisine_type VARCHAR(100) NOT NULL,
    menu_description TEXT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    status ENUM('draft', 'published', 'archived') DEFAULT 'draft',
    FOREIGN KEY (host_id) REFERENCES users(id),
    INDEX host_idx (host_id),
    INDEX status_idx (status),
    address VARCHAR(255) NOT NULL DEFAULT '',
    zipcode VARCHAR(10) NOT NULL DEFAULT '',
    city VARCHAR(100) NOT NULL DEFAULT '',
    state VARCHAR(50) NOT NULL DEFAULT '',
    latitude DECIMAL(10,8) NOT NULL DEFAULT 0,
    longitude DECIMAL(11,8) NOT NULL DEFAULT 0
);

-- Food experience images
DROP TABLE IF EXISTS food_experience_images;
CREATE TABLE food_experience_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    experience_id INT NOT NULL,
    image_path VARCHAR(255) NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at DATETIME NOT NULL,
    display_order INT DEFAULT 0,
    FOREIGN KEY (experience_id) REFERENCES food_experiences(id)
);

-- Food availability table
CREATE TABLE IF NOT EXISTS food_experience_availability (
    id INT AUTO_INCREMENT PRIMARY KEY,
    experience_id INT NOT NULL,
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    available_slots INT NOT NULL,
    FOREIGN KEY (experience_id) REFERENCES food_experiences(id),
    INDEX experience_date_idx (experience_id, date)
);

-- Stays table
CREATE TABLE IF NOT EXISTS stays (
    id INT AUTO_INCREMENT PRIMARY KEY,
    host_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    location_name VARCHAR(255) NOT NULL,
    price_per_night DECIMAL(10, 2) NOT NULL,
    max_guests INT NOT NULL,
    bedrooms INT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    status ENUM('draft', 'published', 'archived') DEFAULT 'draft',
    FOREIGN KEY (host_id) REFERENCES users(id),
    INDEX host_idx (host_id),
    INDEX status_idx (status),
    address VARCHAR(255) NOT NULL DEFAULT '',
    zipcode VARCHAR(10) NOT NULL DEFAULT '',
    city VARCHAR(100) NOT NULL DEFAULT '',
    state VARCHAR(50) NOT NULL DEFAULT '',
    latitude DECIMAL(10,8) NOT NULL DEFAULT 0,
    longitude DECIMAL(11,8) NOT NULL DEFAULT 0
);

-- Stay images
DROP TABLE IF EXISTS stay_images;
CREATE TABLE stay_images (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stay_id INT NOT NULL,
    image_path VARCHAR(255) NOT NULL,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at DATETIME NOT NULL,
    display_order INT DEFAULT 0,
    FOREIGN KEY (stay_id) REFERENCES stays(id)
);

-- Amenities lookup table
DROP TABLE IF EXISTS amenities;
CREATE TABLE amenities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50) NOT NULL,
    type ENUM('stay', 'food', 'both') NOT NULL DEFAULT 'both'
);

-- Insert some default amenities
INSERT INTO amenities (name, category, type) VALUES
-- Stay amenities
('WiFi', 'Basic', 'stay'),
('Air Conditioning', 'Basic', 'stay'),
('Kitchen', 'Basic', 'stay'),
('Free Parking', 'Basic', 'stay'),
('Pool', 'Outdoor', 'stay'),
('Hot Tub', 'Outdoor', 'stay'),
('BBQ Grill', 'Outdoor', 'stay'),
('Gym', 'Facilities', 'stay'),
('Washer/Dryer', 'Basic', 'stay'),
('TV', 'Entertainment', 'stay'),
-- Food Experience amenities
('Vegetarian Options', 'Dietary', 'food'),
('Vegan Options', 'Dietary', 'food'),
('Gluten-Free', 'Dietary', 'food'),
('Halal', 'Dietary', 'food'),
('Kosher', 'Dietary', 'food'),
('Wine Pairing', 'Beverages', 'food'),
('Cocktail Making', 'Activities', 'food'),
('Cooking Class', 'Activities', 'food'),
('Private Chef', 'Service', 'food'),
('Outdoor Dining', 'Setting', 'food'),
-- Shared amenities
('Wheelchair Accessible', 'Accessibility', 'both'),
('Pet Friendly', 'Basic', 'both'),
('Family Friendly', 'Basic', 'both');

-- Stay amenities junction table
CREATE TABLE IF NOT EXISTS stay_amenities (
    stay_id INT NOT NULL,
    amenity_id INT NOT NULL,
    PRIMARY KEY (stay_id, amenity_id),
    FOREIGN KEY (stay_id) REFERENCES stays(id),
    FOREIGN KEY (amenity_id) REFERENCES amenities(id)
);

-- Stay availability table with pricing
DROP TABLE IF EXISTS stay_availability;
CREATE TABLE stay_availability (
    id INT AUTO_INCREMENT PRIMARY KEY,
    stay_id INT NOT NULL,
    date DATE NOT NULL,
    is_available BOOLEAN DEFAULT true,
    price_override DECIMAL(10, 2) NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    FOREIGN KEY (stay_id) REFERENCES stays(id),
    UNIQUE KEY stay_date_idx (stay_id, date)
);

ALTER TABLE users
ADD COLUMN is_host BOOLEAN DEFAULT FALSE;

-- Add display_order column to food_experience_images if it doesn't exist
ALTER TABLE food_experience_images 
ADD COLUMN IF NOT EXISTS display_order INT DEFAULT 0;

-- Update existing rows to have sequential display_order
SET @order := 0;
UPDATE food_experience_images 
SET display_order = (@order := @order + 1) 
WHERE display_order = 0 
ORDER BY created_at;

-- Update existing rows to have sequential display_order
SET @order := 0;
UPDATE stay_images 
SET display_order = (@order := @order + 1) 
WHERE display_order = 0 
ORDER BY created_at;

-- Add indexes for location-based queries
ALTER TABLE food_experiences
ADD INDEX location_idx (latitude, longitude),
ADD INDEX zipcode_idx (zipcode);

ALTER TABLE stays
ADD INDEX location_idx (latitude, longitude),
ADD INDEX zipcode_idx (zipcode);

-- Drop the reviews table if it exists to avoid conflicts
DROP TABLE IF EXISTS reviews;

-- Create the reviews table
CREATE TABLE reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    experience_id INT,
    stay_id INT,
    rating DECIMAL(2,1) NOT NULL,
    comment TEXT,
    created_at DATETIME NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (experience_id) REFERENCES food_experiences(id),
    FOREIGN KEY (stay_id) REFERENCES stays(id),
    CHECK (rating BETWEEN 1 AND 5),
    CHECK ((experience_id IS NOT NULL AND stay_id IS NULL) OR 
           (experience_id IS NULL AND stay_id IS NOT NULL)),
    type ENUM('food', 'stay') NOT NULL DEFAULT 'food'
);

-- Add indexes for better performance
CREATE INDEX idx_experience_reviews ON reviews(experience_id);
CREATE INDEX idx_stay_reviews ON reviews(stay_id);

-- Add new columns to food_experiences table if they don't exist
ALTER TABLE food_experiences
ADD COLUMN IF NOT EXISTS duration VARCHAR(50) DEFAULT '2 hours',
ADD COLUMN IF NOT EXISTS max_guests INT DEFAULT 8,
ADD COLUMN IF NOT EXISTS language VARCHAR(50) DEFAULT 'English';

-- Make sure reviews table exists
CREATE TABLE IF NOT EXISTS reviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    experience_id INT,
    stay_id INT,
    rating DECIMAL(2,1) NOT NULL,
    comment TEXT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (experience_id) REFERENCES food_experiences(id),
    FOREIGN KEY (stay_id) REFERENCES stays(id),
    CHECK (rating BETWEEN 1 AND 5),
    CHECK ((experience_id IS NOT NULL AND stay_id IS NULL) OR 
           (experience_id IS NULL AND stay_id IS NOT NULL)),
    type ENUM('food', 'stay') NOT NULL DEFAULT 'food'
);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_experience_reviews ON reviews(experience_id);
CREATE INDEX IF NOT EXISTS idx_stay_reviews ON reviews(stay_id);

-- Add bathrooms column to stays table if it doesn't exist
ALTER TABLE stays
ADD COLUMN IF NOT EXISTS bathrooms INT DEFAULT 1; 