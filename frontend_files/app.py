# ============================== SuperKart Sales Forecast - Streamlit frontend ==============================
import os                      # Read the backend URL from an environment variable
import requests                # Call the Flask backend
import pandas as pd            # Display / download batch results
import streamlit as st         # Web UI framework

# Backend base URL: container name 'backend' on the Docker network (override with -e BACKEND_URL=...)
BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:7860").rstrip("/")

# Reference year used to compute Store_Age_Years - must match the notebook (2025)
REFERENCE_YEAR = 2025

# Page configuration
st.set_page_config(page_title="SuperKart Sales Forecast", page_icon="🛒", layout="wide")
st.title("🛒 SuperKart Sales Revenue Forecast")
st.caption(f"Predicts Product_Store_Sales_Total for a product in a store | Backend: {BACKEND_URL}")

# Two tabs: online (single) and batch inference
tab_single, tab_batch = st.tabs(["Single Prediction", "Batch Prediction"])

# ------------------------------------------- Single prediction -------------------------------------------
with tab_single:
    with st.form("single_prediction_form"):                    # Form -> one API call per submit
        col1, col2 = st.columns(2)                              # Product inputs left, store inputs right
        with col1:
            st.subheader("Product details")
            product_id_char = st.selectbox("Product family (Product_Id prefix)", ["FD", "DR", "NC"],
                                           help="FD = Food, DR = Drinks, NC = Non-Consumable")
            product_type_category = st.selectbox("Product type category", ["Perishables", "Non Perishables"])
            product_weight = st.number_input("Product weight", min_value=0.0, max_value=50.0, value=12.66, step=0.01)
            product_sugar = st.selectbox("Sugar content", ["Low Sugar", "Regular", "No Sugar"])
            product_area = st.number_input("Allocated display area (ratio)", min_value=0.0, max_value=1.0,
                                           value=0.027, step=0.001, format="%.3f")
            product_mrp = st.number_input("Product MRP", min_value=0.0, max_value=1000.0, value=117.08, step=0.01)
        with col2:
            st.subheader("Store details")
            store_type = st.selectbox("Store type", ["Supermarket Type1", "Supermarket Type2", "Departmental Store", "Food Mart"])
            store_size = st.selectbox("Store size", ["Small", "Medium", "High"], index=1)
            city_type = st.selectbox("City tier", ["Tier 1", "Tier 2", "Tier 3"], index=1)
            est_year = st.number_input("Store establishment year", min_value=1950, max_value=REFERENCE_YEAR,
                                       value=2009, step=1)
            store_age = int(REFERENCE_YEAR - est_year)                       # Same feature engineering as training
            st.info(f"Store age used by the model: {store_age} years")
        submitted = st.form_submit_button("Predict sales")                   # Submit button

    if submitted:
        # JSON payload - keys must match the API / model feature names
        payload = {
            "Product_Weight": product_weight,
            "Product_Sugar_Content": product_sugar,
            "Product_Allocated_Area": product_area,
            "Product_MRP": product_mrp,
            "Store_Size": store_size,
            "Store_Location_City_Type": city_type,
            "Store_Type": store_type,
            "Product_Id_char": product_id_char,
            "Store_Age_Years": store_age,
            "Product_Type_Category": product_type_category,
        }
        try:
            response = requests.post(f"{BACKEND_URL}/v1/predict", json=payload, timeout=30)   # Call the API
            if response.status_code == 200:                                                  # Success
                prediction = response.json()["Predicted_Product_Store_Sales_Total"]
                st.success(f"Predicted Product_Store_Sales_Total: {prediction:,.2f}")
                st.metric("Forecast revenue", f"{prediction:,.2f}")
            else:                                                                            # API returned an error
                st.error(f"API error {response.status_code}: {response.text}")
            with st.expander("Request payload and raw API response"):                        # Transparency for screenshots
                st.json({"request": payload, "response": response.text})
        except requests.exceptions.RequestException as err:                                  # Network problems
            st.error(f"Could not reach the backend at {BACKEND_URL}: {err}")

# ------------------------------------------- Batch prediction -------------------------------------------
with tab_batch:
    st.write("Upload a CSV with the columns: Product_Weight, Product_Sugar_Content, Product_Allocated_Area, "
             "Product_MRP, Store_Size, Store_Location_City_Type, Store_Type, Product_Id_char, "
             "Store_Age_Years, Product_Type_Category")
    uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])        # CSV uploader

    if uploaded_file is not None:
        batch_df = pd.read_csv(uploaded_file)                                 # Preview the uploaded data
        st.write(f"Preview ({len(batch_df)} rows):")
        st.dataframe(batch_df.head(20))

        if st.button("Predict batch"):
            try:
                files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "text/csv")}   # Multipart upload
                response = requests.post(f"{BACKEND_URL}/v1/predictbatch", files=files, timeout=120)
                if response.status_code == 200:
                    preds = response.json()                                                    # {row_index: prediction}
                    batch_df["Predicted_Product_Store_Sales_Total"] = [preds[str(i)] for i in range(len(batch_df))]
                    st.success("Batch prediction completed.")
                    st.dataframe(batch_df)                                                     # Inputs + predictions
                    st.download_button("Download predictions as CSV",
                                       batch_df.to_csv(index=False).encode("utf-8"),
                                       file_name="superkart_batch_predictions.csv", mime="text/csv")
                    with st.expander("Raw API response"):
                        st.json(preds)
                else:
                    st.error(f"API error {response.status_code}: {response.text}")
            except requests.exceptions.RequestException as err:
                st.error(f"Could not reach the backend at {BACKEND_URL}: {err}")
