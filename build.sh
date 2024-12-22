#!/usr/bin/env bash
# exit on error
set -o errexit

# Install python dependencies
pip install -r requirements.txt

# Create media directory
python tailwind_django/create_media_dir.py

# Collect static files
python tailwind_django/manage.py collectstatic --no-input

# Run migrations
python tailwind_django/manage.py migrate
