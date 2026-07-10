# TODO - Tâches Utilisateur

Ces tâches nécessitent une action manuelle de ta part. Le code est prêt, il ne reste que la configuration.

---

## 1. Installer FFmpeg

- [ ] Télécharger FFmpeg depuis https://www.gyan.dev/ffmpeg/builds/ (version "essentials")
- [ ] Extraire dans `C:\ffmpeg`
- [ ] Ajouter `C:\ffmpeg\bin` au PATH système :
  - Rechercher "Variables d'environnement" dans Windows
  - Modifier la variable `Path`
  - Ajouter `C:\ffmpeg\bin`
- [ ] Redémarrer le terminal
- [ ] Vérifier avec `ffmpeg -version`

---

## 2. Installer Ollama + Modèle LLM

- [ ] Télécharger Ollama depuis https://ollama.ai/download
- [ ] Installer l'application
- [ ] Lancer Ollama
- [ ] Ouvrir un terminal et exécuter :
  ```bash
  ollama pull llama3.1:8b
  ```
- [ ] Vérifier avec `ollama list`

---

## 3. Configurer Twitch API

- [ ] Aller sur https://dev.twitch.tv/console
- [ ] Se connecter avec ton compte Twitch
- [ ] Cliquer sur "Register Your Application"
- [ ] Remplir :
  - **Nom** : Nexus
  - **OAuth Redirect URL** : `http://localhost:8000/auth/twitch/callback`
  - **Catégorie** : Application Integration
- [ ] Cliquer sur "Create"
- [ ] Copier le **Client ID**
- [ ] Cliquer sur "New Secret" pour générer le **Client Secret**
- [ ] Ouvrir le fichier `.env` et remplir :
  ```
  TWITCH_CLIENT_ID=ton_client_id
  TWITCH_CLIENT_SECRET=ton_client_secret
  ```

---

## 4. Configurer YouTube API (optionnel - pour publication)

- [ ] Aller sur https://console.cloud.google.com
- [ ] Créer un nouveau projet (ex: "Nexus")
- [ ] Dans le menu, aller dans "APIs & Services" > "Library"
- [ ] Chercher et activer "YouTube Data API v3"
- [ ] Aller dans "APIs & Services" > "Credentials"
- [ ] Cliquer "Create Credentials" > "OAuth client ID"
- [ ] Type : "Desktop application"
- [ ] Télécharger le fichier JSON
- [ ] Renommer en `youtube_credentials.json`
- [ ] Placer dans le dossier `data/`

---

## 5. Configurer Instagram (optionnel - pour publication)

### Option A : Compte standard (via instagrapi)
- [ ] Au premier lancement, l'app te demandera tes identifiants Instagram
- [ ] La session sera sauvegardée automatiquement

### Option B : Compte Business (API officielle)
- [ ] Convertir ton compte Instagram en compte Professionnel
- [ ] Créer une page Facebook et la lier
- [ ] Créer une app sur https://developers.facebook.com
- [ ] Configurer les permissions Instagram

---

## 6. Premier Lancement

- [ ] Copier `.env.example` vers `.env` (si pas déjà fait)
- [ ] Remplir les credentials Twitch dans `.env`
- [ ] Ouvrir un terminal dans le dossier du projet
- [ ] Exécuter `scripts\setup.bat` (installation)
- [ ] Puis `scripts\start-all.bat` (lance backend + frontend)
- [ ] Ouvrir http://localhost:5173 (frontend)
- [ ] Cliquer sur "Connexion Twitch"

### Scripts disponibles
- `scripts\setup.bat` - Installation complète
- `scripts\start-all.bat` - Lance tout (backend + frontend)
- `scripts\start-backend.bat` - Lance uniquement le backend
- `scripts\start-frontend.bat` - Lance uniquement le frontend

---

## Vérification Rapide

Une fois tout configuré, va sur http://localhost:8000/api/system/check pour vérifier que tout est OK.
