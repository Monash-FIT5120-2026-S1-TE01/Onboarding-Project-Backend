-- creat tables
-- 1. device_uuid given by frontend


CREATE TABLE IF NOT EXISTS user_device (
    device_uuid UUID PRIMARY KEY,
    created_timestamp TIMESTAMPTZ
);

-- Cloth suggestion structure can be see in initial_cloth_sugg.sql
CREATE TABLE IF NOT EXISTS cloth_sugg (
    sugg_id SERIAL PRIMARY KEY,
    sugg_text TEXT NOT NULL,
    uv_level VARCHAR(20),
    temp_level VARCHAR(10),
    is_raining BOOLEAN
);

CREATE TABLE IF NOT EXISTS sunscr_sugg (
    sunscr_id SERIAL PRIMARY KEY,
    sunscr_degree INT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS weather (
    weather_id SERIAL PRIMARY KEY,
    weather_name VARCHAR(10) NOT NULL,
    weather_icon_id INT NOT NULL
);

CREATE TABLE IF NOT EXISTS record (
    record_id SERIAL PRIMARY KEY,
    record_temp INT,
    record_humdi INT,
    record_uvi DECIMAL(5,2),
    record_lat INT,
    record_lon INT,
    record_timestamp TIMESTAMPTZ NOT NULL,
    weather_id INT REFERENCES weather(weather_id),
    device_uuid UUID REFERENCES user_device(device_uuid),
    sugg_id INT REFERENCES cloth_sugg(sugg_id),
    sunscr_id INT REFERENCES sunscr_sugg(sunscr_id)
);