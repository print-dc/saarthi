

# Saarthi

Saarthi is now set up to run in a free local support mode by default. That means you can host the app publicly without paying for Google Cloud or Vertex AI.

## How it works now

- `app.py` runs the Streamlit interface
- `local_support.py` generates empathetic support replies locally with no paid APIs
- Vertex AI remains optional, not required

## Local run

1. Create and activate a Python 3.12 environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Optionally copy `.streamlit/secrets.toml.example` to `.streamlit/secrets.toml`.
4. Start the app:

```bash
streamlit run app.py
```

## Free public deployment options

### Option 1: Streamlit Community Cloud

1. Push this project to GitHub.
2. Sign in at [Streamlit Community Cloud](https://share.streamlit.io/).
3. Deploy the repo with:
   - Main file path: `app.py`
4. Add these secrets if you want:

```toml
SAARTHI_MODE = "local"
DEFAULT_REGION = "india"
```

This is the simplest free public link for Saarthi.

### Option 2: Hugging Face Spaces

1. Create a new Space with the Streamlit SDK.
2. Upload this project.
3. Keep the app entrypoint as `app.py`.
4. Set optional secrets:

```toml
SAARTHI_MODE = "local"
DEFAULT_REGION = "india"
```

## Optional Vertex AI mode

If you later want a cloud-backed model again, set:<img width="959" height="449" alt="saarthi UI" src="https://github.com/user-attachments/assets/99a8c278-2ad0-4ec3-9de6-ee265750a456" />
<img width="959" height="449" alt="saarthi UI" src="https://github.com/user-attachments/assets/38633312-b974-4374-afd6-a43766ae6a73" />


```toml
SAARTHI_MODE = "vertex"
PROJECT_ID = "your-gcp-project-id"
LOCATION = "us-central1"
STAGING_BUCKET = "gs://your-staging-bucket"
RESOURCE_ID = "projects/your-gcp-project-id/locations/us-central1/reasoningEngines/your-agent-id"
GOOGLE_SERVICE_ACCOUNT_KEY = '{"type":"service_account","project_id":"your-gcp-project-id"}'
```

That mode is optional and may incur Google Cloud costs.
