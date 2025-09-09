-- Migración inicial: modelo de datos IPC Ushuaia

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    brand TEXT,
    category TEXT,
    UNIQUE(name, brand)
);

CREATE TABLE skus (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    description TEXT,
    pack_size FLOAT,
    pack_unit TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    UNIQUE(code)
);

CREATE INDEX idx_skus_product_id ON skus(product_id);

CREATE TABLE runs (
    id SERIAL PRIMARY KEY,
    run_date DATE NOT NULL,
    branch TEXT,
    status TEXT,
    UNIQUE(run_date, branch)
);

CREATE TABLE prices (
    id SERIAL PRIMARY KEY,
    sku_id INTEGER REFERENCES skus(id) ON DELETE CASCADE,
    run_id INTEGER REFERENCES runs(id) ON DELETE CASCADE,
    price_final FLOAT NOT NULL,
    promo TEXT,
    stock BOOLEAN,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(sku_id, run_id)
);

CREATE TABLE basket_items (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES products(id) ON DELETE CASCADE,
    monthly_qty_value FLOAT,
    monthly_qty_unit TEXT,
    notes TEXT
);

CREATE TABLE index_values (
    id SERIAL PRIMARY KEY,
    run_id INTEGER REFERENCES runs(id) ON DELETE CASCADE,
    cba_ae FLOAT,
    cba_family FLOAT,
    index_value FLOAT,
    var_mm FLOAT,
    var_ia FLOAT
);

CREATE TABLE logs (
    id SERIAL PRIMARY KEY,
    run_id INTEGER REFERENCES runs(id) ON DELETE CASCADE,
    level TEXT,
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
