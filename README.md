# SuperKart Sales Forecast - Containerized Deployment

| Folder / file | Content |
|---|---|
| `backend_files/` | Flask API (`app.py`), `requirements.txt`, `Dockerfile`, serialized model `superkart_model.joblib` |
| `frontend_files/` | Streamlit UI (`app.py`), `requirements.txt`, `Dockerfile` |
| `deploy.sh` | Builds both images and runs them on a shared Docker network |
| `Batch_Data_SuperKart.csv` | Sample file for batch inference |

## Run in GitHub Codespaces
1. Code -> Codespaces -> Create codespace on main
2. In the terminal: `bash deploy.sh`
3. PORTS tab: set ports 7860 and 8501 to Public
4. Open the forwarded URL of port 8501 (Streamlit); the API is at the forwarded URL of port 7860

## API
- `POST /v1/predict` - JSON with the 10 features
- `POST /v1/predictbatch` - multipart form, key `file` = CSV
