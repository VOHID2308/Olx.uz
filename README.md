# OLX.UZ Marketplace Backend

OLX.UZ ga o'xshash sodda marketplace backend platformasi. Django va Django REST Framework bilan qurilgan.

## Texnologiyalar
- Django 4.2
- Django REST Framework
- PostgreSQL
- Simple JWT (autentifikatsiya)
- drf-spectacular (Swagger API docs)
- django-filter (filterlash)

---

## O'rnatish va Ishga Tushirish

### 1. Repository'ni clone qiling
```bash
git clone https://github.com/yourusername/olx-uz-backend.git
cd olx-uz-backend
```

### 2. Virtual muhit yarating
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 3. Kerakli kutubxonalarni o'rnating
```bash
pip install -r requirements.txt
```

### 4. .env faylni sozlang
```bash
cp .env.example .env
# .env faylini o'z ma'lumotlaringiz bilan to'ldiring
```

### 5. PostgreSQL bazasini yarating
```sql
CREATE DATABASE olx_uz_db;
CREATE USER olx_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE olx_uz_db TO olx_user;
```

### 6. Migratsiyalarni bajaring
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Superuser yarating
```bash
python manage.py createsuperuser
```

### 8. Serverni ishga tushiring
```bash
python manage.py runserver
```

---

## API Hujjatlari

Swagger UI: `http://localhost:8000/api/docs/`  
ReDoc: `http://localhost:8000/api/redoc/`

---

## .env fayl namunasi

```env
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=olx_uz_db
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=localhost
DB_PORT=5432

TELEGRAM_BOT_TOKEN=your-telegram-bot-token
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

---

## API Endpointlar

### Autentifikatsiya
| Method | URL | Tavsif |
|--------|-----|--------|
| POST | `/api/v1/auth/telegram-login/` | Telegram orqali login |
| POST | `/api/v1/auth/refresh/` | Token yangilash |
| POST | `/api/v1/auth/logout/` | Chiqish |

### Foydalanuvchilar
| Method | URL | Tavsif |
|--------|-----|--------|
| GET/PATCH | `/api/v1/users/me/` | O'z profili |
| POST | `/api/v1/users/me/upgrade-to-seller/` | Sotuvchi bo'lish |
| GET | `/api/v1/sellers/{id}/` | Sotuvchi profili |
| GET | `/api/v1/sellers/{id}/products/` | Sotuvchi mahsulotlari |

### Kategoriyalar
| Method | URL | Tavsif |
|--------|-----|--------|
| GET | `/api/v1/categories/` | Barcha kategoriyalar |
| GET | `/api/v1/categories/{slug}/` | Bitta kategoriya |
| GET | `/api/v1/categories/{slug}/products/` | Kategoriya mahsulotlari |

### Mahsulotlar
| Method | URL | Tavsif |
|--------|-----|--------|
| GET | `/api/v1/products/` | Aktiv mahsulotlar (filter, search) |
| POST | `/api/v1/products/` | Yangi e'lon (seller) |
| GET/PATCH/DELETE | `/api/v1/products/{id}/` | Bitta mahsulot |
| POST | `/api/v1/products/{id}/publish/` | E'lonni nashr qilish |
| POST | `/api/v1/products/{id}/archive/` | Arxivlash |
| POST | `/api/v1/products/{id}/sold/` | Sotilgan deb belgilash |

### Sevimlilar
| Method | URL | Tavsif |
|--------|-----|--------|
| GET/POST | `/api/v1/favorites/` | Sevimlilar |
| DELETE | `/api/v1/favorites/{id}/` | O'chirish |

### Buyurtmalar
| Method | URL | Tavsif |
|--------|-----|--------|
| GET/POST | `/api/v1/orders/` | Buyurtmalar |
| GET/PATCH | `/api/v1/orders/{id}/` | Bitta buyurtma |

### Fikrlar
| Method | URL | Tavsif |
|--------|-----|--------|
| GET/POST | `/api/v1/reviews/` | Fikrlar |

---

## Loyiha Strukturasi

```
olx_uz/
├── apps/
│   ├── users/         # Foydalanuvchilar va autentifikatsiya
│   ├── categories/    # Kategoriyalar
│   ├── products/      # Mahsulotlar va sevimlilar
│   ├── orders/        # Buyurtmalar
│   └── reviews/       # Fikr va reytinglar
├── config/
│   ├── settings.py
│   └── urls.py
├── manage.py
├── requirements.txt
└── .env.example
```