CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    price NUMERIC(10, 2) NOT NULL
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER REFERENCES customers(id),
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount NUMERIC(10, 2) NOT NULL
);

CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER REFERENCES orders(id),
    product_id INTEGER REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(10, 2) NOT NULL
);

-- Seed Data
INSERT INTO customers (name, email) VALUES
    ('Acme Corp', 'contact@acme.com'),
    ('Globex Corporation', 'sales@globex.com'),
    ('Soylent Corp', 'info@soylent.com');

INSERT INTO products (name, category, price) VALUES
    ('Widget A', 'Widgets', 10.00),
    ('Widget B', 'Widgets', 15.00),
    ('Gadget X', 'Gadgets', 25.50),
    ('Gadget Y', 'Gadgets', 50.00);

INSERT INTO orders (customer_id, total_amount) VALUES
    (1, 12450.00),
    (2, 350.00),
    (1, 150.00);

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
    (1, 4, 249, 50.00),
    (2, 2, 10, 15.00),
    (2, 3, 2, 25.50),
    (3, 1, 15, 10.00);
