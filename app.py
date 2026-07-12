
import streamlit as st
import pyodbc
import pandas as pd
from datetime import date


# DATABASE CONNECTION


def get_connection():
    conn = pyodbc.connect(
        "DRIVER={SQL Server};"
        "SERVER=DESKTOP-7TKHK5P\\SQLEXPRESS;"
        "DATABASE=SalesDB;"
        "Trusted_Connection=yes;"
    )
    return conn

# ═══════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════

def get_branches():
    conn = get_connection()
    df = pd.read_sql(
        "SELECT branch_id, branch_name FROM branches ORDER BY branch_name",
        conn
    )
    conn.close()
    return df

def get_products():
    conn = get_connection()
    df = pd.read_sql(
        "SELECT DISTINCT product_name FROM customer_sales ORDER BY product_name",
        conn
    )
    conn.close()
    return df['product_name'].tolist()

def login(username, password):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role, branch_id
        FROM users
        WHERE username = ?
        AND password = ?
    """, (username, password))
    result = cursor.fetchone()
    conn.close()
    if result:
        return result[0], result[1]
    return None, None

def get_sales_data(role, branch_id):
    conn = get_connection()
    if role == "Super Admin":
        query = """
            SELECT
                cs.sale_id,
                b.branch_name,
                cs.date,
                cs.name,
                cs.mobile_number,
                cs.product_name,
                cs.gross_sales,
                cs.received_amount,
                (cs.gross_sales - cs.received_amount) AS pending_amount,
                cs.status
            FROM customer_sales cs
            JOIN branches b ON cs.branch_id = b.branch_id
            ORDER BY cs.sale_id
        """
        df = pd.read_sql(query, conn)
    else:
        query = """
            SELECT
                cs.sale_id,
                b.branch_name,
                cs.date,
                cs.name,
                cs.mobile_number,
                cs.product_name,
                cs.gross_sales,
                cs.received_amount,
                (cs.gross_sales - cs.received_amount) AS pending_amount,
                cs.status
            FROM customer_sales cs
            JOIN branches b ON cs.branch_id = b.branch_id
            WHERE cs.branch_id = ?
            ORDER BY cs.sale_id
        """
        df = pd.read_sql(query, conn, params=[branch_id])
    conn.close()
    return df

def get_pending_sales(role, branch_id):
    conn = get_connection()
    if role == "Super Admin":
        query = """
            SELECT
                cs.sale_id,
                cs.name,
                b.branch_name,
                (cs.gross_sales - cs.received_amount) AS pending_amount
            FROM customer_sales cs
            JOIN branches b ON cs.branch_id = b.branch_id
            WHERE cs.status = 'Open'
            ORDER BY cs.sale_id
        """
        df = pd.read_sql(query, conn)
    else:
        query = """
            SELECT
                cs.sale_id,
                cs.name,
                b.branch_name,
                (cs.gross_sales - cs.received_amount) AS pending_amount
            FROM customer_sales cs
            JOIN branches b ON cs.branch_id = b.branch_id
            WHERE cs.status = 'Open'
            AND cs.branch_id = ?
            ORDER BY cs.sale_id
        """
        df = pd.read_sql(query, conn, params=[branch_id])
    conn.close()
    return df


# PAGE CONFIG


st.set_page_config(
    page_title="Sales Management System",
    page_icon="💼",
    layout="wide"
)

# SESSION STATE


if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "role" not in st.session_state:
    st.session_state.role = None
if "branch_id" not in st.session_state:
    st.session_state.branch_id = None
if "username" not in st.session_state:
    st.session_state.username = None
if "page" not in st.session_state:
    st.session_state.page = "Dashboard & Reports"


# LOGIN PAGE


def show_login_page():
    st.title("Sales Management System")
    st.subheader("Welcome to the Super admin Login Page")
    st.info("Please login to check the customer sales report")
    st.markdown("---")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if username and password:
            role, branch_id = login(username, password)
            if role:
                st.session_state.logged_in = True
                st.session_state.role      = role
                st.session_state.branch_id = branch_id
                st.session_state.username  = username
                st.rerun()
            else:
                st.error("Invalid username or password!")
        else:
            st.warning("Please enter username and password!")


# SIDEBAR


def show_sidebar():
    with st.sidebar:
        st.markdown("## Navigation")
        st.markdown("**Go to**")

        if st.button("📊 Dashboard & Reports", use_container_width=True):
            st.session_state.page = "Dashboard & Reports"
            st.rerun()

        if st.button("➕ Data Entry Workspace", use_container_width=True):
            st.session_state.page = "Data Entry Workspace"
            st.rerun()

        if st.button("🔍 Advanced SQL Engine", use_container_width=True):
            st.session_state.page = "Advanced SQL Engine"
            st.rerun()

        st.markdown("---")
        st.markdown(f"👤 **User:** {st.session_state.username}")
        st.markdown(f"🔑 **Role:** {st.session_state.role}")
        st.markdown("---")

        if st.button("🚪 Log Out", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.role      = None
            st.session_state.branch_id = None
            st.session_state.username  = None
            st.session_state.page      = "Dashboard & Reports"
            st.rerun()


# PAGE 1 — DASHBOARD & REPORTS


def show_dashboard():
    st.title("📊 Dashboard & Reports")
    st.markdown("---")

    df = get_sales_data(
        st.session_state.role,
        st.session_state.branch_id
    )

    # FILTERS
    st.subheader("🔍 Filters")
    col1, col2, col3, col4 = st.columns(4)

    branches_df  = get_branches()
    branch_names = ["All"] + branches_df['branch_name'].tolist()
    products     = ["All"] + get_products()

    with col1:
        branch_filter = st.selectbox("Branch Name", branch_names)
    with col2:
        product_filter = st.selectbox("Product Name", products)
    with col3:
        start_date = st.date_input("Start Date", value=None)
    with col4:
        end_date = st.date_input("End Date", value=None)

    # APPLY FILTERS
    filtered_df = df.copy()

    if branch_filter != "All":
        filtered_df = filtered_df[filtered_df["branch_name"] == branch_filter]
    if product_filter != "All":
        filtered_df = filtered_df[filtered_df["product_name"] == product_filter]
    if start_date:
        filtered_df = filtered_df[
            pd.to_datetime(filtered_df["date"]) >= pd.to_datetime(start_date)
        ]
    if end_date:
        filtered_df = filtered_df[
            pd.to_datetime(filtered_df["date"]) <= pd.to_datetime(end_date)
        ]

    # KPI METRICS
    st.markdown("---")
    st.subheader("📈 KPI Summary")

    total_revenue  = filtered_df["gross_sales"].sum()
    total_received = filtered_df["received_amount"].sum()
    total_pending  = filtered_df["pending_amount"].sum()
    pending_pct    = (total_pending / total_revenue * 100) if total_revenue > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Overall Revenue",  f"₹{total_revenue:,.0f}")
    with col2:
        st.metric("✅ Total Received",   f"₹{total_received:,.0f}")
    with col3:
        st.metric("⏳ Total Pending",    f"₹{total_pending:,.0f}")
    with col4:
        st.metric("📉 Pending %",        f"{pending_pct:.1f}%")

    # TABLE
    st.markdown("---")
    st.subheader(f"📋 Sales Data ({len(filtered_df)} records)")
    st.dataframe(filtered_df, use_container_width=True)

    csv = filtered_df.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name="sales_data.csv",
        mime="text/csv"
    )


# PAGE 2 — DATA ENTRY WORKSPACE


def show_data_entry():
    st.title("📝 Operations Record Creator")
    st.markdown("---")

    tab1, tab2 = st.tabs([
        "➕ Add New Sales Entry",
        "💳 Log Payment Split Details"
    ])

    # TAB 1: NEW SALES ENTRY
    with tab1:
        st.subheader("New Sale Generation")

        branches_df = get_branches()

        if st.session_state.role == "Admin":
            own_branch = branches_df[
                branches_df['branch_id'] == st.session_state.branch_id
            ]['branch_name'].values[0]
            branch_name = st.selectbox("Select Target Branch", [own_branch])
        else:
            branch_name = st.selectbox(
                "Select Target Branch",
                branches_df['branch_name'].tolist()
            )

        col1, col2 = st.columns(2)

        with col1:
            student_name = st.text_input("Student Name")
            mobile       = st.text_input("Mobile Number")
            gross_sales  = st.number_input(
                "Gross Sales Amount (₹)",
                min_value=0.0,
                format="%.2f"
            )

        with col2:
            course       = st.text_input("Select Course Name")
            joining_date = st.date_input("Joining Date", value=date.today())
            status       = st.selectbox("Initial Order Status", ["Open", "Close"])

        if st.button("🚀 Publish Sale Entry", use_container_width=True):
            if student_name and mobile and course:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()

                    branch_id = int(branches_df[
                        branches_df['branch_name'] == branch_name
                    ]['branch_id'].values[0])

                    cursor.execute("""
                        INSERT INTO customer_sales
                        (branch_id, date, name, mobile_number,
                         product_name, gross_sales, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (branch_id, joining_date, student_name,
                          mobile, course, gross_sales, status))
                    conn.commit()
                    conn.close()
                    st.success("✅ Sale Entry Added Successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please fill all required fields!")

    # TAB 2: PAYMENT ENTRY
    with tab2:
        st.subheader("Post Payment Installment Split")

        pending_df = get_pending_sales(
            st.session_state.role,
            st.session_state.branch_id
        )

        if len(pending_df) == 0:
            st.info("No pending sales!")
        else:
            sale_options = [
                f"ID {row['sale_id']} - {row['name']} ({row['branch_name']}) - Rs.{row['pending_amount']:,.1f} Pending"
                for _, row in pending_df.iterrows()
            ]

            selected       = st.selectbox("Select Target Active Sale ID Asset", sale_options)
            sale_id        = int(selected.split(" ")[1])
            payment_method = st.selectbox("Payment Collection Channel", ["Cash", "UPI", "Card", "Bank Transfer"])
            amount_paid    = st.number_input("Collected Split Amount Balance (Rs.)", min_value=0.01, format="%.2f")
            payment_date   = st.date_input("Payment Date", value=date.today())

            if st.button("💾 Apply Payment Allocation", use_container_width=True):
                if amount_paid > 0:
                    try:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO payment_splits
                            (sale_id, payment_date, amount_paid, payment_method)
                            VALUES (?, ?, ?, ?)
                        """, (sale_id, payment_date, amount_paid, payment_method))
                        conn.commit()
                        conn.close()
                        st.success("✅ Payment Logged Successfully!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error: {e}")
                else:
                    st.warning("Please enter amount!")

# PAGE 3 — ADVANCED SQL ENGINE


def show_sql_engine():
    st.title("🔍 Advanced SQL Engine")
    st.markdown("---")

    query_options = {
        "-- Select a query --": "",
        "1. All customer_sales records":
            "SELECT * FROM customer_sales",
        "2. All branches records":
            "SELECT * FROM branches",
        "3. All payment_splits records":
            "SELECT * FROM payment_splits",
        "4. Sales with status = Open":
            "SELECT * FROM customer_sales WHERE status = 'Open'",
        "5. Sales of Chennai branch": """SELECT cs.*
FROM customer_sales cs
JOIN branches b ON cs.branch_id = b.branch_id
WHERE b.branch_name = 'Chennai'""",
        "6. Total gross sales": """SELECT SUM(gross_sales) AS total_gross_sales
FROM customer_sales""",
        "7. Total received amount": """SELECT SUM(received_amount) AS total_received
FROM customer_sales""",
        "8. Total pending amount": """SELECT SUM(gross_sales - received_amount) AS total_pending
FROM customer_sales""",
        "9. Total sales per branch": """SELECT b.branch_name,
       COUNT(cs.sale_id) AS total_sales
FROM customer_sales cs
JOIN branches b ON cs.branch_id = b.branch_id
GROUP BY b.branch_name
ORDER BY total_sales DESC""",
        "10. Average gross sales": """SELECT AVG(gross_sales) AS avg_gross_sales
FROM customer_sales""",
        "11. Sales with branch name": """SELECT cs.sale_id, b.branch_name, cs.date,
       cs.name, cs.product_name,
       cs.gross_sales, cs.status
FROM customer_sales cs
JOIN branches b ON cs.branch_id = b.branch_id
ORDER BY cs.sale_id""",
        "12. Sales with total payment received": """SELECT cs.sale_id, cs.name, cs.gross_sales,
       SUM(ps.amount_paid) AS total_paid
FROM customer_sales cs
JOIN payment_splits ps ON cs.sale_id = ps.sale_id
GROUP BY cs.sale_id, cs.name, cs.gross_sales
ORDER BY cs.sale_id""",
        "13. Branch-wise total gross sales": """SELECT b.branch_name,
       SUM(cs.gross_sales) AS total_gross_sales
FROM customer_sales cs
JOIN branches b ON cs.branch_id = b.branch_id
GROUP BY b.branch_name
ORDER BY total_gross_sales DESC""",
        "14. Sales with payment method": """SELECT cs.sale_id, cs.name, cs.gross_sales,
       ps.payment_method, ps.amount_paid
FROM customer_sales cs
JOIN payment_splits ps ON cs.sale_id = ps.sale_id
ORDER BY cs.sale_id""",
        "15. Sales with branch admin name": """SELECT cs.sale_id, cs.name,
       b.branch_name, b.branch_admin_name,
       cs.gross_sales, cs.status
FROM customer_sales cs
JOIN branches b ON cs.branch_id = b.branch_id
ORDER BY cs.sale_id""",
        "16. Sales where pending > 5000": """SELECT sale_id, name, gross_sales,
       received_amount,
       (gross_sales - received_amount) AS pending_amount
FROM customer_sales
WHERE (gross_sales - received_amount) > 5000
ORDER BY pending_amount DESC""",
        "17. Top 3 highest gross sales": """SELECT TOP 3 sale_id, name,
       gross_sales, status
FROM customer_sales
ORDER BY gross_sales DESC""",
        "18. Branch with highest gross sales": """SELECT TOP 1 b.branch_name,
       SUM(cs.gross_sales) AS total_gross
FROM customer_sales cs
JOIN branches b ON cs.branch_id = b.branch_id
GROUP BY b.branch_name
ORDER BY total_gross DESC""",
        "19. Monthly sales summary": """SELECT YEAR(date) AS year,
       MONTH(date) AS month,
       COUNT(*) AS total_sales,
       SUM(gross_sales) AS total_revenue
FROM customer_sales
GROUP BY YEAR(date), MONTH(date)
ORDER BY year, month""",
        "20. Payment method-wise collection": """SELECT payment_method,
       SUM(amount_paid) AS total_collected
FROM payment_splits
GROUP BY payment_method
ORDER BY total_collected DESC""",
    }

    # ── ADMIN QUERIES (branch restricted!) ──
    admin_query_options = {
        "-- Select a query --": "",
        "1. My branch sales": f"""SELECT cs.sale_id, b.branch_name,
       cs.date, cs.name, cs.mobile_number,
       cs.product_name, cs.gross_sales,
       cs.received_amount,
       (cs.gross_sales - cs.received_amount) AS pending_amount,
       cs.status
FROM customer_sales cs
JOIN branches b ON cs.branch_id = b.branch_id
WHERE cs.branch_id = {st.session_state.branch_id}
ORDER BY cs.sale_id""",
        "2. My branch open sales": f"""SELECT cs.sale_id, cs.name,
       cs.gross_sales, cs.received_amount,
       (cs.gross_sales - cs.received_amount) AS pending_amount
FROM customer_sales cs
WHERE cs.branch_id = {st.session_state.branch_id}
AND cs.status = 'Open'""",
        "3. My branch total revenue": f"""SELECT SUM(gross_sales) AS total_revenue,
       SUM(received_amount) AS total_received,
       SUM(gross_sales - received_amount) AS total_pending
FROM customer_sales
WHERE branch_id = {st.session_state.branch_id}""",
        "4. My branch payment collection": f"""SELECT ps.payment_method,
       SUM(ps.amount_paid) AS total_collected
FROM payment_splits ps
JOIN customer_sales cs ON ps.sale_id = cs.sale_id
WHERE cs.branch_id = {st.session_state.branch_id}
GROUP BY ps.payment_method
ORDER BY total_collected DESC""",
        "5. My branch top 3 sales": f"""SELECT TOP 3 sale_id, name,
       gross_sales, status
FROM customer_sales
WHERE branch_id = {st.session_state.branch_id}
ORDER BY gross_sales DESC""",
    }

    st.subheader("📋 Predefined Queries")

    # Show different queries based on role!
    if st.session_state.role == "Admin":
        st.info(
            f"⚠️ Showing queries for "
            f"your branch only!"
        )
        selected_query = st.selectbox(
            "Select a Predefined Query",
            list(admin_query_options.keys())
        )
        current_options = admin_query_options
    else:
        selected_query = st.selectbox(
            "Select a Predefined Query",
            list(query_options.keys())
        )
        current_options = query_options

    st.markdown("---")
    st.subheader("✍️ Custom Query")

    if selected_query != "-- Select a query --":
        query_text = st.text_area(
            "SQL Query",
            value=current_options[selected_query].strip(),
            height=150
        )
    else:
        query_text = st.text_area(
            "SQL Query",
            height=150,
            placeholder="SELECT * FROM customer_sales"
        )

    if st.button("▶️ Execute Query", use_container_width=True):
        if query_text:
            # Admin restriction on custom queries!
            if st.session_state.role == "Admin":
                branch_id = st.session_state.branch_id
                if f"branch_id = {branch_id}" not in query_text \
                and f"branch_id={branch_id}" not in query_text:
                    if "WHERE" in query_text.upper():
                        query_text = query_text + \
                            f" AND cs.branch_id = {branch_id}"
                    st.warning(
                        "⚠️ Query restricted to your branch!"
                    )
            try:
                conn   = get_connection()
                result = pd.read_sql(query_text, conn)
                conn.close()
                st.success(f"✅ {len(result)} rows returned!")
                st.dataframe(result, use_container_width=True)
                csv = result.to_csv(index=False)
                st.download_button(
                    label="📥 Download Result",
                    data=csv,
                    file_name="query_result.csv",
                    mime="text/csv"
                )
            except Exception as e:
                st.error(f"SQL Error: {e}")
        else:
            st.warning("Please enter or select a query!")

# MAIN ROUTER


if not st.session_state.logged_in:
    show_login_page()
else:
    show_sidebar()

    if st.session_state.page == "Dashboard & Reports":
        show_dashboard()
    elif st.session_state.page == "Data Entry Workspace":
        show_data_entry()
    elif st.session_state.page == "Advanced SQL Engine":
        show_sql_engine()
