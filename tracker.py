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
            total_cost REAL NOT NULL
        )
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
        qty = float(input("Quantity (or press Enter to skip): ").strip() or 0)
    except ValueError:
        qty = 0.0

    unit = input("Unit (e.g. bags, birds, pcs, litres - optional): ").strip()

    try:
        cost = float(input("Total Cost: ").strip())
    except ValueError:
        print("❌ Error: Total Cost must be a valid number.")
        return

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT INTO expenses (date, category, item_description, quantity, unit, total_cost)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (date_input, category, item_desc, qty, unit, cost))
        conn.commit()
    except sqlite3.Error as exc:
        print(f"❌ Database error: {exc}")
        conn.rollback()
    finally:
        conn.close()

    print("✅ Expense logged successfully!")


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
            cursor.execute("SELECT id, date, category, item_description, total_cost FROM expenses ORDER BY date DESC LIMIT 15")
            rows = cursor.fetchall()
            if not rows:
                print("No expense records found to edit.")
                return

            print("\nRecent Expenses:")
            print(f"{'ID':<5} | {'Date':<12} | {'Category':<12} | {'Description':<25} | {'Cost':<10}")
            print("-" * 70)
            for r in rows:
                print(f"{r['id']:<5} | {r['date']:<12} | {r['category']:<12} | {r['item_description']:<25} | {r['total_cost']:<10.2f}")

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
            new_qty = input(f"Quantity [{record['quantity']}]: ").strip() or record['quantity']
            new_unit = input(f"Unit [{record['unit']}]: ").strip() or record['unit']
            new_cost = input(f"Total Cost [{record['total_cost']}]: ").strip() or record['total_cost']

            cursor.execute('''
                UPDATE expenses
                SET date=?, category=?, item_description=?, quantity=?, unit=?, total_cost=?
                WHERE id=?
            ''', (new_date, new_cat, new_desc, float(new_qty), new_unit, float(new_cost), record_id))
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
