# Requirements Bestanden

## requirements.txt
**Voor: Vercel deployment (productie)**

Dit bestand bevat alleen de essentiële packages die nodig zijn voor de productie omgeving op Vercel.
Zware packages zoals pandas en boto3 zijn NIET inbegrepen om onder de 250MB Vercel limiet te blijven.

## requirements-local.txt
**Voor: Lokale development**

Dit bestand bevat ALLE packages inclusief:
- pandas (voor simulatie functionaliteit)
- boto3/botocore (AWS functionaliteit)
- faker (voor test data)
- Alle andere development tools

## Installatie

### Lokaal ontwikkelen:
```bash
pip install -r requirements-local.txt
```

### Vercel deployment:
Vercel gebruikt automatisch `requirements.txt` (geen actie nodig)
