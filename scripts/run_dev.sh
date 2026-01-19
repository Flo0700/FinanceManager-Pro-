#!/bin/bash
echo "🚀 Démarrage de FinanceManager Pro..."
cd backend
source .venv/bin/activate
python manage.py migrate
python manage.py runserver