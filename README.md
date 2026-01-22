# FinanceManager Pro

API de gestion financière pour PME avec authentification Supabase.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL (or Supabase account)

### Installation

```bash
# Clone the repository
git clone https://github.com/your-username/FinanceManager-Pro-.git
cd FinanceManager-Pro-/backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac

# Install dependenciespip install -r requirements.txt
python.exe -m pip install --upgrade pip
```

### Configuration

Create a `.env` file in `backend/`:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@host:5432/database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
```

### Run

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

API: `http://127.0.0.1:8000`

## 📚 API Documentation

- **Swagger UI**: http://127.0.0.1:8000/api/docs/
- **ReDoc**: http://127.0.0.1:8000/api/redoc/
- **UserDoc**: http://127.0.0.1:8000/api/userdoc/

## 🔗 Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register |
| POST | `/api/v1/auth/login` | Login |
| GET | `/api/v1/auth/google` | Google OAuth |
| POST | `/api/v1/auth/refresh` | Refresh token |
| POST | `/api/v1/auth/logout` | Logout |
| GET | `/api/v1/me` | User profile |
| GET | `/api/v1/companies/` | List companies |
| GET | `/api/v1/invoices/` | List invoices |
| GET | `/api/v1/treasury/dashboard` | Treasury |



