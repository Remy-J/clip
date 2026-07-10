# Nexus - Twitch VOD to Clips Automatique

## Vue d'ensemble

Application 100% locale et gratuite pour :
1. Se connecter à Twitch et récupérer les VODs
2. Analyser les VODs pour détecter les moments clés (drôles, dynamiques, marquants, instructifs)
3. Créer automatiquement des clips au format vertical (Shorts/Reels)
4. Publier sur YouTube et Instagram

## Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│                     STACK 100% LOCALE & GRATUITE                        │
├────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐   ┌─────────────────────────────────────┐             │
│  │   Twitch    │   │         ANALYSE LOCALE              │             │
│  │   OAuth     │──▶│  faster-whisper → Ollama/Llama      │             │
│  └─────────────┘   │  + Analyse audio (Librosa)          │             │
│        │           └─────────────────────────────────────┘             │
│        ▼                          │                                     │
│  ┌─────────────┐                  ▼                                     │
│  │  Télécharge │   ┌─────────────────────────────────────┐             │
│  │  VODs       │   │  FFmpeg + MoviePy                   │             │
│  └─────────────┘   │  Découpage, format 9:16, sous-titres│             │
│                    └─────────────────────────────────────┘             │
│                                   │                                     │
│                    ┌──────────────┴──────────────┐                     │
│                    ▼                             ▼                     │
│             ┌───────────┐                 ┌───────────┐                │
│             │  YouTube  │                 │ Instagram │                │
│             └───────────┘                 └───────────┘                │
└────────────────────────────────────────────────────────────────────────┘
```

## Stack Technique

| Composant | Technologie | Coût |
|-----------|-------------|------|
| Backend | Python 3.11 + FastAPI | Gratuit |
| Frontend | React + Vite + TailwindCSS | Gratuit |
| Base de données | SQLite | Gratuit |
| Transcription | faster-whisper (Whisper local) | Gratuit |
| LLM | Ollama + Llama 3.1 8B | Gratuit |
| Analyse audio | Librosa | Gratuit |
| Traitement vidéo | FFmpeg + MoviePy | Gratuit |
| YouTube API | YouTube Data API v3 | Gratuit |
| Instagram API | instagrapi | Gratuit |

## Prérequis Machine

| Composant | Minimum | Recommandé |
|-----------|---------|------------|
| RAM | 8 Go | 16 Go |
| GPU | Pas obligatoire | NVIDIA 6Go+ VRAM |
| Stockage | 20 Go libres | SSD 50 Go+ |
| CPU | 4 cores | 8 cores |

## Structure du Projet

```
nexus/
├── PLAN.md                      # Ce fichier
├── README.md                    # Documentation utilisateur
├── requirements.txt             # Dépendances Python
├── .env.example                 # Variables d'environnement exemple
├── .env                         # Variables d'environnement (à créer)
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Configuration
│   │   │
│   │   ├── twitch/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # OAuth Twitch
│   │   │   ├── api.py           # Récupération VODs
│   │   │   └── downloader.py    # Téléchargement VODs
│   │   │
│   │   ├── analysis/
│   │   │   ├── __init__.py
│   │   │   ├── transcriber.py   # Whisper local
│   │   │   ├── audio.py         # Analyse audio (Librosa)
│   │   │   ├── llm.py           # Ollama/Llama local
│   │   │   └── detector.py      # Combinaison des analyses
│   │   │
│   │   ├── video/
│   │   │   ├── __init__.py
│   │   │   ├── clipper.py       # Découpage FFmpeg
│   │   │   ├── formatter.py     # Formatage 9:16
│   │   │   └── subtitles.py     # Génération sous-titres
│   │   │
│   │   ├── publishers/
│   │   │   ├── __init__.py
│   │   │   ├── youtube.py       # Upload YouTube
│   │   │   └── instagram.py     # Upload Instagram
│   │   │
│   │   └── database/
│   │       ├── __init__.py
│   │       ├── models.py        # SQLAlchemy models
│   │       └── crud.py          # Opérations DB
│   │
│   └── tests/
│       └── __init__.py
│
├── frontend/                    # Dashboard React (Phase 10)
│
└── data/
    ├── vods/                    # VODs téléchargées
    ├── clips/                   # Clips générés
    └── transcripts/             # Transcriptions
```

## Phases de Développement

### Phase 1: Setup ✅
- [x] Structure du projet
- [x] Configuration environnement
- [x] Dépendances

### Phase 2: Authentification Twitch ✅
- [x] Configuration app Twitch Developer Console
- [x] OAuth 2.0 flow (Authorization Code)
- [x] Stockage sécurisé des tokens
- [x] Refresh token automatique

### Phase 3: Récupération VODs ✅
- [x] Liste des VODs via Helix API
- [x] Métadonnées (titre, durée, date, thumbnail)
- [x] Téléchargement avec yt-dlp
- [x] Gestion du stockage local

### Phase 4: Transcription (Whisper) ✅
- [x] Installation faster-whisper
- [x] Transcription avec timestamps
- [x] Support GPU/CPU
- [x] Cache des transcriptions

### Phase 5: Analyse Audio ✅
- [x] Extraction audio (FFmpeg)
- [x] Détection pics d'énergie (Librosa)
- [x] Détection silences/explosions
- [x] Scoring des segments

### Phase 6: Analyse LLM ✅
- [x] Installation Ollama + Llama 3.1
- [x] Prompt engineering pour détection moments
- [x] Analyse de la transcription
- [x] Classification (drôle/instructif/marquant)

### Phase 7: Création Clips ✅
- [x] Découpage aux timestamps
- [x] Reformatage 9:16 (vertical)
- [x] Ajout sous-titres automatiques
- [x] Fond flouté pour vidéos horizontales

### Phase 8: YouTube Upload ✅
- [x] Configuration Google Cloud Console
- [x] OAuth YouTube
- [x] Upload avec métadonnées
- [x] Gestion Shorts

### Phase 9: Instagram Upload ✅
- [x] Support instagrapi (unofficial)
- [x] Support Graph API (official)
- [x] Upload Reels

### Phase 10: Frontend ✅
- [x] Dashboard React avec statistiques
- [x] Liste VODs avec sync Twitch
- [x] Galerie de clips avec filtres
- [x] Page paramètres complète
- [x] Interface de publication YouTube/Instagram
- [x] Design moderne avec TailwindCSS

## APIs et Credentials Requis

### Twitch (gratuit)
1. Aller sur https://dev.twitch.tv/console
2. Créer une application
3. Récupérer Client ID et Client Secret
4. Configurer Redirect URI: `http://localhost:8000/auth/twitch/callback`

### YouTube (gratuit)
1. Aller sur https://console.cloud.google.com
2. Créer un projet
3. Activer YouTube Data API v3
4. Créer credentials OAuth 2.0
5. Configurer écran de consentement

### Instagram (gratuit)
1. Convertir compte en Business/Creator
2. Lier une page Facebook
3. Créer app sur https://developers.facebook.com
4. Configurer Instagram Graph API

## Commandes Utiles

```bash
# Installation
pip install -r requirements.txt

# Lancer le backend
cd backend && uvicorn app.main:app --reload

# Lancer Ollama (dans un autre terminal)
ollama serve

# Télécharger Llama 3.1
ollama pull llama3.1:8b

# Lancer le frontend (Phase 10)
cd frontend && npm run dev
```

## Notes Techniques

### Whisper - Choix du modèle
- `tiny` : Très rapide, moins précis
- `base` : Bon compromis
- `small` : Recommandé pour la plupart des cas
- `medium` : Meilleure qualité, plus lent
- `large-v3` : Meilleure qualité, nécessite GPU

### Llama - Choix du modèle
- `llama3.1:8b` : Recommandé, bon équilibre
- `mistral:7b` : Alternative légère
- `phi3:mini` : Très léger, moins précis

### Format Clips
- YouTube Shorts : 9:16, max 60 secondes
- Instagram Reels : 9:16, max 90 secondes
- Résolution : 1080x1920 recommandé
