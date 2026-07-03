#!/bin/bash
# ============================================================
# PathAR — Setup en Ubuntu 24.04
# Ejecutar como: bash setup.sh
# ============================================================

set -e  # Detener si hay error

echo "▶ Actualizando paquetes..."
sudo apt update && sudo apt upgrade -y

echo "▶ Instalando Python 3.12 y PostgreSQL..."
sudo apt install -y python3.12 python3.12-venv python3-pip postgresql postgresql-contrib

echo "▶ Iniciando PostgreSQL..."
sudo systemctl start postgresql
sudo systemctl enable postgresql

echo "▶ Creando base de datos y usuario..."
sudo -u postgres psql <<EOF
CREATE USER pathar_user WITH PASSWORD 'pathar_password';
CREATE DATABASE pathar_db OWNER pathar_user;
GRANT ALL PRIVILEGES ON DATABASE pathar_db TO pathar_user;
EOF

echo "▶ Creando entorno virtual..."
python3.12 -m venv .venv
source .venv/bin/activate

echo "▶ Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt
pip install pydantic-settings  # necesario para config.py

echo ""
echo "✅ Setup completo."
echo ""
echo "Pasos siguientes:"
echo "  1. Copiá .env.example a .env y completá los valores"
echo "  2. Activá el entorno:  source .venv/bin/activate"
echo "  3. Corré el servidor:  uvicorn app.main:app --reload"
echo "  4. Documentación:      http://localhost:8000/docs"
