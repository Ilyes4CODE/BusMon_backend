@echo off
title Bus Monitoring System
color 0A
cls

echo.
echo  ============================================
echo   BUS MONITORING SYSTEM - Backend
echo  ============================================
echo.

REM ── Go to script's own directory ─────────────────────────────
cd /d "%~dp0"
echo  [INFO] Working directory: %CD%
echo.

REM ── Check Python ─────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Python not found. Install from https://python.org
    pause
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do echo  [OK] %%i

REM ── First run check ──────────────────────────────────────────
if exist ".initialized" (
    echo  [INFO] Already initialized - starting server directly...
    goto :ACTIVATE
)

echo.
echo  [SETUP] First run detected - full setup starting...
echo  ============================================

REM ── Create venv ──────────────────────────────────────────────
echo.
echo  [1/5] Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    if errorlevel 1 ( echo  [ERROR] Failed to create venv & pause & exit /b 1 )
)
echo  [OK] Virtual environment ready.

REM ── Activate venv ────────────────────────────────────────────
:ACTIVATE
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo  [ERROR] Cannot activate virtual environment.
    pause
    exit /b 1
)
echo  [OK] Virtual environment activated.

REM ── Install dependencies (first run only) ────────────────────
if not exist ".initialized" (
    echo.
    echo  [2/5] Installing dependencies...
    pip install --upgrade pip --quiet
    pip install -r requirements.txt --quiet
    if errorlevel 1 ( echo  [ERROR] pip install failed & pause & exit /b 1 )
    echo  [OK] Dependencies installed.
)

REM ── Migrations (first run only) ──────────────────────────────
if not exist ".initialized" (
    echo.
    echo  [3/5] Running migrations...
    python manage.py makemigrations accounts --no-input
    python manage.py makemigrations buses --no-input
    python manage.py makemigrations routes --no-input
    python manage.py makemigrations drivers --no-input
    python manage.py makemigrations maintenance --no-input
    python manage.py makemigrations notifications --no-input
    python manage.py makemigrations ratings --no-input
    python manage.py migrate --no-input
    if errorlevel 1 ( echo  [ERROR] Migration failed & pause & exit /b 1 )
    echo  [OK] Database ready.
)

REM ── Seed data (first run only) ───────────────────────────────
if not exist ".initialized" (
    echo.
    echo  [4/5] Creating initial data...
    python manage.py shell -c "
from apps.accounts.models import User
from apps.buses.models import Bus
from apps.routes.models import Route, Stop
from apps.drivers.models import DriverProfile

if not User.objects.filter(email='admin@busapp.dz').exists():
    User.objects.create_superuser(username='admin', email='admin@busapp.dz', password='Admin@1234', first_name='Super', last_name='Admin', role='admin')
    print('  Admin created: admin@busapp.dz / Admin@1234')

if not User.objects.filter(email='driver1@busapp.dz').exists():
    d = User.objects.create_user(username='driver1', email='driver1@busapp.dz', password='Driver@1234', first_name='Ahmed', last_name='Benali', role='driver', phone='0550000001')
    DriverProfile.objects.create(user=d, license_number='DZ-2020-001', license_expiry='2027-12-31', experience_years=5, is_available=True)
    print('  Driver created: driver1@busapp.dz / Driver@1234')

if not User.objects.filter(email='user1@busapp.dz').exists():
    User.objects.create_user(username='user1', email='user1@busapp.dz', password='User@1234', first_name='Karim', last_name='Meziane', role='user')
    print('  User created: user1@busapp.dz / User@1234')

buses = [
    ('16-001-DZ','Mercedes','Citaro',80,2020,'stopped',36.7538,3.0588),
    ('16-002-DZ','Volvo','B8R',60,2019,'moving',36.7600,3.0650),
    ('16-003-DZ','MAN','Lion City',70,2021,'maintenance',36.7450,3.0500),
]
for plate,brand,model,cap,year,status,lat,lng in buses:
    if not Bus.objects.filter(plate_number=plate).exists():
        Bus.objects.create(plate_number=plate,brand=brand,model=model,capacity=cap,year=year,status=status,latitude=lat,longitude=lng)
        print(f'  Bus created: {plate}')

if not Route.objects.filter(name='Ligne 01').exists():
    r = Route.objects.create(name='Ligne 01',origin='Place des Martyrs',destination='Aeroport H.B.',distance_km=28.5,duration_min=55,is_active=True)
    for name,order,lat,lng in [('Place des Martyrs',1,36.7762,3.0590),('Grande Poste',2,36.7693,3.0568),('Universite USTHB',3,36.7315,3.1612),('Aeroport H.B.',4,36.6910,3.2154)]:
        Stop.objects.create(route=r,name=name,order=order,lat=lat,lng=lng)
    print('  Route Ligne 01 created')
"
    echo  [OK] Initial data ready.
)

REM ── Collect static (first run only) ──────────────────────────
if not exist ".initialized" (
    echo.
    echo  [5/5] Collecting static files...
    python manage.py collectstatic --no-input --quiet
    echo  [OK] Static files ready.
    echo. > .initialized
    echo  [OK] Setup complete!
)

REM ── Detect local IP ──────────────────────────────────────────
echo.
echo  [INFO] Detecting local IP...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /R /C:"IPv4"') do (
    for /f "tokens=1" %%b in ("%%a") do (
        set LOCAL_IP=%%b
        goto :GOTIP
    )
)
:GOTIP
set LOCAL_IP=%LOCAL_IP: =%
echo  [OK] Local IP: %LOCAL_IP%

REM ── Write Flutter config ──────────────────────────────────────
if not exist "staticfiles" mkdir staticfiles
echo {"api_url": "http://%LOCAL_IP%:8000/api/", "ws_url": "ws://%LOCAL_IP%:8000/ws/", "server_ip": "%LOCAL_IP%", "port": 8000} > staticfiles\config.json
echo  [OK] Flutter config written.

REM ── Launch server ─────────────────────────────────────────────
echo.
echo  ============================================
echo   SERVER STARTING...
echo  ============================================
echo.
echo   API:       http://%LOCAL_IP%:8000/api/
echo   Admin:     http://%LOCAL_IP%:8000/admin/
echo   WebSocket: ws://%LOCAL_IP%:8000/ws/buses/
echo   Config:    http://%LOCAL_IP%:8000/api/config/
echo.
echo   Accounts:
echo     Admin  - admin@busapp.dz   / Admin@1234
echo     Driver - driver1@busapp.dz / Driver@1234
echo     User   - user1@busapp.dz   / User@1234
echo.
echo   Press CTRL+C to stop.
echo  ============================================
echo.

REM Open browser after 2 seconds
start "" timeout /t 2 /nobreak >nul && start http://%LOCAL_IP%:8000/admin/

daphne -b 0.0.0.0 -p 8000 config.asgi:application

echo.
echo  [INFO] Server stopped.
pause
