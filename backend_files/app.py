# ============================== SuperKart Sales Forecast - Flask backend ==============================
import os                                    # Build the absolute path of the model file
import joblib                                # Load the serialized scikit-learn pipeline
import pandas as pd                          # Build DataFrames from the incoming JSON / CSV
from flask import Flask, request, jsonify    # Flask app, incoming request object and JSON response helper

# Initialize the Flask application (the object name is referenced by gunicorn in the Dockerfile)
superkart_api = Flask("SuperKart Sales Forecast API")

# Absolute path of the model file, located next to this script inside the container
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "superkart_model.joblib")

# Load the trained pipeline (preprocessing + model) once at start-up, not on every request
model = joblib.load(MODEL_PATH)

# Features expected by the model, in training order
EXPECTED_FEATURES = [
    "Product_Weight", "Product_Sugar_Content", "Product_Allocated_Area", "Product_MRP",
    "Store_Size", "Store_Location_City_Type", "Store_Type",
    "Product_Id_char", "Store_Age_Years", "Product_Type_Category",
]

# Subset of features that must be numeric
NUMERIC_FEATURES = ["Product_Weight", "Product_Allocated_Area", "Product_MRP", "Store_Age_Years"]


def validate_and_prepare(df):
    """Check that all expected columns exist, cast numeric columns and return the model-ready frame."""
    missing = [col for col in EXPECTED_FEATURES if col not in df.columns]   # Columns that are absent
    if missing:                                                               # Reject incomplete input
        raise ValueError(f"Missing required feature(s): {missing}")
    df = df[EXPECTED_FEATURES].copy()                                         # Keep only expected columns, in order
    for col in NUMERIC_FEATURES:                                              # Cast numeric columns
        df[col] = pd.to_numeric(df[col], errors="raise")                      # Raises ValueError on non-numeric text
    if df[NUMERIC_FEATURES].isnull().any().any():                             # Numeric fields must not be empty
        raise ValueError("Numeric features must not be empty.")
    return df


@superkart_api.get("/")
def home():
    """Landing route - confirms the API is up."""
    return "Welcome to the SuperKart Sales Forecast API!"


@superkart_api.get("/health")
def health():
    """Health-check route used by the notebook / monitoring."""
    return jsonify({"status": "ok"})


@superkart_api.post("/v1/predict")
def predict_sales():
    """Online (single) inference: JSON body with one record -> predicted sales."""
    try:
        payload = request.get_json(silent=True)                     # Parse JSON body (None if invalid JSON)
        if not isinstance(payload, dict):                           # Body must be a JSON object
            return jsonify({"error": "Request body must be a JSON object with the input features."}), 400
        input_df = validate_and_prepare(pd.DataFrame([payload]))   # One-row DataFrame, validated
        prediction = float(model.predict(input_df)[0])              # Model prediction for the single row
        return jsonify({"Predicted_Product_Store_Sales_Total": round(prediction, 2)})   # JSON response
    except ValueError as err:                                       # Validation / casting problems -> 400
        return jsonify({"error": str(err)}), 400
    except Exception as err:                                        # Any other failure -> 500
        return jsonify({"error": f"Prediction failed: {err}"}), 500


@superkart_api.post("/v1/predictbatch")
def predict_sales_batch():
    """Batch inference: CSV file uploaded under the form key 'file' -> {row_index: prediction}."""
    try:
        if "file" not in request.files:                             # The CSV must be sent with key 'file'
            return jsonify({"error": "No file part named 'file' in the request."}), 400
        input_df = pd.read_csv(request.files["file"])               # Read the uploaded CSV into a DataFrame
        if input_df.empty:                                          # Reject empty files
            return jsonify({"error": "The uploaded CSV file is empty."}), 400
        prepared = validate_and_prepare(input_df)                   # Validate columns and types
        predictions = model.predict(prepared)                       # Predict all rows in one call
        result = {str(idx): round(float(pred), 2) for idx, pred in zip(input_df.index, predictions)}   # row index -> prediction
        return jsonify(result)
    except ValueError as err:                                       # Validation / parsing problems -> 400
        return jsonify({"error": str(err)}), 400
    except Exception as err:                                        # Any other failure -> 500
        return jsonify({"error": f"Batch prediction failed: {err}"}), 500


# Development server (inside Docker the app is served by gunicorn - see Dockerfile)
if __name__ == "__main__":
    superkart_api.run(host="0.0.0.0", port=int(os.environ.get("PORT", 7860)), debug=False)
