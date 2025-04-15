-- create_plants_data.sql
CREATE TABLE IF NOT EXISTS plants_data (
    id SERIAL PRIMARY KEY,
    url_source TEXT NOT NULL,
    url_s3 TEXT,
    label VARCHAR(50) NOT NULL
);
