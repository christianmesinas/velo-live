# Velo Live - Deployment Guide

Deze guide legt uit hoe je de Velo Live Flask applicatie kan deployen op verschillende platforms.

## 📋 Inhoudsopgave

- [Docker (Lokaal)](#docker-lokaal)
- [Vercel (Serverless)](#vercel-serverless)
- [Database Setup](#database-setup)
- [Environment Variables](#environment-variables)

---

## 🐳 Docker (Lokaal)

### Vereisten
- Docker Desktop geïnstalleerd
- Docker Compose geïnstalleerd

### Quick Start

1. **Clone de repository en navigeer naar de directory:**
   ```bash
   cd velo-live
   ```

2. **Maak een `.env` bestand aan:**
   ```bash
   cp .env.example .env
   ```

3. **Vul de environment variables in** (zie [Environment Variables](#environment-variables))

4. **Build en start de containers:**
   ```bash
   docker-compose up --build
   ```

   Of in detached mode:
   ```bash
   docker-compose up -d --build
   ```

5. **De applicatie is nu beschikbaar op:**
   - **Web App**: http://localhost:8000
   - **pgAdmin**: http://localhost:8080
   - **PostgreSQL**: localhost:5433

### Docker Services

De `docker-compose.yml` bevat 4 services:

- **db**: PostgreSQL 15 database
- **pgadmin**: Database beheer interface
- **web**: Flask web applicatie (met gunicorn)
- **app**: Simulatie script

### Database initialiseren

De database wordt automatisch geïnitialiseerd bij de eerste start. Als je de database handmatig wil opnieuw seeden:

```bash
docker-compose exec web python init_db.py --reset
docker-compose exec web python init_db.py --seed
```

### Docker Commands

```bash
# Stop alle containers
docker-compose down

# Stop en verwijder volumes (verwijdert database data!)
docker-compose down -v

# Bekijk logs
docker-compose logs -f web

# Herstart een service
docker-compose restart web

# Database status controleren
docker-compose exec web python init_db.py --check
```

---

## ☁️ Vercel (Serverless)

Vercel is een serverless platform, ideaal voor Flask apps met een externe database.

### Vereisten
- Vercel account (gratis tier beschikbaar)
- Node.js en npm geïnstalleerd (voor Vercel CLI)
- **Externe PostgreSQL database** (zie [Database Opties](#database-opties))

### Setup Stappen

1. **Installeer Vercel CLI:**
   ```bash
   npm install -g vercel
   ```

2. **Login bij Vercel:**
   ```bash
   vercel login
   ```

3. **Configureer een externe database** (zie [Database Opties](#database-opties))

4. **Deploy naar Vercel:**
   ```bash
   # Test deployment
   vercel

   # Production deployment
   vercel --prod
   ```

5. **Configureer environment variables in Vercel:**

   Via de Vercel CLI:
   ```bash
   vercel env add DATABASE_URL
   vercel env add SECRET_KEY
   vercel env add STRIPE_SECRET_KEY
   vercel env add AUTH0_CLIENT_ID
   vercel env add AUTH0_CLIENT_SECRET
   vercel env add AUTH0_DOMAIN
   ```

   Of via het Vercel Dashboard:
   - Ga naar je project in Vercel
   - Settings → Environment Variables
   - Voeg alle benodigde variabelen toe

### Database initialiseren voor Vercel

Omdat Vercel serverless is, moet je de database apart initialiseren:

1. **Lokaal met remote database:**
   ```bash
   # Stel DATABASE_URL in .env in naar je remote database
   DATABASE_URL=postgresql://user:password@your-db-host:5432/dbname

   # Initialiseer database
   python init_db.py --seed
   ```

2. **Of via een Docker container:**
   ```bash
   docker run --rm -it \
     -e DATABASE_URL=your_database_url \
     -e AUTH0_CLIENT_ID=your_client_id \
     -e AUTH0_CLIENT_SECRET=your_secret \
     -e AUTH0_DOMAIN=your_domain \
     -v $(pwd):/app \
     -w /app \
     python:3.11-slim \
     bash -c "pip install -r requirements.txt && python init_db.py --seed"
   ```

### Vercel Configuratie

De app bevat al de volgende Vercel configuratie bestanden:

- `vercel.json` - Vercel deployment configuratie
- `api/index.py` - Serverless entry point
- `.vercelignore` - Bestanden die niet geüpload worden

---

## 💾 Database Setup

### Database Opties

#### Optie 1: Docker (Lokaal Development)
De `docker-compose.yml` bevat al een PostgreSQL container. Geen extra setup nodig!

#### Optie 2: Supabase (Gratis, Aanbevolen voor Vercel)
1. Ga naar [supabase.com](https://supabase.com)
2. Maak een gratis project aan
3. Kopieer de PostgreSQL connection string
4. Gebruik deze als `DATABASE_URL`

#### Optie 3: Railway
1. Ga naar [railway.app](https://railway.app)
2. Maak een PostgreSQL database aan
3. Kopieer de connection string

#### Optie 4: Neon
1. Ga naar [neon.tech](https://neon.tech)
2. Maak een gratis project aan
3. Kopieer de connection string

#### Optie 5: AWS RDS / Google Cloud SQL
Voor productie workloads met meer traffic.

### Database Migratie Tool

Het `init_db.py` script helpt bij database management:

```bash
# Controleer database status
python init_db.py --check

# Maak alleen tabellen aan
python init_db.py --create-tables

# Maak tabellen aan + seed data
python init_db.py --seed

# Reset database (VOORZICHTIG!)
python init_db.py --reset
```

---

## 🔐 Environment Variables

Maak een `.env` bestand aan met de volgende variabelen:

```env
# Database
DATABASE_URL=postgresql://user:password@host:5432/database

# Flask
SECRET_KEY=your-secret-key-hier-maak-dit-lang-en-random

# Stripe
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...

# Auth0
AUTH0_DOMAIN=your-domain.eu.auth0.com
AUTH0_CLIENT_ID=your-client-id
AUTH0_CLIENT_SECRET=your-client-secret

# AWS (optioneel, voor S3 uploads)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_S3_BUCKET=your-bucket

# Optional
PORT=8000
```

### Secret Key Genereren

Voor een veilige secret key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 🚀 Production Checklist

Voordat je naar productie gaat:

- [ ] Alle environment variables zijn geconfigureerd
- [ ] `SECRET_KEY` is een sterke, random string
- [ ] Database is correct geïnitialiseerd
- [ ] `DEBUG` mode is uitgeschakeld (niet in .env)
- [ ] HTTPS is ingeschakeld
- [ ] Database backups zijn geconfigureerd
- [ ] Monitoring is ingesteld (optioneel)
- [ ] Rate limiting is geconfigureerd (optioneel)

---

## 🔧 Troubleshooting

### Docker Issues

**Database connectie mislukt:**
```bash
# Controleer of de database container draait
docker-compose ps

# Bekijk database logs
docker-compose logs db

# Herstart database
docker-compose restart db
```

**Port al in gebruik:**
```bash
# Verander de poort in docker-compose.yml
ports:
  - "8001:8000"  # Gebruik 8001 in plaats van 8000
```

### Vercel Issues

**Deployment faalt:**
- Controleer de Vercel build logs in het dashboard
- Zorg dat alle dependencies in `requirements.txt` staan
- Check of `api/index.py` correct is geconfigureerd

**Database connectie faalt:**
- Controleer of `DATABASE_URL` correct is geconfigureerd
- Test de connectie lokaal met dezelfde URL
- Zorg dat de database externe connecties toelaat

**Import errors:**
- Controleer dat alle paths relatief zijn
- Zorg dat `PYTHONPATH` niet nodig is

---

## 📚 Meer Informatie

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Vercel Documentation](https://vercel.com/docs)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

---

## 🆘 Support

Bij problemen:
1. Check de logs (`docker-compose logs` of Vercel dashboard)
2. Controleer de database status (`python init_db.py --check`)
3. Valideer environment variables
4. Raadpleeg deze documentatie

Happy deploying! 🎉
