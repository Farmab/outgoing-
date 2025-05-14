import streamlit as st
import hashlib
import pandas as pd
import datetime
from io import BytesIO

st.set_page_config(page_title="Ice Cream Outgoing Tracker", layout="wide")

# --- Login system ---
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login():
    st.title("🔐 Login")
    username_input = st.text_input("Username")
    password_input = st.text_input("Password", type="password")
    if st.button("Login"):
        if username_input == "abdulsalam" and hash_password(password_input) == hash_password("2025"):
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login()
    st.stop()

# --- Initialize session state ---
data_key = "outgoing_data.csv"

@st.cache_data(show_spinner=False)
def load_saved_data():
    try:
        return pd.read_csv(data_key, parse_dates=["Date"])
    except:
        return pd.DataFrame(columns=["Type", "Date", "Product", "Branch", "Unit", "Quantity", "Unit Price", "Total Price", "Currency", "Note"])

@st.cache_data(show_spinner=False, persist=True)
def save_data(df):
    df.to_csv(data_key, index=False)
if "products" not in st.session_state:
    st.session_state.products = pd.DataFrame(columns=["Product", "Type", "Default Unit"])

if "branches" not in st.session_state:
    st.session_state.branches = ["ڕێی مەسیف", "ڕێی بەحرکە", "ڕێی بنەسڵاوە"]

if "outgoing" not in st.session_state:
    st.session_state.outgoing = load_saved_data()

# Save anytime data is updated
if st.session_state.outgoing is not None and not st.session_state.outgoing.empty:
    save_data(st.session_state.outgoing)


    st.session_state.outgoing = pd.DataFrame(columns=["Type", 
        "Date", "Product", "Branch", "Unit", "Quantity",
        "Unit Price", "Total Price", "Currency", "Note"
    ])

# --- Product Registration ---

# --- Import from Excel ---
st.sidebar.header("📥 Import Products from Excel")
uploaded_file = st.sidebar.file_uploader("Upload Excel file with Product, Type, and Unit", type=["xlsx"])
if uploaded_file:
    df_upload = pd.read_excel(uploaded_file)
    if {"product", "default type", "unit"}.issubset(df_upload.columns):
        df_upload.columns = ["Product", "Type", "Default Unit"]
        st.session_state.products = pd.concat([st.session_state.products, df_upload], ignore_index=True).drop_duplicates()
        st.success("✅ Products imported successfully!")
    else:
        st.error("❌ Excel must have columns: product, default type, unit")
st.sidebar.header("📦 Register Products")
with st.sidebar.form("add_product"):
    new_product = st.text_input("Product Name (in Kurdish)")
    standard_units = ["kg", "piece", "carton", "box"]
    selected_unit = st.selectbox("Choose Unit", options=standard_units)
    custom_unit = st.text_input("Or enter a custom unit")
    unit = custom_unit if custom_unit else selected_unit
    new_type = st.text_input("Type of Product")
    add_btn = st.form_submit_button("➕ Add Product")
    if add_btn and new_product:
        new_entry = {"Product": new_product, "Type": new_type, "Default Unit": unit}
        st.session_state.products = st.session_state.products._append(new_entry, ignore_index=True)
        st.success(f"✅ '{new_product}' added with unit '{unit}'")

# --- Branch Registration ---
st.sidebar.header("🏪 Register Branches")
with st.sidebar.form("add_branch"):
    new_branch = st.text_input("New Branch Name")
    add_branch_btn = st.form_submit_button("➕ Add Branch")
    if add_branch_btn and new_branch and new_branch not in st.session_state.branches:
        st.session_state.branches.append(new_branch)
        st.success(f"✅ Branch '{new_branch}' added")

# --- Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(["📅 Daily Outgoing", "📊 Filter & Summary", "📋 All Data", "📥 Export"])

# --- Daily Outgoing Entry ---
with tab1:
    st.header("📅 Daily Outgoing Entry")
    if st.session_state.products.empty:
        st.warning("⚠️ Please register at least one product before adding outgoing entries.")
    else:
        with st.form("daily_entry", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                date = st.date_input("Date", value=datetime.date.today())
                product = st.selectbox("Product", options=st.session_state.products["Product"].unique())
                product_match = st.session_state.products[st.session_state.products["Product"] == product]
                type_options = product_match["Type"].dropna().unique()
                unit_options = product_match["Default Unit"].dropna().unique()
                product_type = st.text_input("Type of Product")  # Manually entered now
                all_units = st.session_state.products["Default Unit"].dropna().unique()
                unit_options = st.session_state.products["Default Unit"].dropna().unique()
                unit = st.selectbox("Unit", options=unit_options)
                # handled within try block above
                # unit handled above dynamically
                quantity = st.number_input("Quantity", min_value=0.0)
            with col2:
                branch = st.selectbox("Branch", options=st.session_state.branches)
                currency = st.radio("Currency", options=["IQD", "$"])
                unit_price = st.number_input("Unit Price", min_value=0.0)
                total_price = quantity * unit_price
                note = st.text_input("Note")

            submitted = st.form_submit_button("Save Entry")
            if submitted:
                row = {
                    "Date": date, "Product": product, "Type": product_type, "Branch": branch,
                    "Unit": unit, "Quantity": quantity,
                    "Unit Price": unit_price, "Total Price": total_price,
                    "Currency": currency, "Note": note
                }
                st.session_state.outgoing = st.session_state.outgoing._append(row, ignore_index=True)
                save_data(st.session_state.outgoing)
                st.success("✅ Entry saved!")

# --- Filter & Summary ---
with tab2:
    st.header("📊 Filter & Summary")
    df = st.session_state.outgoing.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    with st.expander("🔍 Filters"):
        col1, col2, col3 = st.columns(3)
        with col1:
            selected_branch = st.multiselect("Branch", options=df["Branch"].unique())
        with col2:
            selected_product = st.multiselect("Product", options=df["Product"].unique())
        with col3:
            date_range = st.date_input("Date Range", [])

    if selected_branch:
        df = df[df["Branch"].isin(selected_branch)]
    if selected_product:
        df = df[df["Product"].isin(selected_product)]
    if len(date_range) == 2:
        df = df[(df["Date"] >= pd.to_datetime(date_range[0])) & (df["Date"] <= pd.to_datetime(date_range[1]))]

    if not df.empty:
        st.write("### 📦 Summary by Branch and Product")
        st.button("🖨 Print Summary", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))
        summary = df.groupby(["Branch", "Product", "Type", "Unit", "Currency"])[["Quantity", "Total Price"]].sum().reset_index()
        grand_total = summary["Total Price"].sum()
        summary['Quantity'] = summary['Quantity'].apply(lambda x: f"{int(x):,}" if x == int(x) else f"{x:,}")
        summary['Total Price'] = summary['Total Price'].apply(lambda x: f"{int(x):,}" if x == int(x) else f"{x:,}")
        st.table(summary)
        total_sum = df["Total Price"].sum()
        st.success(f"💰 Total Price of Filtered Items: {total_sum:,.2f}")
        st.info(f"🧾 Grand Total Across All Items: {grand_total:,.2f}")
    else:
        st.info("No data matches your filters.")

# --- View All Data with Edit/Delete ---
with tab3:
    st.header("📋 All Outgoing Records")
    st.markdown("<script>window.print = () => { window.open(document.location.href, '_blank').print(); };</script>", unsafe_allow_html=True)
    st.button("🖨 Print Page", on_click=lambda: st.markdown("<script>window.print();</script>", unsafe_allow_html=True))
    df = st.session_state.outgoing
    if "Type" not in df.columns:
        try:
            df["Type"] = st.session_state.products.set_index("Product").loc[df["Product"]]["Type"].values
        except:
            df["Type"] = ""
    if not df.empty:
        styled_df = df.copy()
        styled_df["Quantity"] = styled_df["Quantity"].apply(lambda x: f"{int(x):,}" if x == int(x) else f"{x:,}")
        styled_df["Unit Price"] = styled_df["Unit Price"].apply(lambda x: f"{int(x):,}" if x == int(x) else f"{x:,}")
        styled_df["Total Price"] = styled_df["Total Price"].apply(lambda x: f"{int(x):,}" if x == int(x) else f"{x:,}")
        styled_df["Edit"] = [f"✏️ Edit {i}" for i in styled_df.index]
        styled_df["Delete"] = [f"🗑 Delete {i}" for i in styled_df.index]
        st.table(styled_df.drop(columns=["Note"]))

        for i in styled_df.index:
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button(f"✏️ Edit", key=f"edit_btn_{i}"):
                    st.session_state.edit_index = i
            with col2:
                if st.button(f"🗑 Delete", key=f"delete_btn_{i}"):
                    st.session_state.outgoing.drop(index=i, inplace=True)
                    st.session_state.outgoing.reset_index(drop=True, inplace=True)
                    try:
                        st.rerun()
                    except AttributeError:
                        pass

    for i, row in df.iterrows():
        cols = st.columns([2, 2, 1, 1, 1, 1, 1, 2, 1])
        with cols[0]: st.write(row["Date"])
        with cols[1]: st.write(f"{row['Product']} ({row['Type']})")
        with cols[2]: st.write(row["Branch"])
        with cols[3]:
            qty = f"{int(row['Quantity']):,}" if row['Quantity'] == int(row['Quantity']) else f"{row['Quantity']:,}"
            st.write(f"{qty} {row['Unit']}")
        with cols[4]:
            unit_price = f"{int(row['Unit Price']):,}" if row['Unit Price'] == int(row['Unit Price']) else f"{row['Unit Price']:,}"
            st.write(f"{unit_price} {row['Currency']}")
        with cols[5]:
            total_price = f"{int(row['Total Price']):,}" if row['Total Price'] == int(row['Total Price']) else f"{row['Total Price']:,}"
            st.write(f"{total_price} {row['Currency']}")
        with cols[6]: st.write(row["Note"])
        with cols[7]:
            if st.button("✏️ Edit", key=f"edit_{i}"):
                st.session_state.edit_index = i
        with cols[8]:
            if st.button("🗑 Delete", key=f"delete_{i}"):
            st.session_state.outgoing.drop(index=i, inplace=True)
            st.session_state.outgoing.reset_index(drop=True, inplace=True)
            save_data(st.session_state.outgoing)
            try:
                st.rerun()
            except AttributeError:
                pass  # Safe fallback for older versions

    # Edit form below the table
    if "edit_index" in st.session_state and st.session_state.edit_index is not None:
        idx = st.session_state.edit_index
        row = st.session_state.outgoing.loc[idx]
        st.markdown("### ✏️ Edit Entry")
        with st.form("edit_form"):
            col1, col2 = st.columns(2)
            with col1:
                date = st.date_input("Date", value=row["Date"])
                product = st.text_input("Product", value=row["Product"])
                unit = st.text_input("Unit", value=row["Unit"])
                quantity = st.number_input("Quantity", value=row["Quantity"], min_value=0.0)
            with col2:
                branch = st.selectbox("Branch", options=st.session_state.branches, index=st.session_state.branches.index(row["Branch"]))
                currency = st.radio("Currency", options=["IQD", "$"], index=["IQD", "$"].index(row["Currency"]))
                unit_price = st.number_input("Unit Price", value=row["Unit Price"], min_value=0.0)
                note = st.text_input("Note", value=row["Note"])

            total_price = quantity * unit_price
            if st.form_submit_button("Update Entry"):
                type_ = st.text_input("Type", value=row.get("Type", ""))
                st.session_state.outgoing.loc[idx] = [
                    date, product, type_, branch, unit, quantity,
                    unit_price, total_price, currency, note
                ]
                save_data(st.session_state.outgoing)
                st.session_state.edit_index = None
                st.success("✅ Entry updated!")
                try:
                    st.rerun()
                except AttributeError:
                    pass

# --- PDF Export ---
with tab3:
    from fpdf import FPDF
    from pathlib import Path
    if st.button("🖨 Export Summary as PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.add_font('DejaVu', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', uni=True)
        pdf.set_font('DejaVu', '', 12)
        pdf.cell(200, 10, txt="Ice Cream Outgoing Summary", ln=True, align='C')
        pdf.ln(10)
        for i, row in summary.iterrows():
            quantity = int(row['Quantity']) if row['Quantity'] == int(row['Quantity']) else row['Quantity']
            total = int(row['Total Price']) if row['Total Price'] == int(row['Total Price']) else row['Total Price']
            line = f"{row['Branch']} - {row['Product']} ({row['Type']}, {row['Unit']}): {quantity} qty, {total} {row['Currency']}"
            pdf.cell(200, 10, txt=line, ln=True)
        final_total = int(total_sum) if total_sum == int(total_sum) else total_sum
        pdf.cell(200, 10, txt=f"Total Price: {final_total}", ln=True)
        pdf_output = BytesIO()
        pdf.output(pdf_output)
        pdf_output.seek(0)
        st.download_button("📄 Download PDF", data=pdf_output.getvalue(), file_name="summary.pdf", mime="application/pdf")

# --- Export ---
with tab4:
    st.header("📥 Export All Data")

    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False)
        output.seek(0)
        return output

    excel_file = to_excel(st.session_state.outgoing)
    st.download_button(
        label="📥 Download as Excel",
        data=excel_file,
        file_name="ice_cream_outgoing.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
