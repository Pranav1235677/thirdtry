import streamlit as st
import sqlite3
import pandas as pd
import random
import calendar

# Initialize SQLite database and create monthly tables
def init_db():
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    for month in calendar.month_name[1:]:  # January to December
        cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS {month} (
                Date TEXT,
                Category TEXT,
                Payment_Mode TEXT,
                Description TEXT,
                Amount_Paid REAL,
                Cashback REAL,
                Month TEXT
            )
        """)
    conn.commit()
    conn.close()

# Generate random expense data for a given month
def generate_data(month):
    categories = ["Bills", "Dining", "Groceries", "Investments", "Stationery", 
                  "Subscriptions", "Fruits & Vegetables", "School FEES", 
                  "Home Essentials", "Sports & Fitness"]
    payment_modes = ["Cash", "Wallet", "UPI", "Net Banking", "Credit Card", "Debit Card"]
    descriptions = [
        "Paid electricity bill", "Monthly groceries", "Dinner at a restaurant",
        "Investment in mutual funds", "School fees", "Gym subscription",
        "Office supplies", "Purchased fruits and vegetables", "Household items",
        "Annual sports membership"
    ]

    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    data = []
    days_in_month = 31 if month in ["January", "March", "May", "July", "August", "October", "December"] else 30
    days_in_month = 28 if month == "February" else days_in_month
    for _ in range(random.randint(15, 20)):  # Generate 15-20 random expenses
        day = random.randint(1, days_in_month)
        date = f"2024-{list(calendar.month_name).index(month):02}-{day:02}"
        category = random.choice(categories)
        payment_mode = random.choice(payment_modes)
        description = random.choice(descriptions)
        amount_paid = round(random.uniform(50, 500), 2)
        cashback = round(random.uniform(0, 20), 2)
        data.append((date, category, payment_mode, description, amount_paid, cashback, month))
    
    cursor.executemany(f"INSERT INTO {month} VALUES (?, ?, ?, ?, ?, ?, ?)", data)
    conn.commit()
    conn.close()
    return pd.DataFrame(data, columns=["Date", "Category", "Payment_Mode", "Description", "Amount_Paid", "Cashback", "Month"])

# Combine all monthly tables into a single view for querying
def combine_all_months():
    conn = sqlite3.connect('expenses.db')
    cursor = conn.cursor()
    combined_query = "SELECT * FROM January"
    for month in calendar.month_name[2:]:  # February to December
        combined_query += f" UNION ALL SELECT * FROM {month}"
    cursor.execute(f"CREATE VIEW IF NOT EXISTS expenses AS {combined_query}")
    conn.commit()
    conn.close()

# Query data from the database
def query_data(query):
    try:
        conn = sqlite3.connect('expenses.db')
        result = pd.read_sql_query(query, conn)
        conn.close()
        return result
    except Exception as e:
        st.error(f"An error occurred while executing the query: {e}")
        return pd.DataFrame()

# Streamlit app
def main():
    st.title("Personal Expense Tracker")

    # Database initialization
    init_db()

    # Sidebar menu
    menu = ["Generate Data", "Spending Insights", "Custom Query"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Generate Data":
        st.subheader("Generate Expense Data")
        month = st.text_input("Enter the month (e.g., January):", "January")
        if st.button("Generate"):
            if month in calendar.month_name[1:]:
                df = generate_data(month)
                combine_all_months()
                st.success(f"Data for {month} generated and loaded into the database!")
                st.write(df)
            else:
                st.error("Invalid month entered. Please check!")

    elif choice == "Spending Insights":
        st.subheader("Predefined SQL Queries")
        queries = {
            "Total Spending by Category": "SELECT Category, SUM(Amount_Paid) AS Total_Spending FROM expenses GROUP BY Category",
            "Monthly Spending Trend": "SELECT Month, SUM(Amount_Paid) AS Total_Spending FROM expenses GROUP BY Month",
            "Total Cashback Earned": "SELECT SUM(Cashback) AS Total_Cashback FROM expenses",
            "Payment Mode Distribution": "SELECT Payment_Mode, COUNT(*) AS Count FROM expenses GROUP BY Payment_Mode",
            "Highest Single Expense": "SELECT * FROM expenses ORDER BY Amount_Paid DESC LIMIT 1",
            "Average Cashback by Category": "SELECT Category, AVG(Cashback) AS Average_Cashback FROM expenses GROUP BY Category"
        }
        query_choice = st.selectbox("Select a query to run", list(queries.keys()))
        if st.button("Run Query"):
            query_result = query_data(queries[query_choice])
            if not query_result.empty:
                st.write(query_result)
            else:
                st.warning("No data available for this query!")

    elif choice == "Custom Query":
        st.subheader("Run a Custom SQL Query")
        custom_query = st.text_area("Enter your SQL query here:")
        if st.button("Execute Query"):
            query_result = query_data(custom_query)
            if not query_result.empty:
                st.write(query_result)
            else:
                st.warning("No data available for this query!")

if _name_ == "_main_":
    main()