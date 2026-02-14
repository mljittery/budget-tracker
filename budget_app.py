import streamlit as st
import json
import os
import csv
from datetime import datetime
from io import StringIO
import pandas as pd

# Page config
st.set_page_config(
    page_title="Budget Tracker",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# File paths
CONFIG_FILE = 'budget_config.json'
DATA_FILE = 'budget_data.json'
RULES_FILE = 'categorization_rules.json'

# Initialize session state
if 'config' not in st.session_state:
    st.session_state.config = None
if 'data' not in st.session_state:
    st.session_state.data = None
if 'rules' not in st.session_state:
    st.session_state.rules = None

# Load functions
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        "categories": {},
        "fixed_expenses": {}
    }

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return {"months": {}}

def load_rules():
    if os.path.exists(RULES_FILE):
        with open(RULES_FILE, 'r') as f:
            return json.load(f)
    return {
        "keyword_rules": {
            "WHOLE FOODS": "Necessities",
            "TRADER JOE": "Necessities",
            "WALMART": "Necessities",
            "TARGET": "Necessities",
            "STARBUCKS": "Discretionary",
            "CHIPOTLE": "Discretionary",
            "SHELL": "Necessities",
            "CHEVRON": "Necessities",
            "UBER": "Necessities",
            "NETFLIX": "Discretionary",
            "AMAZON": "Discretionary",
        },
        "learned_rules": {}
    }

def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def save_rules(rules):
    with open(RULES_FILE, 'w') as f:
        json.dump(rules, f, indent=2)

def auto_categorize(description, rules):
    """Auto-categorize transaction based on description"""
    description_upper = description.upper()
    
    # Check learned rules first
    for merchant, category in rules["learned_rules"].items():
        if merchant.upper() in description_upper:
            return category
    
    # Check keyword rules
    for keyword, category in rules["keyword_rules"].items():
        if keyword.upper() in description_upper:
            return category
    
    return None

# Load data
st.session_state.config = load_config()
st.session_state.data = load_data()
st.session_state.rules = load_rules()

# Custom CSS
st.markdown("""
<style>
    .big-font {
        font-size: 24px !important;
        font-weight: bold;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar navigation
st.sidebar.title("💰 Budget Tracker")
page = st.sidebar.radio("Navigation", [
    "📊 Dashboard",
    "📥 Import CSV",
    "➕ Add Expense",
    "⚙️ Manage Categories",
    "📅 New Month",
    "📈 Summary"
])

# Main content
if page == "📊 Dashboard":
    st.title("📊 Budget Dashboard")
    
    current_month = datetime.now().strftime("%Y-%m")
    
    # Month selector
    available_months = sorted(st.session_state.data["months"].keys(), reverse=True)
    if available_months:
        selected_month = st.selectbox("Select Month", available_months, index=0)
    else:
        st.warning("No budget data yet. Create a new month budget first!")
        st.stop()
    
    month_data = st.session_state.data["months"][selected_month]
    budget = month_data["budget"]
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("💵 Total Income", f"${budget['total_income']:,.2f}")
    
    with col2:
        total_spent = sum(cat["spent"] for cat in budget["categories"].values())
        st.metric("💸 Total Spent", f"${total_spent:,.2f}")
    
    with col3:
        remaining = budget['total_income'] - total_spent
        st.metric("💰 Remaining", f"${remaining:,.2f}")
    
    with col4:
        spent_pct = (total_spent / budget['total_income'] * 100) if budget['total_income'] > 0 else 0
        st.metric("📊 Spent %", f"{spent_pct:.1f}%")
    
    st.markdown("---")
    
    # Category breakdown
    st.subheader("Category Breakdown")
    
    for category, details in budget["categories"].items():
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.write(f"**{category}** ({details['percentage']}%)")
            progress = details['spent'] / details['allocated'] if details['allocated'] > 0 else 0
            progress = min(progress, 1.0)
            
            st.progress(progress)
            st.caption(f"${details['spent']:,.2f} of ${details['allocated']:,.2f} spent • ${details['remaining']:,.2f} left")
        
        with col2:
            if details['remaining'] < 0:
                st.error(f"Over by ${abs(details['remaining']):,.2f}")
            else:
                st.success(f"${details['remaining']:,.2f} left")
    
    st.markdown("---")
    
    # Recent transactions
    st.subheader("Recent Transactions")
    
    if month_data["expenses"]:
        expenses_df = pd.DataFrame(month_data["expenses"])
        expenses_df['date'] = pd.to_datetime(expenses_df['date']).dt.strftime('%m/%d/%Y %H:%M')
        expenses_df = expenses_df[['date', 'category', 'description', 'amount']]
        expenses_df = expenses_df.sort_values('date', ascending=False).head(10)
        expenses_df['amount'] = expenses_df['amount'].apply(lambda x: f"${x:.2f}")
        
        st.dataframe(expenses_df, use_container_width=True, hide_index=True)
    else:
        st.info("No expenses recorded yet.")

elif page == "📥 Import CSV":
    st.title("📥 Import Chase CSV")
    
    current_month = datetime.now().strftime("%Y-%m")
    
    # Check if budget exists
    if current_month not in st.session_state.data["months"]:
        st.error(f"No budget exists for {current_month}. Create one in 'New Month' first!")
        st.stop()
    
    st.markdown("""
    ### How to get your Chase CSV:
    1. Log into chase.com
    2. Go to your checking/credit card account
    3. Click "Download account activity"
    4. Select date range and download as CSV
    5. Upload it below
    """)
    
    uploaded_file = st.file_uploader("Upload Chase CSV", type=['csv'])
    
    if uploaded_file is not None:
        # Read CSV
        stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
        csv_reader = csv.DictReader(stringio)
        
        transactions = []
        for row in csv_reader:
            description = row.get('Description', row.get('Details', ''))
            amount_str = row.get('Amount', '0')
            date_str = row.get('Posting Date', row.get('Date', ''))
            trans_type = row.get('Type', '').upper()
            
            if not description:
                continue
            
            try:
                amount_raw = float(amount_str.replace(',', ''))
            except ValueError:
                continue
            
            # Skip deposits/credits
            if amount_raw >= 0:
                continue
            
            if trans_type in ['CREDIT', 'DEPOSIT', 'ACH_CREDIT', 'DSLIP']:
                continue
            
            amount = abs(amount_raw)
            
            transactions.append({
                'description': description,
                'amount': amount,
                'date': date_str
            })
        
        if not transactions:
            st.warning("No valid transactions found in CSV (income/deposits automatically filtered out)")
            st.stop()
        
        # Check for duplicates
        existing_expenses = st.session_state.data["months"][current_month]["expenses"]
        duplicates = []
        new_transactions = []
        
        for trans in transactions:
            is_duplicate = False
            for existing in existing_expenses:
                if (existing.get('description', '').upper() == trans['description'].upper() and
                    abs(existing.get('amount', 0) - trans['amount']) < 0.01):
                    is_duplicate = True
                    break
            
            if is_duplicate:
                duplicates.append(trans)
            else:
                new_transactions.append(trans)
        
        # Display results
        st.success(f"Found {len(transactions)} expense transactions in CSV")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Transactions", len(transactions))
        with col2:
            st.metric("Duplicates", len(duplicates), delta="Skipped", delta_color="off")
        with col3:
            st.metric("New Transactions", len(new_transactions), delta="Ready", delta_color="normal")
        
        if duplicates:
            st.warning(f"⚠️ Found {len(duplicates)} duplicate transactions (will skip)")
            with st.expander("View Duplicates"):
                for dup in duplicates[:10]:
                    st.text(f"{dup['description'][:50]} - ${dup['amount']:.2f}")
        
        if new_transactions:
            st.info(f"Ready to import {len(new_transactions)} new transactions")
            
            if st.button("🚀 Import New Transactions", type="primary"):
                imported = 0
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, trans in enumerate(new_transactions):
                    category = auto_categorize(trans['description'], st.session_state.rules)
                    
                    if category and category in st.session_state.config["categories"]:
                        # Add expense
                        expense = {
                            "date": datetime.now().isoformat(),
                            "category": category,
                            "amount": trans['amount'],
                            "description": trans['description']
                        }
                        
                        st.session_state.data["months"][current_month]["expenses"].append(expense)
                        st.session_state.data["months"][current_month]["budget"]["categories"][category]["spent"] += trans['amount']
                        st.session_state.data["months"][current_month]["budget"]["categories"][category]["remaining"] -= trans['amount']
                        
                        imported += 1
                    
                    progress_bar.progress((i + 1) / len(new_transactions))
                    status_text.text(f"Importing {i + 1}/{len(new_transactions)}...")
                
                save_data(st.session_state.data)
                
                st.success(f"✅ Imported {imported} transactions!")
                st.balloons()
                
                if imported < len(new_transactions):
                    st.warning(f"{len(new_transactions) - imported} transactions couldn't be auto-categorized. Add them manually in 'Add Expense' page.")
        else:
            st.info("All transactions already imported!")

elif page == "➕ Add Expense":
    st.title("➕ Add Expense")
    
    current_month = datetime.now().strftime("%Y-%m")
    
    if current_month not in st.session_state.data["months"]:
        st.error(f"No budget exists for {current_month}. Create one in 'New Month' first!")
        st.stop()
    
    categories = list(st.session_state.config["categories"].keys())
    
    if not categories:
        st.error("No categories set up. Go to 'Manage Categories' first!")
        st.stop()
    
    with st.form("add_expense_form"):
        category = st.selectbox("Category", categories)
        amount = st.number_input("Amount ($)", min_value=0.01, step=0.01)
        description = st.text_input("Description")
        
        submitted = st.form_submit_button("Add Expense", type="primary")
        
        if submitted:
            expense = {
                "date": datetime.now().isoformat(),
                "category": category,
                "amount": amount,
                "description": description
            }
            
            st.session_state.data["months"][current_month]["expenses"].append(expense)
            st.session_state.data["months"][current_month]["budget"]["categories"][category]["spent"] += amount
            st.session_state.data["months"][current_month]["budget"]["categories"][category]["remaining"] -= amount
            
            save_data(st.session_state.data)
            
            st.success(f"✅ Added ${amount:.2f} to {category}")
            st.balloons()

elif page == "⚙️ Manage Categories":
    st.title("⚙️ Manage Categories")
    
    st.subheader("Current Categories")
    
    if st.session_state.config["categories"]:
        total_pct = 0
        for cat_name, details in st.session_state.config["categories"].items():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.write(f"**{cat_name}**")
            with col2:
                st.write(f"{details['percentage']}%")
            with col3:
                if st.button("🗑️", key=f"delete_{cat_name}"):
                    del st.session_state.config["categories"][cat_name]
                    save_config(st.session_state.config)
                    st.rerun()
            
            total_pct += details['percentage']
        
        st.markdown("---")
        if total_pct != 100:
            st.warning(f"⚠️ Total percentage is {total_pct}%, should be 100%")
        else:
            st.success(f"✅ Total percentage: {total_pct}%")
    else:
        st.info("No categories yet. Add one below!")
    
    st.markdown("---")
    st.subheader("Add New Category")
    
    with st.form("add_category_form"):
        new_cat_name = st.text_input("Category Name")
        new_cat_pct = st.number_input("Percentage", min_value=1, max_value=100, value=10)
        
        submitted = st.form_submit_button("Add Category", type="primary")
        
        if submitted:
            if new_cat_name in st.session_state.config["categories"]:
                st.error(f"Category '{new_cat_name}' already exists!")
            elif not new_cat_name:
                st.error("Please enter a category name!")
            else:
                st.session_state.config["categories"][new_cat_name] = {
                    "percentage": new_cat_pct,
                    "subcategories": []
                }
                save_config(st.session_state.config)
                st.success(f"✅ Added category '{new_cat_name}'")
                st.rerun()

elif page == "📅 New Month":
    st.title("📅 Create New Month Budget")
    
    default_month = datetime.now().strftime("%Y-%m")
    
    with st.form("new_month_form"):
        month = st.text_input("Month (YYYY-MM)", value=default_month)
        income = st.number_input("Monthly Income ($)", min_value=0.01, step=100.00, value=1600.00)
        
        submitted = st.form_submit_button("Create Budget", type="primary")
        
        if submitted:
            if not st.session_state.config["categories"]:
                st.error("Please add categories first in 'Manage Categories'!")
            else:
                # Calculate budget
                budget = {
                    "total_income": income,
                    "categories": {},
                    "fixed_expenses": {},
                    "remaining_after_fixed": income
                }
                
                for category, details in st.session_state.config["categories"].items():
                    allocation = (details["percentage"] / 100) * income
                    budget["categories"][category] = {
                        "percentage": details["percentage"],
                        "allocated": round(allocation, 2),
                        "spent": 0,
                        "remaining": round(allocation, 2)
                    }
                
                st.session_state.data["months"][month] = {
                    "created": datetime.now().isoformat(),
                    "budget": budget,
                    "expenses": []
                }
                
                save_data(st.session_state.data)
                
                st.success(f"✅ Created budget for {month} with ${income:,.2f} income!")
                st.balloons()

elif page == "📈 Summary":
    st.title("📈 Budget Summary")
    
    if not st.session_state.data["months"]:
        st.info("No budget data yet. Create your first month in 'New Month'!")
        st.stop()
    
    # Overall stats
    total_months = len(st.session_state.data["months"])
    total_income = sum(data["budget"]["total_income"] for data in st.session_state.data["months"].values())
    avg_income = total_income / total_months if total_months > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📊 Months Tracked", total_months)
    with col2:
        st.metric("💰 Total Income", f"${total_income:,.2f}")
    with col3:
        st.metric("📈 Average Income", f"${avg_income:,.2f}")
    
    st.markdown("---")
    
    # Month by month
    st.subheader("Month by Month")
    
    for month in sorted(st.session_state.data["months"].keys(), reverse=True):
        budget = st.session_state.data["months"][month]["budget"]
        total_spent = sum(cat["spent"] for cat in budget["categories"].values())
        
        with st.expander(f"{month} - Income: ${budget['total_income']:,.2f}"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Income", f"${budget['total_income']:,.2f}")
            with col2:
                st.metric("Spent", f"${total_spent:,.2f}")
            with col3:
                st.metric("Remaining", f"${budget['total_income'] - total_spent:,.2f}")

# Footer
st.sidebar.markdown("---")
st.sidebar.caption("💰 Budget Tracker v2.0")
st.sidebar.caption("Made with ❤️ using Streamlit")
