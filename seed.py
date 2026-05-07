import random
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from bookings.models import Staff, Service, Appointment, Attendance

print("Rozpoczynam generowanie danych...")

now = timezone.now()
today = now.date()

# 1. DODAWANIE USŁUG
services_data = [
    ("Manicure hybrydowy (PRO)", "Pełna stylizacja paznokci", 150.00, 60, "fa-hand-sparkles"),
    ("Masaż gorącymi kamieniami", "Głęboki relaks", 250.00, 90, "fa-spa"),
    ("Oczyszczanie wodorowe twarzy", "Zabieg na twarz", 200.00, 45, "fa-gem"),
    ("Strzyżenie damskie + Modelowanie", "Kompletna stylizacja", 180.00, 60, "fa-cut"),
    ("Zabieg kwasami AHA", "Złuszczanie naskórka", 130.00, 30, "fa-flask")
]
services = []
for name, desc, price, dur, icon in services_data:
    s, _ = Service.objects.get_or_create(name=name, defaults={"description": desc, "price": price, "duration_minutes": dur, "icon_class": icon})
    services.append(s)

# 2. DODAWANIE PRACOWNIKÓW
staff_data = [("Anna", "Mistrz", "Kosmetolog"), ("Piotr", "Zwinny", "Masażysta"), ("Kasia", "Nożyczka", "Fryzjer")]
staff_members = []
for fn, ln, spec in staff_data:
    st, _ = Staff.objects.get_or_create(first_name=fn, last_name=ln, defaults={"specialization": spec})
    staff_members.append(st)

# 3. DODAWANIE KLIENTÓW (15 sztuk)
clients = []
for i in range(1, 16):
    user, created = User.objects.get_or_create(username=f"klientka_{i}")
    if created:
        user.set_password("haslo123")
        user.save()
    clients.append(user)

# 4. GENEROWANIE 150 WIZYT (Ostatnie 60 dni)
statuses = ['COMPLETED', 'COMPLETED', 'COMPLETED', 'COMPLETED', 'CANCELED', 'NOSHOW'] # Większość zakończona sukcesem
sources = ['ONLINE', 'PHONE', 'WALKIN']

created_apps = 0
for _ in range(150):
    client = random.choice(clients)
    staff = random.choice(staff_members)
    service = random.choice(services)

    # Losowy dzień w przeszłości (od 0 do 60 dni wstecz)
    days_ago = random.randint(0, 60)
    app_date = today - timedelta(days=days_ago)

    # Losowa godzina (9:00 - 17:00) co 15 minut
    hour = random.randint(9, 17)
    minute = random.choice([0, 15, 30, 45])
    app_time = timezone.datetime(2000, 1, 1, hour, minute).time()

    # Logika statusu (jeśli wizyta jest dzisiaj to oczekująca/potwierdzona, w przeszłości zakończona/odwołana)
    if days_ago == 0:
        status = random.choice(['PENDING', 'PENDING', 'CONFIRMED'])
    else:
        status = random.choice(statuses)

    try:
        Appointment.objects.create(
            client=client,
            staff=staff,
            service=service,
            date=app_date,
            time=app_time,
            status=status,
            source=random.choice(sources),
            internal_notes=f"Testowa wizyta. Wygenerowana skryptem {days_ago} dni temu."
        )
        created_apps += 1
    except Exception:
        pass # Ignorujemy kolizje (jeśli wylosuje się ten sam pracownik na tę samą godzinę)

# 5. GENEROWANIE OBECNOŚCI DLA PRACOWNIKÓW (Ostatnie 30 dni)
for i in range(31):
    att_date = today - timedelta(days=i)
    if att_date.weekday() == 6: # Pomijamy niedziele
        continue

    for staff in staff_members:
        # 85% szans, że pracownik był w pracy
        is_present = random.random() < 0.85
        Attendance.objects.get_or_create(staff=staff, date=att_date, defaults={"is_present": is_present})

print(f"Sukces! Wygenerowano: {len(services)} usług, {len(staff_members)} pracowników, {len(clients)} klientów i {created_apps} wizyt!")