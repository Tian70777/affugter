CREATE TABLE IF NOT EXISTS Humidity (
    id SERIAL PRIMARY KEY,
    percent NUMERIC(5,2) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS Electricity_Prices (
    id SERIAL PRIMARY KEY,
    DKK_per_kWh NUMERIC(10,4) NOT NULL,
    time_start TIMESTAMPTZ NOT NULL,
    time_end TIMESTAMPTZ NOT NULL,
    Pris_inkl_VAT NUMERIC(10,4) NOT NULL,
    CONSTRAINT unique_price_period UNIQUE (time_start, time_end)
);

CREATE TABLE IF NOT EXISTS Humidifier_State (
    id SERIAL PRIMARY KEY,
    state BOOLEAN NOT NULL,
    reason TEXT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE Humidity
ADD COLUMN IF NOT EXISTS temperature NUMERIC;

-- Zigbee integration: mark which sensor each reading came from.
-- Existing rows default to 'dht11' so nothing breaks; the MQTT catcher
-- will insert new rows stamped 'zigbee'.
ALTER TABLE Humidity
ADD COLUMN IF NOT EXISTS source TEXT NOT NULL DEFAULT 'dht11';


ALTER TABLE Electricity_Prices
DROP COLUMN IF EXISTS Pris_inkl_VAT;

CREATE TABLE IF NOT EXISTS errors (
    id SERIAL PRIMARY KEY,
    error_type TEXT,
    error_message TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE errors OWNER TO sascha;
