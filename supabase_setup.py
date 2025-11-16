"""
Supabase Connection String Builder
Gebruik dit script om je connection string te bouwen
"""

print("=" * 60)
print("SUPABASE CONNECTION STRING BUILDER")
print("=" * 60)
print()

print("Ga naar je Supabase dashboard en vind de volgende info:")
print("Settings → Database → Connection Info")
print()

# Verzamel info
host = input("1. Host (bijv. db.abcdefghijklmnop.supabase.co): ").strip()
database = input("2. Database name (meestal 'postgres'): ").strip() or "postgres"
port = input("3. Port (meestal '5432' voor direct, '6543' voor pooled): ").strip() or "5432"
user = input("4. User (meestal 'postgres'): ").strip() or "postgres"
password = input("5. Password (je database wachtwoord): ").strip()

print()
print("=" * 60)
print("JE CONNECTION STRING:")
print("=" * 60)

# Voor direct connection (port 5432)
if port == "5432":
    connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    print(connection_string)
else:
    # Voor pooled connection (port 6543)
    # Haal project ref uit de host
    if "db." in host:
        project_ref = host.replace("db.", "").replace(".supabase.co", "")
        connection_string = f"postgresql://{user}.{project_ref}:{password}@{host.replace('db.', 'aws-0-eu-central-1.pooler.')}:{port}/{database}"
    else:
        connection_string = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    print(connection_string)

print()
print("=" * 60)
print("VOLGENDE STAPPEN:")
print("=" * 60)
print()
print("1. Kopieer de connection string hierboven")
print("2. Voeg toe aan je .env bestand:")
print(f"   DATABASE_URL={connection_string}")
print()
print("3. Test de connectie:")
print("   python init_db.py --check")
print()
print("4. Seed de database:")
print("   python init_db.py --seed")
print()
print("=" * 60)
