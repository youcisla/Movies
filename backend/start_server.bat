@echo off
cls
echo 🎬 Lancement du Système de Recommandation de Films
echo =====================================================
echo.

REM Se déplacer dans le bon répertoire
cd /d "%~dp0"

REM Vérification de Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python n'est pas installé. Veuillez installer Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python détecté

REM Vérifier si les dépendances sont installées
echo 📦 Vérification des dépendances...
pip show django >nul 2>&1
if %errorlevel% neq 0 (
    echo 📦 Installation des dépendances...
    pip install -r requirements_simple.txt
)

echo ✅ Dépendances OK

REM Configuration de l'environnement
if not exist .env (
    echo 📝 Création du fichier .env...
    copy .env.example .env
    echo ⚠️  Fichier .env créé avec la configuration par défaut
)

echo 🗄️  Configuration de la base de données SQLite...

REM Migration avec la version simple
python manage_simple.py makemigrations 2>nul
if %errorlevel% neq 0 (
    echo ⚠️  Création des migrations...
    python manage_simple.py makemigrations movies
)

python manage_simple.py migrate
if %errorlevel% neq 0 (
    echo ❌ Erreur lors de la migration de la base de données
    pause
    exit /b 1
)

echo ✅ Base de données configurée

REM Collecte des fichiers statiques
echo 📂 Collecte des fichiers statiques...
python manage_simple.py collectstatic --noinput >nul 2>&1

echo.
echo 🎉 Configuration terminée !
echo.
echo 🚀 Le serveur va démarrer automatiquement...
echo.
echo 🔗 Accès à l'application :
echo    - Site web : http://127.0.0.1:8000
echo    - Administration : http://127.0.0.1:8000/admin
echo.
echo 📋 Après le démarrage :
echo    1. Créez un superutilisateur : python manage_simple.py createsuperuser
echo    2. Récupérez des films : python manage_simple.py fetch_movies
echo.
echo 🔄 Démarrage du serveur Django...
echo.

python manage_simple.py runserver

pause
