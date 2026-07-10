# Nexus

Application de création automatique de clips à partir de VODs Twitch.

## Fonctionnalités

- 🎮 Connexion Twitch OAuth
- 📥 Téléchargement automatique des VODs
- 🤖 Analyse IA locale (Whisper + Llama)
- ✂️ Création de clips verticaux (Shorts/Reels)
- 📤 Publication YouTube et Instagram

## Installation

### Prérequis

- Python 3.11+
- FFmpeg
- Ollama (pour l'analyse LLM)

### Setup

1. Cloner le projet et installer les dépendances :

```bash
pip install -r requirements.txt
```

2. Copier le fichier d'environnement :

```bash
cp .env.example .env
```

3. Configurer vos credentials dans `.env`

4. Installer Ollama et télécharger Llama :

```bash
# Windows: télécharger depuis https://ollama.ai
# Puis:
ollama pull llama3.1:8b
```

5. Lancer l'application :

```bash
cd backend
uvicorn app.main:app --reload
```

6. Ouvrir http://localhost:8000

## Configuration

Voir [PLAN.md](PLAN.md) pour les détails de configuration des APIs.

## Licence

MIT
