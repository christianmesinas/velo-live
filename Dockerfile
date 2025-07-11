# Gebruik een lichte Python-image
FROM python:3.13-slim

# Werkmap in de container
WORKDIR /app

# Kopieer requirements en installeer
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopieer alle overige bestanden
COPY . .

# Geen CMD nodig, want deze wordt overschreven in docker-compose.yml