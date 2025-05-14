import streamlit as st
import pandas as pd
import datetime
from io import BytesIO

st.set_page_config(page_title="Ice Cream Outgoing Tracker", layout="wide")

# --- Initialize session state ---
if "products" not in st.session_state:
    st.session_state.products = pd.DataFrame(columns=["Product", "Default Unit"])

if "branches" not in st.session_state:
    st.session_state.branches = ["ڕێی مەسیف", "ڕێی بەحرکە", "ڕێی بنەسڵاوە"]

if "outgoing" not in st.session_state:
    st.session_state.outgoing = pd.DataFrame(columns=[
        "Date", "Product", "Branch", "Unit", "Quantity",
        "Unit Price", "Total Price", "Currency", "Note"
    ])

# --- Product Registration ---
st.sidebar.header("📦 Register Products")
with st.sidebar.form("add_product"):
    new_product = st.text_input("Product Name (in Kurdish)")
    standard_units = ["kg", "piece", "carton", "box"]
    selected_unit = st.selectbox("Choose Unit", options=standard_units)
    custom_unit = st.text_input("Or enter a custom unit")
    unit = custom_unit if custom_unit else selected_unit
    add_btn = st.form_submit_button("➕ Add Product")
    if add_btn and new_product:
        new_entry = {"Product": new_product, "Default Unit": unit}
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
                product = st.selectbox("Product", options=st.session_state.products["Product"])
                matching_unit = st.session_state.products.loc[st.session_state.products["Product"] == product, "Default Unit"]
                default_unit = matching_unit.values[0] if not matching_unit.empty else ""
                unit = st.text_input("Unit", value=default_unit)
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
                    "Date": date, "Product": product, "Branch": branch,
                    "Unit": unit, "Quantity": quantity,
                    "Unit Price": unit_price, "Total Price": total_price,
                    "Currency": currency, "Note": note
                }
                st.session_state.outgoing = st.session_state.outgoing._append(row, ignore_index=True)
                st.success("✅ Entry saved!")

# --- Filter & Summary ---
with tab2:
    st.header("📊 Filter & Summary")
    df = st.session_state.outgoing.copy()

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
        summary = df.groupby(["Branch", "Product", "Unit", "Currency"])[["Quantity", "Total Price"]].sum().reset_index()
        st.dataframe(summary, use_container_width=True)
    else:
        st.info("No data matches your filters.")

# --- View All Data with Edit/Delete ---
with tab3:
    st.header("📋 All Outgoing Records")
    df = st.session_state.outgoing
    for i, row in df.iterrows():
        cols = st.columns([2, 2, 1, 1, 1, 1, 1, 2])
        with cols[0]: st.write(row["Date"])
        with cols[1]: st.write(row["Product"])
        with cols[2]: st.write(row["Branch"])
        with cols[3]: st.write(f"{row['Quantity']} {row['Unit']}")
        with cols[4]: st.write(f"{row['Unit Price']} {row['Currency']}")
        with cols[5]: st.write(f"{row['Total Price']} {row['Currency']}")
        with cols[6]: st.write(row["Note"])
        with cols[7]:
            if st.button("🗑 Delete", key=f"delete_{i}"):
                st.session_state.outgoing.drop(index=i, inplace=True)
                st.session_state.outgoing.reset_index(drop=True, inplace=True)
                st.experimental_rerun()

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
