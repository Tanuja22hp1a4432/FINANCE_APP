import sqlite3
import getpass
import shutil
import os
from datetime import datetime
from tabulate import tabulate

DB_NAME = "finance.db"

# 1. Create tables (users, transactions, budgets)
def create_tables():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            category TEXT,
            type TEXT,
            date TEXT,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            category TEXT,
            month INTEGER,
            year INTEGER,
            limit_amount REAL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    """)
    conn.commit()
    conn.close()

# 2. User Registration
def register_user():
    username = input("Enter new username: ")
    password = getpass.getpass("Enter password: ")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        print("✅ Registration successful!")
    except sqlite3.IntegrityError:
        print("⚠ Username already exists.")
    conn.close()

# 3. Login
def login_user():
    username = input("Enter username: ")
    password = getpass.getpass("Enter password: ")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT id FROM users WHERE username = ? AND password = ?", (username, password))
    user = c.fetchone()
    conn.close()

    if user:
        print(f"✅ Welcome, {username}!")
        return user[0]
    else:
        print("❌ Invalid credentials.")
        return None

# 4. Add Transaction
def add_transaction(user_id):
    try:
        amount = float(input("Enter amount: "))
    except ValueError:
        print("⚠ Invalid amount.")
        return

    category = input("Enter category (e.g., Food, Rent, Salary): ")
    t_type = input("Enter type (income/expense): ").lower()

    if t_type not in ["income", "expense"]:
        print("⚠ Type must be 'income' or 'expense'.")
        return

    date = input("Enter date (YYYY-MM-DD) or leave blank for today: ")
    if date.strip() == "":
        date = datetime.today().strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO transactions (user_id, amount, category, type, date)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, amount, category, t_type, date))
    conn.commit()
    conn.close()

    print("✅ Transaction added successfully!")
    if t_type == "expense":
        check_budget_alert(user_id, category, date)

# 5. View Transactions
def view_transactions(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT amount, category, type, date 
        FROM transactions 
        WHERE user_id = ? 
        ORDER BY date DESC
    """, (user_id,))
    rows = c.fetchall()
    conn.close()

    if rows:
        print(tabulate(rows, headers=["Amount", "Category", "Type", "Date"], tablefmt="grid"))
    else:
        print("No transactions found.")

# 6. Monthly Report
def monthly_report(user_id):
    try:
        year = int(input("Enter year (YYYY): "))
        month = int(input("Enter month (1-12): "))
    except ValueError:
        print("⚠ Invalid year or month.")
        return

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT type, SUM(amount)
        FROM transactions
        WHERE user_id = ?
        AND strftime('%Y', date) = ?
        AND strftime('%m', date) = ?
        GROUP BY type
    """, (user_id, str(year), f"{month:02d}"))

    data = dict(c.fetchall())
    conn.close()

    income = data.get("income", 0)
    expenses = data.get("expense", 0)
    savings = income - expenses

    print(f"\n📅 Monthly Report: {year}-{month:02d}")
    print(f"Total Income:   ₹{income}")
    print(f"Total Expenses: ₹{expenses}")
    print(f"Savings:        ₹{savings}")

# 7. Yearly Report
def yearly_report(user_id):
    try:
        year = int(input("Enter year (YYYY): "))
    except ValueError:
        print("⚠ Invalid year.")
        return

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT type, SUM(amount)
        FROM transactions
        WHERE user_id = ?
        AND strftime('%Y', date) = ?
        GROUP BY type
    """, (user_id, str(year)))

    data = dict(c.fetchall())
    conn.close()

    income = data.get("income", 0)
    expenses = data.get("expense", 0)
    savings = income - expenses

    print(f"\n📅 Yearly Report: {year}")
    print(f"Total Income:   ₹{income}")
    print(f"Total Expenses: ₹{expenses}")
    print(f"Savings:        ₹{savings}")

# 8. Set Budget
def set_budget(user_id):
    category = input("Enter category for budget: ")
    try:
        limit_amount = float(input("Enter budget limit amount: "))
        year = int(input("Enter year (YYYY): "))
        month = int(input("Enter month (1-12): "))
    except ValueError:
        print("⚠ Invalid input.")
        return

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        INSERT INTO budgets (user_id, category, month, year, limit_amount)
        VALUES (?, ?, ?, ?, ?)
    """, (user_id, category, month, year, limit_amount))
    conn.commit()
    conn.close()
    print(f"✅ Budget set for {category} - ₹{limit_amount} for {month}/{year}")

# 9. Check Budget Alerts
def check_budget_alert(user_id, category, date):
    year = int(date.split("-")[0])
    month = int(date.split("-")[1])

    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""
        SELECT limit_amount FROM budgets
        WHERE user_id = ? AND category = ? AND month = ? AND year = ?
    """, (user_id, category, month, year))
    budget = c.fetchone()

    if budget:
        limit_amount = budget[0]
        c.execute("""
            SELECT SUM(amount) FROM transactions
            WHERE user_id = ? AND category = ? AND type = 'expense'
            AND strftime('%Y', date) = ? AND strftime('%m', date) = ?
        """, (user_id, category, str(year), f"{month:02d}"))
        total_spent = c.fetchone()[0] or 0

        if total_spent > limit_amount:
            print(f"⚠ ALERT: You have exceeded your budget for '{category}' ({total_spent} > {limit_amount})")
    conn.close()

# 10. Backup Database
def backup_data():
    backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    try:
        shutil.copy(DB_NAME, backup_file)
        print(f"✅ Backup created: {backup_file}")
    except Exception as e:
        print(f"❌ Backup failed: {e}")

# 11. Restore Database
def restore_data():
    backup_file = input("Enter backup file name to restore: ")
    if not os.path.exists(backup_file):
        print("❌ Backup file not found.")
        return
    try:
        shutil.copy(backup_file, DB_NAME)
        print("✅ Database restored successfully.")
    except Exception as e:
        print(f"❌ Restore failed: {e}")

# 12. User Menu
def user_menu(user_id):
    while True:
        print("\n==== Finance Menu ====")
        print("1. Add Transaction")
        print("2. View Transactions")
        print("3. Monthly Report")
        print("4. Yearly Report")
        print("5. Set Budget")
        print("6. Backup Data")
        print("7. Restore Data")
        print("8. Logout")
        choice = input("Enter choice: ")

        if choice == "1":
            add_transaction(user_id)
        elif choice == "2":
            view_transactions(user_id)
        elif choice == "3":
            monthly_report(user_id)
        elif choice == "4":
            yearly_report(user_id)
        elif choice == "5":
            set_budget(user_id)
        elif choice == "6":
            backup_data()
        elif choice == "7":
            restore_data()
        elif choice == "8":
            print("🔒 Logged out.")
            break
        else:
            print("⚠ Invalid choice, try again.")

# 13. Main Menu
def main():
    create_tables()
    while True:
        print("\n==== Personal Finance App ====")
        print("1. Register")
        print("2. Login")
        print("3. Exit")
        choice = input("Enter choice: ")

        if choice == "1":
            register_user()
        elif choice == "2":
            user_id = login_user()
            if user_id:
                user_menu(user_id)
        elif choice == "3":
            print("👋 Goodbye!")
            break
        else:
            print("⚠ Invalid choice, try again.")

if __name__ == "__main__":
    main()
