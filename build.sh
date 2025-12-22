#!/usr/bin/env bash
# Sair se houver erro
set -o errexit

# Instalar dependências
pip install -r requirements.txt

# Coletar arquivos estáticos
python manage.py collectstatic --no-input

# Aplicar migrações no banco de dados
python manage.py migrate

# Criar superusuário
python create_superuser.py