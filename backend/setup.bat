@echo off
cls
echo 🎬 Configuration du système de recommandation de films Django
echo ============================================================
echo.

REM Vérification de Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python n'est pas installé. Veuillez installer Python 3.8+
    pause
    exit /b 1
)

echo ✅ Python détecté

REM Installation des dépendances
echo 📦 Installation des dépendances...
pip install -r requirements_simple.txt

REM Configuration de l'environnement
if not exist .env (
    echo 📝 Création du fichier .env...
    copy .env.example .env
    echo ⚠️  Veuillez configurer vos clés API dans le fichier .env
)

REM Migration de la base de données
echo 🗄️  Configuration de la base de données...
python manage.py makemigrations
python manage.py migrate

REM Création du superutilisateur
echo 👤 Création du superutilisateur...
echo Veuillez entrer les informations pour le compte administrateur :
python manage.py createsuperuser

REM Collecte des fichiers statiques
echo 📂 Collecte des fichiers statiques...
python manage.py collectstatic --noinput

echo.
echo 🎉 Installation terminée !
echo.
echo 🚀 Pour démarrer le serveur :
echo    python manage.py runserver
echo.
echo 📊 Pour récupérer des films depuis TMDb :
echo    python manage.py fetch_movies
echo.
echo 🔗 Accès à l'application :
echo    - Site web : http://127.0.0.1:8000
echo    - Administration : http://127.0.0.1:8000/admin
echo.
echo 📋 N'oubliez pas de :
echo    1. Configurer votre clé API TMDb dans .env
echo    2. Configurer MongoDB si nécessaire
echo    3. Lancer 'python manage.py fetch_movies' pour récupérer des films
echo.
pause
