# CADTS — Centralized Ambulance Dispatch & Tracking System

CADTS (Centralized Ambulance Dispatch & Tracking System) is a modern, real-time web application designed to bridge the gap between citizens, drivers, and administrators during medical emergencies. The system supports real-time ambulance tracking via WebSockets, automatic billing calculations (in both kilometers and meters), nearest hospital locating using OpenStreetMap, and complete system management via an administrative dashboard.

---

## 🚀 Key Features

* **Real-Time Live Tracking:** High-frequency, bidirectional real-time GPS tracking for users tracking their dispatched ambulance and drivers updating their locations.
* **Dual-Unit Dynamic Billing:** Automatically calculates distance using the Haversine formula on the backend. Displays distance in both kilometers (km) and meters (m) depending on the range (e.g. `< 1km` displays purely in meters).
* **OSM Hospital Locating:** Scans and lists nearby hospitals, clinics, dispensaries, pharmacies, and health centers using the OpenStreetMap Overpass API, sorted by distance.
* **Mobile-Responsive UI:** Fully responsive design with floating mobile-native layouts, sidebar menus, and touch-optimized maps (disabled map dragging on touchscreens to ensure smooth vertical page scrolling).
* **Authentication & Account Management:** Full registration and sign-in flow for both Citizens and Drivers, alongside a secure **Forgot Password / Account Recovery** system.

---

## 💻 System Requirements

To run this application locally, ensure your computer meets the following requirements:

### Prerequisites

* **Operating System:** Windows, macOS, or Linux.
* **Python:** Version `3.10` or higher.
* **Database:** MySQL Server version `8.0` or higher.
* **Web Browser:** Modern browser (Chrome, Safari, Firefox, Edge) with Geolocation permissions enabled.

### Backend Python Packages (Specified in `requirements.txt`)

* `Django==6.0.6` (Core Web Framework)
* `djangorestframework==3.17.1` & `djangorestframework-simplejwt==5.5.1` (REST API & Token Auth)
* `mysqlclient==2.2.8` & `mysql-connector-python` (MySQL Database Drivers)
* `channels==4.3.2` & `daphne==4.2.2` (ASGI & WebSockets Framework)
* `django-cors-headers==4.9.0` (Cross-Origin Resource Sharing)

---

## 🛠️ Local Installation & Setup

Follow these steps to set up the system on your machine:

### 1. Set Up Virtual Environment & Dependencies

Open PowerShell or your preferred terminal inside the project directory (`C:\Users\SHEDRACK\OneDrive\Desktop\CADTS`) and run:

```powershell
# Create virtual environment if not already present
python -m venv venv

# Activate virtual environment
.\venv\Scripts\Activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure the MySQL Database

1. Open your MySQL client (Command Line, Workbench, or phpMyAdmin) and create a database named `cadts_db`:

   ```sql

   CREATE DATABASE cadts_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

2. Double check your settings in `ambulance_system/settings.py` under `DATABASES`. Ensure the `USER`

and `PASSWORD` match your local MySQL configuration:

   ```python
   DATABASES = {
       "default": {
           "ENGINE": "django.db.backends.mysql",
           "NAME": "cadts_db",
           "USER": "root",
           "PASSWORD": "Shedy@123",  # <-- Change this to your local MySQL password
           "HOST": "localhost",
           "PORT": "3306",
           ...
       }
   }
   ```

### 3. Run Database Migrations

Run the migrations to create the database tables:

```powershell
python manage.py migrate
```

### 4. Default Credentials (Superuser)

You can access the admin panel (`/admin/` or dashboard admin panel) using the following credentials:

* **Username / Email:** `admin@cadts.com`

* **Password:** `Admin@123`

---

## 🚦 Running the System

### Standard Local Execution

To run the server locally on your PC:

```powershell
python manage.py runserver 0.0.0.0:8000

```

Open **`http://127.0.0.1:8000/`** in your browser.

---

## 📱 Testing Across Different Networks (Using ngrok)

Modern browsers restrict Geolocation (GPS) APIs to secure environments (`localhost` or `https`). To test the live tracking on your phone while your PC runs the server:

1. Download **ngrok** from [ngrok.com](https://ngrok.com/download) and place `ngrok.exe` in your project folder.
2. Sign up for a free ngrok account and copy your Authtoken.
3. Authenticate ngrok in terminal:

   ```powershell

   .\ngrok.exe config add-authtoken <YOUR_TOKEN>

   ```

4. Start your Django server:

   ```powershell
   python manage.py runserver 0.0.0.0:8000

   ```

5. In another terminal window, start the ngrok tunnel:

   ```powershell
   .\ngrok.exe http 8000

   ```

6. Copy the secure **`https://...`** URL from the ngrok output.
7. Open that `https://` link on your phone. Because it uses HTTPS, your phone's browser will allow GPS access and map tracking will work flawlessly!
