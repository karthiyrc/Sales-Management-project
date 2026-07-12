import pyodbc
import pandas as pd

print("Connecting...")

conn = pyodbc.connect(
    "DRIVER={SQL Server};"
    "SERVER=DESKTOP-7TKHK5P\\SQLEXPRESS;"
    "DATABASE=SalesDB;"
    "Trusted_Connection=yes;"
)
cursor = conn.cursor()

print("Importing branches...")
df = pd.read_csv(
    r"C:\Users\SPLPT 274\Downloads\branches.csv"
)
for _, row in df.iterrows():
    cursor.execute("""
        INSERT INTO branches
        (branch_name, branch_admin_name)
        VALUES (?, ?)
    """, (
        row['branch_name'],
        row['branch_admin_name']
    ))
conn.commit()
print(f" {len(df)} branches done!")

print("Importing users...")
df = pd.read_csv(
    r"C:\Users\SPLPT 274\Downloads\users.csv"
)
for _, row in df.iterrows():
    branch_id = None \
        if pd.isna(row['branch_id']) \
        else int(row['branch_id'])
    cursor.execute("""
        INSERT INTO users
        (username, password, branch_id,
         role, email)
        VALUES (?, ?, ?, ?, ?)
    """, (
        row['username'],
        row['password'],
        branch_id,
        row['role'],
        row['email']
    ))
conn.commit()
print(f" {len(df)} users done!")

print("Importing customer_sales...")
df = pd.read_csv(
    r"C:\Users\SPLPT 274\Downloads\customer_sales.csv"
)
for _, row in df.iterrows():
    cursor.execute("""
        INSERT INTO customer_sales
        (branch_id, date, name,
         mobile_number, product_name,
         gross_sales, received_amount,
         status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        int(row['branch_id']),
        row['date'],
        row['name'],
        str(row['mobile_number']),
        row['product_name'],
        float(row['gross_sales']),
        float(row['received_amount']),
        row['status']
    ))
conn.commit()
print(f" {len(df)} sales done!")

print("Importing payment_splits...")
df = pd.read_csv(
    r"C:\Users\SPLPT 274\Downloads\payment_splits.csv"
)
for _, row in df.iterrows():
    cursor.execute("""
        INSERT INTO payment_splits
        (sale_id, payment_date,
         amount_paid, payment_method)
        VALUES (?, ?, ?, ?)
    """, (
        int(row['sale_id']),
        row['payment_date'],
        float(row['amount_paid']),
        row['payment_method']
    ))
conn.commit()
print(f" {len(df)} payments done!")

conn.close()
print("\n All imported successfully!")
