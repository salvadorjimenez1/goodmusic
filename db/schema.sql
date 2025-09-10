-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Albums table
CREATE TABLE IF NOT EXISTS albums (
    id SERIAL PRIMARY KEY,
    title VARCHAR(200) NOT NULL,
    artist VARCHAR(200) NOT NULL,
    cover_url TEXT,
    external_id VARCHAR(100), -- e.g. Spotify/MusicBrainz ID
    created_at TIMESTAMP DEFAULT NOW()
);

-- Reviews table
CREATE TABLE IF NOT EXISTS reviews (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    album_id INT NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
    rating INT CHECK (rating >= 1 AND rating <= 10),
    content TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- User Album Status table
CREATE TYPE album_status AS ENUM ('want_to_listen', 'listened');

CREATE TABLE IF NOT EXISTS user_album_status (
    id SERIAL PRIMARY KEY,
    user_id INT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    album_id INT NOT NULL REFERENCES albums(id) ON DELETE CASCADE,
    status album_status NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, album_id)
);

-- Create an index for faster lookups on product name
CREATE INDEX idx_album_name ON albums(title);

-- Create an index for faster lookups on customer email
CREATE INDEX idx_user_email ON users(email);