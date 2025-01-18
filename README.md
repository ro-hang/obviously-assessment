# Books CRUD API

A FastAPI application providing a JWT-protected CRUD interface for managing books. Includes real-time Server-Sent Events (SSE) to broadcast create/read/update/delete actions, and paginated responses with next/previous links.

## Features

- **Authentication:** Hardcoded username/password (testuser / testpass)
- **CRUD:** Create, read, update, delete books in an SQLite database
- **Pagination:** `/books/` returns data, total_count, and next_url / prev_url
- **SSE:** Real-time updates at `/sse`
- **Swagger:** Automatic docs at `/docs`
- **JWT:** All endpoints except `/login` require a Bearer token

## Local Setup

1. **Clone this repository:**
   ```bash
   git clone https://github.com/ro-hang/obviously-assessment.git
   cd obviously-assessment
   ```

2. **Create a virtual environment (recommended) and activate it:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application locally:**
   ```bash
   uvicorn app.main:app --reload
   ```

   The server will start at http://127.0.0.1:8000.

## Usage

1. Open your browser to http://127.0.0.1:8000/docs to see the Swagger UI.

2. **Authorize:**
   - Click Authorize
   - Either:
     - Enter username=`testuser` and password=`testpass` if using the OAuth2 "password flow"
     - Provide a token if you already have one
   - Now you can test all endpoints (CRUD + SSE)