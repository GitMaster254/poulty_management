import math
import sqlite3
from datetime import datetime

DB_NAME = 'farm.db'


def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            item_description TEXT,
            quantity REAL DEFAULT 0,
            unit TEXT,
            price REAL,
            total_cost REAL NOT NULL
        )
    ''')

    expense_columns = {
        row['name'] for row in cursor.execute("PRAGMA table_info(expenses)")
    }
    if 'price' not in expense_columns:
        cursor.execute("ALTER TABLE expenses ADD COLUMN price REAL")
        cursor.execute('''
            UPDATE expenses
            SET price = total_cost / quantity
            WHERE quantity > 0
        ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS flock_growth (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            days_old INTEGER,
            bird_count INTEGER,
            mortalities INTEGER DEFAULT 0,
            feed_consumed_kg REAL DEFAULT 0,
            avg_weight_g REAL DEFAULT 0,
            notes TEXT
        )
    ''')

    conn.commit()
    conn.close()


def show_dashboard():
    print("\n" + "=" * 30 + " FARM DASHBOARD " + "=" * 30)
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT SUM(total_cost) FROM expenses")
        total_expenses = cursor.fetchone()[0] or 0.00

        cursor.execute("SELECT bird_count, mortalities FROM flock_growth ORDER BY id DESC LIMIT 1")
        last_growth = cursor.fetchone()

        live_count = last_growth['bird_count'] if last_growth else 0
        total_losses = last_growth['mortalities'] if last_growth else 0

        cursor.execute("SELECT SUM(feed_consumed_kg) FROM flock_growth")
        total_feed = cursor.fetchone()[0] or 0.0
    except sqlite3.Error as exc:
        print(f"❌ Database error: {exc}")
        conn.close()
        return
    finally:
        conn.close()

    print(f" Total Expenses: {total_expenses:,.2f}")
    print(f" Live Count:    {live_count} birds")
    print(f" Recent Losses: {total_losses} birds")
    print(f" Total Feed:    {total_feed:.1f} kg")
    print("=" * 76)


def add_expense():
    print("\n--- Log a New Expense ---")
    date_input = input("Enter Date (YYYY-MM-DD) [Press Enter for today]: ").strip()
    if not date_input:
        date_input = datetime.now().strftime('%Y-%m-%d')

    print("Categories: Stock, Feed, Equipment, Structures, Utilities, Other")
    category = input("Enter Category: ").strip()
    item_desc = input("Item Description (e.g. Starter Mash, Chick Drinkers): ").strip()

    try:
        qty = float(input("Quantity: ").strip())
        if not math.isfinite(qty) or qty <= 0:
            raise ValueError
    except ValueError:
        print("❌ Error: Quantity must be a number greater than zero.")
        return

    unit = input("Unit (e.g. bags, birds, pcs, litres - optional): ").strip()

    try:
        price = float(input("Unit Price: ").strip())
        if not math.isfinite(price) or price < 0:
            raise ValueError
    except ValueError:
        print("❌ Error: Unit Price must be a non-negative number.")
        return

    total_cost = qty * price
    if not math.isfinite(total_cost):
        print("❌ Error: Quantity multiplied by Unit Price is too large.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO expenses (date, category, item_description, quantity, unit, price, total_cost)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (date_input, category, item_desc, qty, unit, price, total_cost))
        conn.commit()
        print("✅ Expense logged successfully!")
    except sqlite3.Error as exc:
        print(f"❌ Database error: {exc}")
        conn.rollback()
    finally:
        conn.close()


def add_flock_record():
    print("\n--- Log Flock Growth & Health ---")
    date_input = input("Enter Date (YYYY-MM-DD) [Press Enter for today]: ").strip()
    if not date_input:
        date_input = datetime.now().strftime('%Y-%m-%d')

    try:
        days_old = int(input("Days Old: ").strip())
        bird_count = int(input("Current Live Bird Count: ").strip())
        losses = int(input("Mortalities/Losses today: ").strip() or 0)
        feed = float(input("Feed consumed today (kg): ").strip() or 0)
        weight = float(input("Average weight per bird (grams - optional): ").strip() or 0)
    except ValueError:
        print("❌ Error: Quantities and counts must be numbers.")
        return

    notes = input("Notes/Observations: ").strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO flock_growth (date, days_old, bird_count, mortalities, feed_consumed_kg, avg_weight_g, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (date_input, days_old, bird_count, losses, feed, weight, notes))
        conn.commit()
    except sqlite3.Error as exc:
        print(f"❌ Database error: {exc}")
        conn.rollback()
    finally:
        conn.close()

    print("✅ Flock record logged successfully!")


def edit_record():
    print("\n--- Edit Existing Records ---")
    print("1. Edit an Expense")
    print("2. Edit a Flock Growth Record")
    choice = input("Select what you want to edit (1-2): ").strip()

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        if choice == '1':
            cursor.execute("""
                SELECT id, date, category, item_description, quantity, unit, price, total_cost
                FROM expenses
                ORDER BY date DESC
                LIMIT 15
            """)
            rows = cursor.fetchall()
            if not rows:
                print("No expense records found to edit.")
                return

            print("\nRecent Expenses:")
            widths = (5, 12, 12, 25, 10, 12, 12, 12)
            headers = ('ID', 'Date', 'Category', 'Description', 'Qty', 'Unit', 'Price', 'Total')
            print(" | ".join(f"{header:<{width}}" for header, width in zip(headers, widths)))
            print("-" * (sum(widths) + 3 * (len(widths) - 1)))
            for r in rows:
                values = (
                    str(r['id']),
                    str(r['date']),
                    str(r['category']),
                    str(r['item_description'] or ''),
                    f"{(r['quantity'] or 0):,.2f}",
                    str(r['unit'] or ''),
                    f"{r['price']:,.2f}" if r['price'] is not None else 'N/A',
                    f"{r['total_cost']:,.2f}",
                )
                print(" | ".join(
                    f"{value[:width]:<{width}}"
                    for value, width in zip(values, widths)
                ))

            record_id = input("\nEnter the ID of the record you want to update: ").strip()
            cursor.execute("SELECT * FROM expenses WHERE id = ?", (record_id,))
            record = cursor.fetchone()
            if not record:
                print("❌ Invalid ID.")
                return

            print("\n--- Leave blank and hit Enter to KEEP current value ---")
            new_date = input(f"Date [{record['date']}]: ").strip() or record['date']
            new_cat = input(f"Category [{record['category']}]: ").strip() or record['category']
            new_desc = input(f"Description [{record['item_description']}]: ").strip() or record['item_description']
            current_qty = record['quantity'] if record['quantity'] is not None else 0
            qty_input = input(f"Quantity [{current_qty}]: ").strip()
            new_unit = input(f"Unit [{record['unit']}]: ").strip() or record['unit']
            price_display = record['price'] if record['price'] is not None else 'not set'
            price_input = input(f"Unit Price [{price_display}]: ").strip()
            try:
                new_qty = current_qty if not qty_input else float(qty_input)
                new_price = record['price'] if not price_input else float(price_input)
            except ValueError:
                print("❌ Error: Quantity and Unit Price must be valid numbers.")
                return

            if not math.isfinite(new_qty) or new_qty < 0:
                print("❌ Error: Quantity must be a non-negative number.")
                return
            if new_price is not None and (not math.isfinite(new_price) or new_price < 0):
                print("❌ Error: Unit Price must be a non-negative number.")
                return

            if qty_input or price_input:
                if new_price is None:
                    print("❌ Error: Enter a Unit Price before changing the quantity.")
                    return
                new_cost = new_qty * new_price
                if not math.isfinite(new_cost):
                    print("❌ Error: Quantity multiplied by Unit Price is too large.")
                    return
            else:
                new_cost = record['total_cost']

            cursor.execute('''
                UPDATE expenses
                SET date=?, category=?, item_description=?, quantity=?, unit=?, price=?, total_cost=?
                WHERE id=?
            ''', (new_date, new_cat, new_desc, new_qty, new_unit, new_price, new_cost, record_id))
            conn.commit()
            print("✅ Expense record updated successfully!")

        elif choice == '2':
            cursor.execute("SELECT id, date, days_old, bird_count, mortalities FROM flock_growth ORDER BY date DESC LIMIT 15")
            rows = cursor.fetchall()
            if not rows:
                print("No flock records found to edit.")
                return

            print("\nRecent Flock Records:")
            print(f"{'ID':<5} | {'Date':<12} | {'Age (Days)':<10} | {'Bird Count':<12} | {'Losses':<8}")
            print("-" * 55)
            for r in rows:
                print(f"{r['id']:<5} | {r['date']:<12} | {r['days_old']:<10} | {r['bird_count']:<12} | {r['mortalities']:<8}")

            record_id = input("\nEnter the ID of the record you want to update: ").strip()
            cursor.execute("SELECT * FROM flock_growth WHERE id = ?", (record_id,))
            record = cursor.fetchone()
            if not record:
                print("❌ Invalid ID.")
                return

            print("\n--- Leave blank and hit Enter to KEEP current value ---")
            new_date = input(f"Date [{record['date']}]: ").strip() or record['date']
            new_age = input(f"Days Old [{record['days_old']}]: ").strip() or record['days_old']
            new_count = input(f"Bird Count [{record['bird_count']}]: ").strip() or record['bird_count']
            new_losses = input(f"Losses [{record['mortalities']}]: ").strip() or record['mortalities']
            new_feed = input(f"Feed (kg) [{record['feed_consumed_kg']}]: ").strip() or record['feed_consumed_kg']
            new_weight = input(f"Avg Weight (g) [{record['avg_weight_g']}]: ").strip() or record['avg_weight_g']
            new_notes = input(f"Notes [{record['notes']}]: ").strip() or record['notes']

            cursor.execute('''
                UPDATE flock_growth
                SET date=?, days_old=?, bird_count=?, mortalities=?, feed_consumed_kg=?, avg_weight_g=?, notes=?
                WHERE id=?
            ''', (new_date, int(new_age), int(new_count), int(new_losses), float(new_feed), float(new_weight), new_notes, record_id))
            conn.commit()
            print("✅ Flock growth record updated successfully!")

        else:
            print("❌ Invalid choice.")
    except sqlite3.Error as exc:
        print(f"❌ Database error: {exc}")
        conn.rollback()
    finally:
        conn.close()


def main():
    init_db()
    while True:
        show_dashboard()
        print("1. Log New Expense")
        print("2. Log Daily Flock Status (Growth/Health)")
        print("3. Edit Existing Records")
        print("4. Exit")

        choice = input("\nSelect an option (1-4): ").strip()
        if choice == '1':
            add_expense()
        elif choice == '2':
            add_flock_record()
        elif choice == '3':
            edit_record()
        elif choice == '4':
            print("\nGoodbye! Happy farming! 🐓")
            break
        else:
            print("❌ Invalid option. Please select 1, 2, 3, or 4.")


if __name__ == "__main__":
    main()

if __name__ == '__main__':
    main()
