import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ambulance_system.settings')
django.setup()

from accounts.models import CustomUser

email = 'admin@cadts.com'
password = 'Admin@123'

if not CustomUser.objects.filter(email=email).exists():
    CustomUser.objects.create_superuser(
        email=email, 
        password=password, 
        first_name='System', 
        last_name='Admin'
    )
    print(f"Superuser {email} created successfully.")
else:
    print(f"Superuser {email} already exists.")
