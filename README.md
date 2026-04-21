# DAX 40 — Backtest & Live Trading (ASRS · Expresso · PDH/PDL)

Quantitative backtest and live execution of three intraday strategies on DAX 40,
based on Tom Hougaard's "School Run" approach.  
Data: Capital.com API (live, ~1 year) + CSV historique 2006–2026 · 5-min bars.

---

## Présentation du projet

Le projet est structuré en trois couches :

1. **Collecte** — `notebooks/00_collect_dax_live.ipynb` récupère les données 5min du DAX
   via l'API Capital.com (demo) et les stocke à la fois dans `data/dax_live_5min.csv`
   et dans la base de données SQLite (`src/database/trading.db`).

2. **Backtest** — `notebooks/strategies.ipynb` analyse les trois stratégies sur les données
   historiques CSV (2006–2026). Une API FastAPI expose également les résultats en temps réel
   depuis la base de données.

3. **Automatisation live** — `scripts/asrs_signal.py` place les ordres OCO au signal,
   `scripts/asrs_monitor.py` surveille la position et ferme manuellement au TP.

---

## Les trois stratégies

| Stratégie | Bougie signal | Buffer | Filtres |
|-----------|--------------|--------|---------|
| **ASRS** | 4ème bougie 5min (09:15 CET) | ±2 pts | range 10–55, pas vendredi, pas jan/juil/août |
| **Expresso** | Bougie pré-ouverture (08:55 CET) | ±17 pts | range 10–55, pas vendredi, pas jan/juil/août |
| **PDH/PDL** | Haut/Bas de la veille | ±5 pts | range 50–300, pas vendredi, pas jan/juil/août |

**Logique commune** : ordres OCO stop au-dessus et en-dessous du signal.
Le premier niveau touché détermine la direction. Stop loss = l'autre niveau d'entrée.
Sortie en fin de journée à 17:30 CET si le stop n'est pas touché.

---

## Limite de l'automatisation

> **Le compte démo Capital.com ne permet pas de fixer un Take Profit natif sur les
> ordres à cours limité (working orders).** Il est techniquement impossible de passer
> un ordre avec `limitLevel` sur un compte démo via l'API REST — Capital.com retourne
> une erreur 400 même si le paramètre est documenté.
>
> En conséquence, `asrs_monitor.py` surveille le prix toutes les 5 secondes et ferme
> la position manuellement quand le TP est atteint (via `DELETE /positions/{dealId}`).
> Sur un compte réel, un TP natif pourrait être fixé directement à l'ordre.

---

## Structure du projet

```
src/
  api/                      # FastAPI — endpoints REST
    routers/backtest_router.py
  dao/                      # Accès base de données SQLite
    candle_dao.py
    trade_dao.py
    db_connection.py
  dto/                      # Schémas de réponse API (Pydantic)
  models/                   # Modèles de données internes
  service/
    backtest_service.py     # Logique des 3 stratégies (ASRS, Expresso, PDHL)
    candle_service.py       # Lecture DB → DataFrame pandas
    collector/
      session_manager.py    # Gestion session Capital.com
      api_client.py         # Client HTTP Capital.com
      parse.py              # Parsing candles API → dicts DB
      db_importer.py        # Insertion candles en base

notebooks/
  00_collect_dax_live.ipynb # Collecte données + insertion DB
  strategies.ipynb          # Backtest des 3 stratégies (20 ans CSV)
  06_tp_regression.ipynb    # Régression MFE / TP optimal
  07_LightGBM.ipynb         # Filtre LightGBM sur les signaux
  features.py               # Feature engineering partagé

scripts/
  asrs_signal.py            # Place les ordres OCO à 09:20 CET
  asrs_monitor.py           # Surveille et ferme la position au TP

data/
  dax_live_5min.csv         # Données live Capital.com (générées par notebook 00)
  dax-5m_bk.csv             # Historique CSV 2006–2026 (backtesting.com)

models/                     # Modèles ML entraînés (.pkl)
```

---

## Installation et démarrage

### Windows

```powershell
# 1. Installer les dépendances
uv sync

# 2. Activer le venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.venv\Scripts\Activate.ps1

# 3. Créer le fichier .env
copy .env.example .env
# Remplir CAPITAL_API_KEY, CAPITAL_IDENTIFIER, CAPITAL_PASSWORD

# 4. Lancer l'API  (Terminal 1)
uvicorn src.api.api:app --port 8000
# Si erreur "port déjà utilisé" (Errno 10048), changer de port :
uvicorn src.api.api:app --port 8001

# 5. Tester les endpoints  (Terminal 2 — pendant que l'API tourne)
curl "http://localhost:8000/health"
curl "http://localhost:8000/backtest?strategy=PDHL"
curl "http://localhost:8000/backtest?strategy=ASRS"
curl "http://localhost:8000/backtest?strategy=EXPRESSO"
# Adapter le port (8001, etc.) si vous avez changé au step 4

# 6. Lancer les tests
python -m pytest
```

### Linux / macOS

```bash
# 1. Installer les dépendances
uv sync

# 2. Activer le venv
source .venv/bin/activate

# 3. Créer le fichier .env
cp .env.example .env
# Remplir CAPITAL_API_KEY, CAPITAL_IDENTIFIER, CAPITAL_PASSWORD

# 4. Lancer l'API  (Terminal 1)
uvicorn src.api.api:app --port 8000
# Si erreur "port déjà utilisé", changer de port :
uvicorn src.api.api:app --port 8001

# 5. Tester les endpoints  (Terminal 2 — pendant que l'API tourne)
curl "http://localhost:8000/health"
curl "http://localhost:8000/backtest?strategy=PDHL"
curl "http://localhost:8000/backtest?strategy=ASRS"
curl "http://localhost:8000/backtest?strategy=EXPRESSO"
# Adapter le port si vous avez changé au step 4

# 6. Lancer les tests
source .venv/bin/activate
python -m pytest

```

---

## Endpoints API

| Méthode | URL | Description |
|---------|-----|-------------|
| GET | `/health` | Statut de l'API |
| GET | `/backtest?strategy=ASRS` | Résultats backtest ASRS |
| GET | `/backtest?strategy=EXPRESSO` | Résultats backtest Expresso |
| GET | `/backtest?strategy=PDHL` | Résultats backtest PDH/PDL |

Documentation interactive : `http://localhost:8000/docs`

---

## Fichier .env requis

```
CAPITAL_API_KEY=...
CAPITAL_IDENTIFIER=...
CAPITAL_PASSWORD=...
```

Compte démo Capital.com suffisant pour la collecte et le backtest.

---

## Résultats backtest (données live ~1 an)

| Stratégie | Trades | Win Rate | Profit Factor | PnL total |
|-----------|--------|----------|---------------|-----------|
| ASRS | 141 | 14.2% | 0.76 | −1 014 pts |
| Expresso | 66 | 30.3% | 1.65 | +1 690 pts |
| PDH/PDL | 101 | 58.4% | 1.68 | +2 795 pts |

> Sur 20 ans de données CSV (2006–2026), l'ASRS avec filtres atteint un Profit Factor de 1.27
> et un PnL total de +9 278 pts — voir `notebooks/strategies.ipynb`.
