CREATE DATABASE SalesDB;

use SalesDB;
-- BRANCHES
CREATE TABLE branches (
    branch_id         INT PRIMARY KEY IDENTITY(1,1),
    branch_name       VARCHAR(100) NOT NULL UNIQUE,
    branch_admin_name VARCHAR(100) NOT NULL
);

-- CUSTOMER SALES
CREATE TABLE customer_sales (
    sale_id         INT PRIMARY KEY IDENTITY(1,1),
    branch_id       INT NOT NULL,
    date            DATE NOT NULL,
    name            VARCHAR(100) NOT NULL,
    mobile_number   VARCHAR(15) NOT NULL,
    product_name    VARCHAR(30) NOT NULL,
    gross_sales     DECIMAL(12,2) NOT NULL,
    received_amount DECIMAL(12,2) DEFAULT 0,
    pending_amount  DECIMAL(12,2) DEFAULT 0,
    status          VARCHAR(10)
                    DEFAULT 'Open'
                    CHECK (status IN ('Open','Close')),
    CONSTRAINT UQ_mobile UNIQUE (mobile_number),
    CONSTRAINT FK_branch FOREIGN KEY (branch_id)
    REFERENCES branches(branch_id)
);

-- USERS
CREATE TABLE users (
    user_id   INT PRIMARY KEY IDENTITY(1,1),
    username  VARCHAR(100) NOT NULL,
    password  VARCHAR(255) NOT NULL,
    branch_id INT,
    role      VARCHAR(20) NOT NULL
              CHECK (role IN ('Super Admin','Admin')),
    email     VARCHAR(255) UNIQUE NOT NULL,
    CONSTRAINT FK_user_branch FOREIGN KEY (branch_id)
    REFERENCES branches(branch_id)
);

-- PAYMENT SPLITS
CREATE TABLE payment_splits (
    payment_id     INT PRIMARY KEY IDENTITY(1,1),
    sale_id        INT NOT NULL,
    payment_date   DATE NOT NULL,
    amount_paid    DECIMAL(12,2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    CONSTRAINT FK_sale FOREIGN KEY (sale_id)
    REFERENCES customer_sales(sale_id)
);

-- TRIGGER
CREATE TRIGGER after_payment_insert
ON payment_splits
AFTER INSERT
AS
BEGIN
    UPDATE customer_sales
    SET received_amount = (
        SELECT COALESCE(SUM(amount_paid), 0)
        FROM payment_splits
        WHERE sale_id = customer_sales.sale_id
    )
    WHERE sale_id IN (
        SELECT sale_id FROM INSERTED
    );

    UPDATE customer_sales
    SET
        pending_amount = (
            SELECT SUM(c2.gross_sales - c2.received_amount)
            FROM customer_sales c2
            WHERE c2.sale_id <= customer_sales.sale_id
        ),
        status = CASE
            WHEN (gross_sales - received_amount) <= 0
            THEN 'Close'
            ELSE 'Open'
        END;
END;

-- DATA
INSERT INTO branches (branch_name, branch_admin_name)
VALUES
('Chennai',   'Ravi Kumar'),
('Delhi',     'Priya Sharma'),
('Bangalore', 'Kumar Das');

INSERT INTO users
(username, password, branch_id, role, email)
VALUES
('superadmin',    'pass123', NULL, 'Super Admin', 'super@sales.com'),
('chennai_admin', 'pass123', 1,    'Admin',       'chennai@sales.com'),
('delhi_admin',   'pass123', 2,    'Admin',       'delhi@sales.com');

INSERT INTO customer_sales
(branch_id, date, name,
 mobile_number, product_name, gross_sales)
VALUES
(1, '2024-01-15', 'Arun',  '9876543210', 'DS',  50000),
(1, '2024-01-16', 'Meera', '8765432109', 'DA',  30000),
(2, '2024-01-17', 'Raj',   '7654321098', 'FSD', 60000),
(2, '2024-01-18', 'Priya', '6543210987', 'BA',  45000),
(3, '2024-01-19', 'Kumar', '5432109876', 'DS',  55000);

INSERT INTO payment_splits
(sale_id, payment_date, amount_paid, payment_method)
VALUES
(1, '2024-01-15', 48000, 'Cash'),
(2, '2024-01-16', 27000, 'UPI'),
(3, '2024-01-17', 60000, 'Card'),
(4, '2024-01-18', 40000, 'Cash'),
(5, '2024-01-19', 50000, 'UPI');


SELECT sale_id, name, gross_sales,
       received_amount, pending_amount, status
FROM customer_sales;

DROP PROCEDURE IF EXISTS GetSalesData;


CREATE PROCEDURE GetSalesData
    @username VARCHAR(100),
    @password VARCHAR(255)
AS
BEGIN
    DECLARE @role      VARCHAR(20);
    DECLARE @branch_id INT;

    SELECT
        @role      = role,
        @branch_id = branch_id
    FROM users
    WHERE username = @username
    AND   password = @password;

    IF @role IS NULL
    BEGIN
        SELECT 'Invalid username or password!' AS message;
        RETURN;
    END

    SELECT
        cs.sale_id,
        b.branch_name,
        cs.name,
        cs.gross_sales,
        cs.received_amount,
        cs.pending_amount,
        cs.status
    FROM customer_sales cs
    JOIN branches b
    ON cs.branch_id = b.branch_id
    WHERE
        @role = 'Super Admin'
        OR cs.branch_id = @branch_id
    ORDER BY cs.sale_id;
END;


EXEC GetSalesData
    @username = 'superadmin',
    @password = 'pass123';

-- Chennai Admin
EXEC GetSalesData
    @username = 'chennai_admin',
    @password = 'pass123';

use SalesDB;
 Delete from payment_splits;
 Delete from customer_sales;
 Delete from users;
 Delete from branches;


DBCC checkident ('payment_splits',RESEED,0);
DBCC checkident ('customer_sales',RESEED,0);
DBCC checkident ('users',RESEED,0);
DBCC checkident ('branches',RESEED,0);

select * from users;
