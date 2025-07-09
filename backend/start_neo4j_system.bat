@echo off
echo 🚀 Starting Neo4j Movie Recommendation System
echo =============================================

echo.
echo 📦 Installing dependencies...
pip install -r requirements.txt

echo.
echo 🔧 Setting up Django...
python manage.py makemigrations
python manage.py migrate

echo.
echo 📊 Migrating data to Neo4j...
python migrate_to_neo4j.py

echo.
echo 🧪 Testing Neo4j system...
python test_neo4j_system.py

echo.
echo 🌟 Starting Django server...
python manage.py runserver

pause
