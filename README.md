# GreenBasket — Data-Driven Organic Grocery Retail Prototype

A Flask + SQLite academic prototype demonstrating an organic grocery storefront and a retail analytics dashboard.

## Features
- Responsive grocery homepage with sample product catalogue
- Admin login and protected analytics dashboard
- Descriptive analysis: revenue by category
- Diagnostic view: top products by units sold
- Predictive view: simple average-based next-day sales estimate
- Prescriptive view: low-stock restock recommendations
- Sample demonstration orders created automatically only when the orders table is empty
- Deployment files for a Gunicorn-based host such as Render

## Requirements
- Python 3.10+
- Internet connection for Bootstrap and Chart.js CDN assets

## Run locally (Windows)
1. Extract the ZIP.
2. Open the extracted `GreenBasket_Prototype` folder in VS Code.
3. Open Terminal in that folder.
4. Create a virtual environment:

   ```bash
   py -m venv .venv
   .venv\\Scripts\\activate
   ```

5. Install packages:

   ```bash
   pip install -r requirements.txt
   ```

6. Run the app:

   ```bash
   python app.py
   ```

7. Open `http://127.0.0.1:5000/` for the homepage.
8. Open `http://127.0.0.1:5000/admin/login` for the dashboard login.

## Local demo login
- Username: `admin`
- Password: `GreenBasket@123`

This password is only for local academic demonstration. Before hosting publicly, set a strong `ADMIN_PASSWORD` and a secure `SECRET_KEY` environment variable. If you already ran a previous version that created an admin account, changing the environment variable will not change that existing account's password.

## Hosting
This project includes `Procfile` and `render.yaml` for Render-style deployment:
1. Upload the project to a GitHub repository (do not upload `.env` or a real database).
2. Create a new Web Service from that repository.
3. Build command: `pip install -r requirements.txt`
4. Start command: `gunicorn app:app`
5. Set `SECRET_KEY` to a strong random value and `ADMIN_PASSWORD` to a strong password in host environment variables.
6. Important: the default SQLite database is stored in the app directory. On many cloud hosts, local files may reset on redeploy/restart. For persistent hosted data, attach a persistent disk and set `DATABASE_PATH` to a file path on that disk, or migrate to a managed PostgreSQL database. For a classroom prototype, demo data can be recreated on startup.

## Project structure
```text
GreenBasket_Prototype/
├── app.py
├── db.py
├── requirements.txt
├── Procfile
├── render.yaml
├── .env.example
├── .gitignore
├── README.md
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   └── dashboard.html
└── static/
    └── css/
        └── style.css
```

## Analytics note
All seeded orders are demonstration data, not real customer transactions. The prediction is intentionally simple and intended to demonstrate the concept, not to claim statistically reliable forecasting. Diagnostic sales comparisons show patterns but do not establish why customers purchased a product.
