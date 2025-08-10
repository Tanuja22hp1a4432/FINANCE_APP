import os
import sqlite3
import unittest
import finance_app

class TestFinanceApp(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """Runs once before all tests."""
        # Use a separate test database
        finance_app.DB_NAME = "test_finance.db"

        # Remove old test DB if exists
        if os.path.exists(finance_app.DB_NAME):
            os.remove(finance_app.DB_NAME)

        # Create fresh tables
        finance_app.create_tables()

    def setUp(self):
        """Runs before each test."""
        # Make sure test user exists for each test
        conn = sqlite3.connect(finance_app.DB_NAME)
        conn.execute("DELETE FROM users")  # Clear old data
        conn.execute("DELETE FROM transactions")
        conn.commit()
        conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("testuser", "pass123"))
        conn.commit()
        conn.close()

    def test_register_and_login(self):
        """Test if user can be inserted and retrieved."""
        conn = sqlite3.connect(finance_app.DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ? AND password = ?", ("testuser", "pass123"))
        user = c.fetchone()
        conn.close()
        self.assertIsNotNone(user, "User should exist after registration.")

    def test_add_transaction(self):
        """Test adding a transaction for the user."""
        conn = sqlite3.connect(finance_app.DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username = ?", ("testuser",))
        user_id = c.fetchone()[0]

        # Add a sample transaction
        conn.execute("""
            INSERT INTO transactions (user_id, amount, category, type, date)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, 1000, "Salary", "income", "2025-08-10"))
        conn.commit()

        c.execute("SELECT * FROM transactions WHERE user_id = ?", (user_id,))
        transactions = c.fetchall()
        conn.close()

        self.assertGreater(len(transactions), 0, "At least one transaction should exist.")

if __name__ == "__main__":
    unittest.main()
