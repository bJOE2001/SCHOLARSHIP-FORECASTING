# ScholarSync ML Forecasting & Risk Service

FastAPI-based Machine Learning microservice powering applicant forecasting, scholar risk detection, and applicant ranking for the ScholarSync platform.

---

## 📋 Features

- **Random Forest Forecasting**: Predicts monthly scholarship applicant volume and confidence intervals based on historical application trends.
- **Decision Tree Risk Evaluation**: Classifies scholars into `Stable`, `Borderline`, or `At Risk` based on GPA margin deficit against program maintaining grades.
- **Multi-Factor Applicant Ranking**: Scores incoming applicants using a weighted composite model evaluating merit, financial need, application completeness, and priority course alignment.

---

## 🚀 Running the Service (Local Development)

### 1. Prerequisites
Ensure Python 3.10+ is installed:
```powershell
python --version
```

### 2. Install Dependencies
```powershell
cd C:\xampp\htdocs\SCHOLARSHIP-FORECASTING
pip install -r requirements.txt
```

### 3. Start the FastAPI Server
Run the service with Uvicorn on port `8001`:

```powershell
cd C:\xampp\htdocs\SCHOLARSHIP-FORECASTING
python -m uvicorn app:app --host 127.0.0.1 --port 8001 --reload
```

> **Note on Port 8001:** The Laravel backend (`SCHOLARSHIP-BACKEND`) expects the service at `http://127.0.0.1:8001` (leaving port `8000` reserved for Laravel's `php artisan serve`).

---

## 🔍 Verification & Interactive Docs

Once running, verify the service in your browser or with curl:

- **Health Check Endpoint**: [http://127.0.0.1:8001/health](http://127.0.0.1:8001/health)  
  Returns:
  ```json
  {"status": "ok", "service": "scholarship-forecasting"}
  ```
- **Interactive OpenAPI/Swagger Documentation**: [http://127.0.0.1:8001/docs](http://127.0.0.1:8001/docs)
- **ReDoc Documentation**: [http://127.0.0.1:8001/redoc](http://127.0.0.1:8001/redoc)

---

## 🧪 Running Automated Tests

Run the test suite using `pytest`:

```powershell
cd C:\xampp\htdocs\SCHOLARSHIP-FORECASTING
python -m pytest tests
```

Tests cover API endpoints, model training, risk evaluation logic, and applicant ranking calculations.

---

## 📦 Populating Data in Laravel Backend

To generate realistic multi-month cohorts for training and testing forecasting in the backend:

```bash
cd C:\xampp\htdocs\SCHOLARSHIP-BACKEND
php artisan scholarship:seed-ml-cohorts --months=6 --per-month=6
```

---

## 🌐 Production Deployment (Linux / DigitalOcean)

### Automated Setup Script
An automated setup script is available in `deploy/setup-digitalocean.sh`:

```bash
cd /var/www/SCHOLARSHIP-FORECASTING
bash deploy/setup-digitalocean.sh
```

### Manual Gunicorn Execution
To run manually using Gunicorn with Uvicorn workers:

```bash
gunicorn app:app -c gunicorn.conf.py
```

### Systemd Service Management
The service can be managed via systemd:

```bash
sudo systemctl start scholarship-forecasting
sudo systemctl status scholarship-forecasting
sudo systemctl restart scholarship-forecasting
sudo journalctl -u scholarship-forecasting -f
```

---

## 🛠️ API Endpoints Summary

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Service health status check |
| `POST` | `/forecast` | Random Forest applicant volume prediction |
| `POST` | `/risk-detection/evaluate` | Batch scholar risk evaluation |
| `POST` | `/ranking/evaluate` | Multi-factor applicant ranking evaluation |

