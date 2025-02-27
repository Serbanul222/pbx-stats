# PBX Call Records Viewer

A tool to view and filter PBX call records, with both Flask and Streamlit interfaces.

## Setup and Run

### Local Setup

1. Clone the repository:
```bash
git clone <your-repository-url>
cd pbx-call-records-viewer
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file with your PBX API credentials:
```
PBX_URL=https://your-pbx-url.com/api/cdr
PBX_API_TOKEN=your_api_token
PBX_API_KEY=your_api_key
```

5. Run the Flask application:
```bash
python app.py
```

6. Access the application at http://localhost:5000

### Docker Setup

1. Create a `.env` file with your credentials (as shown above)

2. Build and run with Docker Compose:
```bash
docker-compose up -d
```

3. Access the application at http://localhost:5000

### Streamlit Setup

1. Install Streamlit:
```bash
pip install streamlit
```

2. Run the Streamlit app:
```bash
streamlit run streamlit_app.py
```

3. Access the Streamlit app at http://localhost:8501

## Deployment to Streamlit Cloud

1. Push your code to GitHub

2. Go to [Streamlit Sharing](https://share.streamlit.io/)

3. Deploy your app and configure these secrets in the Streamlit dashboard:
   - PBX_URL
   - PBX_API_TOKEN
   - PBX_API_KEY

## Features

- Filter call records by date range
- Additional filters for Caller ID, Call Code, and Call Status
- View call statistics
- Download filtered data as CSV

## Docker Image

The Docker image includes:
- Python 3.9
- Flask application
- All required dependencies

## File Structure

- `app.py`: Flask application
- `streamlit_app.py`: Streamlit application
- `templates/index.html`: HTML template for Flask app
- `Dockerfile`: Docker configuration
- `docker-compose.yml`: Docker Compose configuration
- `requirements.txt`: Python dependencies