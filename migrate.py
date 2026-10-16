import sqlite3
from datetime import datetime

# Exact raw data extracted from your Excel screenshot layout
excel_inventory = [
    {"date": "10/10/2026", "item": "LIQUID PARAFFIN MEDISEL", "unit": "50 ml", "qty": 1, "price": "Ksh 100.00", "total": "Ksh 100.00"},
    {"date": "10/10/2026", "item": "CHICKSTART VETCARE", "unit": "30 gm", "qty": 1, "price": "Ksh 80.00", "total": "Ksh 80.00"},
    {"date": "10/10/2026", "item": "UNGA F/G B/STARTER CRUMB", "unit": "10 kg", "qty": 1, "price": "Ksh 930.00", "total": "Ksh 930.00"},
    {"date": "10/10/2026", "item": "CHICKEN DRINKER OVAL", "unit": "1 Lt", "qty": 1, "price": "Ksh 160.00", "total": "Ksh 160.00"},
    {"date": "10/10/2026", "item": "CHICKEN FEEDER", "unit": "1.5 kg", "qty": 2, "price": "Ksh 250.00", "total": "Ksh 500.00"}
]

excel_utilities = [
    {"date": "10/10/2026", "item": "Transport", "cost": "Ksh 200.00"},
    {"date": "10/10/2026", "item": "Eletricity Bill", "cost": "Ksh 300.00"}
]

def clean_currency(val_str):
    """Removes currency symbols, spaces, and signs to ensure mathematical values."""
    if not val_str:
        return 0.0
    cleaned = val_str.replace("Ksh", "").replace("-", "").strip()
    return float(cleaned)

def format_date(date_str):
    """Converts DD/MM/YYYY to database-friendly YYYY-MM-DD standard format."""
    try:
        dt = datetime.strptime(date_str, "%d/%m/%Y")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        return date_str

# Connect to database
conn = sqlite3.connect('farm.db')
cursor = conn.cursor()

print("🚀 Starting data cleaning and transfer from Excel to SQLite...")

# 1. Migrate Inventory Section
for row in excel_inventory:
    clean_date = format_date(row["date"])
    p_val = clean_currency(row["price"])
    t_val = clean_currency(row["total"])
    
    cursor.execute('''
        INSERT INTO expenses (date, category, item_description, quantity, unit, price, total_cost)
        VALUES (?, 'Inventory', ?, ?, ?, ?, ?)
    ''', (clean_date, row["item"], row["qty"], row["unit"], p_val, t_val))

# 2. Migrate Utilities Section
for row in excel_utilities:
    clean_date = format_date(row["date"])
    t_val = clean_currency(row["cost"])
    
    cursor.execute('''
        INSERT INTO expenses (date, category, item_description, quantity, unit, price, total_cost)
        VALUES (?, 'Utilities', ?, 1, 'pcs', ?, ?)
    ''', (clean_date, row["item"], t_val, t_val))

conn.commit()
conn.close()
print("🎉 Success! All Excel data has been cleaned and migrated into your expenses table.")
