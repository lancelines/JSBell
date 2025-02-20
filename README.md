# Inventory Management System

A comprehensive inventory management system built with Django and Tailwind CSS.

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- Node.js and npm (for Tailwind CSS)

## Installation

2. Create a virtual environment and activate it:
```bash
python -m venv venv
# On Windows
venv\Scripts\activate
# On macOS/Linux
source venv/bin/activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
# or(if command above doesn't work)
pip install Django>=4.2.0
pip install django-tailwind>=3.6.0
pip install pillow>=10.0.0
pip install django-crispy-forms>=2.0
pip install crispy-tailwind>=0.5.0
pip install python-dotenv>=1.0.0
pip install django-browser-reload>=1.11.0
pip install django-htmx>=1.17.0
pip install django-filter>=23.3
pip install django-widget-tweaks>=1.5.0
pip install gunicorn>=21.2.0
pip install whitenoise>=6.5.0
pip install dj-database-url>=2.1.0
pip install django-model-utils>=4.3.1
pip install reportlab>=4.1.0

pip install psycopg2-binary>=2.9.9
#or (if pip install psycopg2-binary>=2.9.9 doesn't work)
pip install psycopg[binary]>3
```

4. Install Tailwind CSS dependencies:
```bash
cd tailwind_django
python manage.py tailwind install
```

5. Create necessary directories:
```bash
python create_media_dir.py
```

6. Apply database migrations:
```bash
python manage.py migrate
```

7. Create a superuser (admin):
```bash
python manage.py createsuperuser
```

## Running the Development Server

1. Start the Tailwind CSS build process:
```bash
python manage.py tailwind start
```

2. In a new terminal, run the Django development server:
```bash
python manage.py runserver
```

3. Access the application at: http://127.0.0.1:8000

## Features

- User Authentication and Authorization
- Inventory Management
- Purchase Management
- Requisition System
- Responsive Design with Tailwind CSS

## Project Structure

- `account/`: User authentication and profile management
- `inventory/`: Core inventory management functionality
- `purchasing/`: Purchase order and supplier management
- `requisition/`: Requisition system
- `theme/`: Tailwind CSS configuration and styling

## Development

- To make changes to the styling, edit the files in the `theme/static_src/src/input.css` file
- The project uses Django's template system with Tailwind CSS for styling
- Static files are automatically collected when deploying

## License

This project is licensed under the MIT License - see the LICENSE file for details
