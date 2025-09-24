-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    hashed_password TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Artists table
CREATE TABLE IF NOT EXISTS artists (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL
);

-- Albums table
CREATE TABLE IF NOT EXISTS albums (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    year INT,
    cover_url TEXT,
    artist_id INT NOT NULL REFERENCES artists(id) ON DELETE CASCADE
);

-- Reviews table
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    content TEXT NOT NULL,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    album_id INT NOT NULL REFERENCES albums(id) ON DELETE CASCADE
);

-- User Album Status table
CREATE TABLE IF NOT EXISTS user_album_status (
    id SERIAL PRIMARY KEY,
    status VARCHAR(50) NOT NULL, -- "listened", "want-to-listen", "favorite"
    created_at TIMESTAMP DEFAULT NOW(),
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    album_id INT NOT NULL REFERENCES albums(id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_album_title ON albums(title);
CREATE INDEX idx_user_username ON users(username);