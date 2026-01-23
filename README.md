
# FinanceManager Pro

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![Django](https://img.shields.io/badge/django-6.0-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

**Solution SaaS B2B de gestion financière pour PME et cabinets comptables**

[Documentation](#-documentation) • [Installation](#-installation) • [API](#-api-endpoints) • [Contribution](#-contribution)

</div>

---

##  À propos

FinanceManager Pro est une application de gestion financière complète conçue pour les PME françaises. Elle offre :

- **Facturation** — Création, validation et suivi des factures
- **Trésorerie** — Gestion des transactions et rapprochement bancaire
- **Multi-tenant** — Gestion de plusieurs entreprises avec isolation des données
- **Sécurité** — Authentification Supabase avec JWT et Row Level Security

---

## Fonctionnalités

| Module | Description |
|--------|-------------|
|  **Authentification** | Email/password, Google OAuth, vérification email |
|  **Multi-entreprise** | Gestion de plusieurs sociétés avec rôles différenciés |
|  **Facturation** | Création, validation, numérotation automatique, export PDF |
|  **Clients** | Gestion complète du portefeuille clients |
|  **Trésorerie** | Suivi des entrées/sorties, solde en temps réel |
|  **Rapprochement** | Association transactions bancaires ↔ factures |
|  **Équipe** | Invitations, gestion des rôles et permissions |

---

## 🛠 Stack technique

- **Backend** : Django 6.0 + Django REST Framework
- **Base de données** : PostgreSQL (Supabase)
- **Authentification** : Supabase Auth (JWT)
- **Sécurité** : Row Level Security (RLS)
- **Documentation** : drf-spectacular (OpenAPI 3.0)
- **Desktop** : Electron + React + TypeScript

---

## 🚀 Installation

### Prérequis

- Python 3.11+
- PostgreSQL (ou compte Supabase)
- Node.js 18+ (pour l'application desktop)

### Backend

```bash
# Cloner le repository
git clone https://github.com/flo0700/FinanceManager-Pro-.git
cd FinanceManager-Pro-/backend

# Créer l'environnement virtuel
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# Installer les dépendances
pip install --upgrade pip
pip install -r requirements.txt
```

### Configuration

Créer un fichier `.env` dans [backend/](/FinanceManager-Pro-/backend) :

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=127.0.0.1,localhost

# Base de données
DATABASE_URL=postgresql://user:password@host:5432/database

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
```

### Lancement

```bash
# Appliquer les migrations
python manage.py migrate

# Démarrer le serveur
python manage.py runserver
```

L'API est accessible sur `http://127.0.0.1:8000`

---

## 📚 Documentation

| Interface | URL |
|-----------|-----|
| **Swagger UI** | http://127.0.0.1:8000/api/docs/ |
| **ReDoc** | http://127.0.0.1:8000/api/redoc/ |
| **Schema OpenAPI** | http://127.0.0.1:8000/api/schema/ |

---

## 🔗 API Endpoints

### Authentification

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Inscription |
| `POST` | `/api/v1/auth/login` | Connexion |
| `GET` | `/api/v1/auth/google` | OAuth Google |
| `POST` | `/api/v1/auth/refresh` | Rafraîchir le token |
| `POST` | `/api/v1/auth/logout` | Déconnexion |
| `GET` | `/api/v1/me` | Profil utilisateur |

### Entreprises

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/v1/companies/` | Liste des entreprises |
| `POST` | `/api/v1/companies/create` | Créer une entreprise |
| `GET` | `/api/v1/tenants/` | Tenants de l'utilisateur |

### Facturation

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/v1/invoices/` | Liste des factures |
| `POST` | `/api/v1/invoices/create` | Créer une facture |
| `GET` | `/api/v1/invoices/{id}` | Détail facture |
| `POST` | `/api/v1/invoices/{id}/validate` | Valider une facture |
| `GET` | `/api/v1/invoices/customers/` | Liste des clients |
| `POST` | `/api/v1/invoices/customers/create` | Créer un client |

### Trésorerie

| Méthode | Endpoint | Description |
|---------|----------|-------------|
| `GET` | `/api/v1/treasury/dashboard` | Tableau de bord |
| `GET` | `/api/v1/treasury/transactions/` | Transactions |
| `POST` | `/api/v1/treasury/transactions/create` | Nouvelle transaction |
| `GET` | `/api/v1/treasury/reconciliations/` | Rapprochements |

---

## 🏗 Architecture

```
FinanceManager-Pro-/
├── backend/                 # API Django
│   ├── apps/
│   │   ├── authentication/  # Auth Supabase
│   │   ├── companies/       # Gestion entreprises
│   │   ├── invoices/        # Facturation & clients
│   │   ├── treasury/        # Trésorerie
│   │   └── users/           # Utilisateurs
│   └── config/              # Configuration Django
├── desktop/                 # Application Electron
│   └── financemanager-desktop/
└── AGENTS/                  # Documentation projet
```

---

## 🤝 Contribution

1. Fork le projet
2. Créer une branche (`git checkout -b feature/amazing-feature`)
3. Commit (`git commit -m 'Add amazing feature'`)
4. Push (`git push origin feature/amazing-feature`)
5. Ouvrir une Pull Request

---

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

<div align="center">

**FinanceManager Pro** — Simplifiez la gestion financière de votre PME

</div>
```

---

## 👥 Équipe

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/flo0700">
        <img src="https://github.com/flo0700.png" width="80px;" alt="flo0700"/>
        <br />
        <sub><b>flo0700</b></sub>
      </a>
    </td>
    <td align="center">
      <a href="https://github.com/sony-level">
        <img src="https://github.com/sony-level.png" width="80px;" alt="sony-level"/>
        <br />
        <sub><b>sony-level</b></sub>
      </a>
    </td>
    <!-- Ajouter d'autres collaborateurs ici -->
  </tr>
</table>

---