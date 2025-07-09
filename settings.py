DATABASES = {
    'default': {
        'ENGINE': 'djongo',
        'CLIENT': {
            'host': 'mongodb+srv://yasskoch35:8QtskpuwQp5yOuGI@movierecommand.orxc1nl.mongodb.net/?retryWrites=true&w=majority&appName=movierecommand',
            'name': 'movierecommand',  # Remplace par le nom de ta base de données
            'authMechanism': 'SCRAM-SHA-1',
            
        }
    }
}

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'movies',  # Ajoute cette ligne pour ton application movies
]

