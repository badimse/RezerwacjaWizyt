from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required 
from django.contrib import messages
from .models import Service, Staff, Appointment, Attendance
from .forms import AppointmentForm, ServiceForm
from django.db.models import Count
from django.utils import timezone
import datetime
import json
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.db.models import Sum

# 1. Strona główna
def index(request):
    services = Service.objects.all()
    user_appointments = []
    
    if request.user.is_authenticated:
        user_appointments = Appointment.objects.filter(client=request.user).order_by('date', 'time')
    
    context = {
        'services': services,
        'user_appointments': user_appointments,
    }
    return render(request, 'bookings/index.html', context)

# 2. Rejestracja
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Konto zostało utworzone pomyślnie!")
            return redirect('index')
    return redirect('index')

# 3. Logowanie
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Witaj ponownie, {user.username}!")
            return redirect('index')
    return redirect('index')

# 4. Wylogowanie
def logout_view(request):
    logout(request)
    messages.info(request, "Zostałeś wylogowany.")
    return redirect('index')

# 5. Rezerwacja wizyty
@login_required 
def book_appointment(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.client = request.user
            appointment.service = service
            # Automatyczne nadawanie statusu "Oczekująca" i źródła "Online"
            appointment.status = 'PENDING'
            appointment.source = 'ONLINE'
            appointment.save()
            messages.success(request, f"Zarezerwowano termin na usługę: {service.name}")
            return redirect('index')
    else:
        form = AppointmentForm()
        
    return render(request, 'bookings/book.html', {'form': form, 'service': service})

# 6. Odwołanie wizyty
@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, client=request.user)
    # Zamiast usuwać wizytę całkowicie z bazy, zmieniamy jej status na "CANCELED"
    appointment.status = 'CANCELED'
    appointment.save()
    messages.info(request, "Wizyta została odwołana.")
    return redirect('index')

# 7. Wyciągnięcie danych z kalendarza dla użytkownika
def get_appointments_by_date(request):
    selected_date = request.GET.get('date')
    appointments = Appointment.objects.filter(date=selected_date).order_by('time')
    
    data = []
    for app in appointments:
        data.append({
            'time': app.time.strftime('%H:%M'),
            'service_name': app.service.name,
            'client': app.client.username if hasattr(app, 'client') else "Brak danych"
        })
        
    return JsonResponse(data, safe=False)

# 8. Ustawienia kalendarza rezerwacji dla użytkownika
def api_wizyty_dnia(request, data_str):
    try:
        # Pobieramy wizyty dla konkretnego dnia, ignorując te odwołane
        wizyty = Appointment.objects.filter(date=data_str).exclude(status='CANCELED').order_by('time')
        
        lista_wizyt = []
        for w in wizyty:
            klient_nazwa = w.client.username if w.client else "Brak danych"
            godzina_str = w.time.strftime('%H:%M') if w.time else "00:00"
            
            lista_wizyt.append({
                'godzina': godzina_str,
                'usluga': w.service.name,
                'klient': klient_nazwa
            })
            
        return JsonResponse(lista_wizyt, safe=False)
        
    except Exception as e:
        print(f"BŁĄD W API WIZYT: {e}")
        return JsonResponse({'error': str(e)}, status=500)
    
# 9. Ustawienia Panelu Admina 
@staff_member_required
def custom_dashboard(request):
    # 1. Określamy ramy czasowe do statystyk
    today = timezone.now().date()
    first_day_of_month = today.replace(day=1) 
    
    # 2. Pobieramy wizyty oczekujące
    pending_appointments = Appointment.objects.filter(status='PENDING').order_by('date', 'time')
    
    # 3. Pobieramy dzisiejszy grafik
    today_appointments = Appointment.objects.filter(date=today).exclude(status='CANCELED').order_by('time')
    
    # 4. STATYSTYKI FINANSOWE
    today_revenue = sum(app.service.price for app in today_appointments)
    month_completed = Appointment.objects.filter(date__gte=first_day_of_month, status='COMPLETED')
    month_revenue = sum(app.service.price for app in month_completed)
    
    # 5. DANE DO WYKRESU
    services_data = Appointment.objects.filter(date__gte=first_day_of_month).values('service__name').annotate(count=Count('id'))
    chart_labels = [item['service__name'] for item in services_data]
    chart_data = [item['count'] for item in services_data]

    # 6. POBIERANIE DANYCH DO MODALI I LIST
    all_services = Service.objects.all()
    all_staff = Staff.objects.all()
    users_list = User.objects.exclude(id=request.user.id).order_by('-is_staff', 'username')

    # Liczymy sumy dla każdej metody płatności (tylko dla wizyt ZAKOŃCZONYCH)
    payment_stats = Appointment.objects.filter(status='COMPLETED').values('payment_method').annotate(total=Sum('service__price'))

    # Przygotowujemy dane do wykresu
    pay_labels = []
    pay_data = []

    # Mapowanie kodów na ładne nazwy
    pay_map = dict(Appointment.PAYMENT_METHODS)

    for stat in payment_stats:
        method_name = pay_map.get(stat['payment_method'], "Nieokreślona")
        pay_labels.append(method_name)
        pay_data.append(float(stat['total'] or 0))

    # --- LOGIKA OBECNOŚCI ---
    # Automatycznie twórz wpis obecności dla każdego pracownika na dziś, jeśli jeszcze nie istnieje
    for staff_member in all_staff:
        Attendance.objects.get_or_create(staff=staff_member, date=today)
    
    # Pobierz dzisiejszą listę obecności, aby wysłać ją do HTML
    todays_attendance = Attendance.objects.filter(date=today).select_related('staff')
    
    # --- PODSUMOWANIE MIESIĄCA ---
    staff_settlement = []
    for staff_member in all_staff:
        # Liczymy ile razy pracownik był obecny od 1-go dnia tego miesiąca
        days_worked = Attendance.objects.filter(
            staff=staff_member, 
            date__gte=first_day_of_month, 
            is_present=True
        ).count()
        
        staff_settlement.append({
            'full_name': f"{staff_member.first_name} {staff_member.last_name}",
            'days_worked': days_worked
        })
    # ------------------------------------
    # Pobieramy statystyki płatności z bazy
    payment_stats_query = Appointment.objects.filter(status='COMPLETED').values('payment_method').annotate(total=Sum('service__price'))

    # Przygotowujemy listy pod wykres
    pay_labels_raw = []
    pay_data_raw = []
    payment_stats_summary = [] # To jest ta zmienna, której szukał błąd!

    # Mapowanie kodów na ładne nazwy (żeby w tabelce nie było "CASH" tylko "Gotówka")
    pay_map = dict(Appointment.PAYMENT_METHODS)

    for stat in payment_stats_query:
        method_name = pay_map.get(stat['payment_method'], "Nieokreślona")
        kwota = float(stat['total'] or 0)
        
        pay_labels_raw.append(method_name)
        pay_data_raw.append(kwota)
        payment_stats_summary.append({'method': method_name, 'total': kwota})

    context = {
        # Podstawowe listy wizyt
        'pending_appointments': pending_appointments,
        'today_appointments': today_appointments,
        
        # Finanse (liczby)
        'today_revenue': today_revenue,
        'month_revenue': month_revenue,
        
        # Dane do wykresu USŁUG (JSON)
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        
        # Dane do wykresu PŁATNOŚCI (JSON) - NOWOŚĆ
        'pay_labels': json.dumps(pay_labels),
        'pay_data': json.dumps(pay_data),
        'payment_stats_summary': payment_stats_summary,
        
        # Listy pomocnicze
        'all_services': all_services,
        'all_staff': all_staff,
        'users_list': users_list,
        
        # Obecność i rozliczenia pracowników
        'todays_attendance': todays_attendance, 
        'staff_settlement': staff_settlement,

        # Pusty formularz dodania usługi
        'service_form': ServiceForm(),
    }
    
    return render(request, 'bookings/dashboard.html', context)
    
    # Zmień status wizyty 
@staff_member_required
def update_status(request, appointment_id, new_status):
    app = get_object_or_404(Appointment, id=appointment_id)
    app.status = new_status
    
    # Odczytujemy metodę płatności z adresu URL (?method=...)
    payment_method = request.GET.get('method')
    if new_status == 'COMPLETED' and payment_method:
        app.payment_method = payment_method # Upewnij się, że masz to pole w modelu!
        
    app.save()
    messages.success(request, f"Wizyta zakończona. Płatność: {app.get_payment_method_display() if app.payment_method else 'Brak'}")
    return redirect('dashboard')

    # Mała notatka o kliencie
@staff_member_required
def update_notes(request, appointment_id):
    if request.method == 'POST':
        appointment = get_object_or_404(Appointment, id=appointment_id)
        # Pobieramy wpisany tekst (jeśli pusto, zapisuje się pusty string)
        appointment.internal_notes = request.POST.get('notes', '')
        appointment.save()
        messages.success(request, f"Zapisano notatkę dla klienta: {appointment.client.username}.")
    return redirect('dashboard')

    # Funkcja przełączająca status
@staff_member_required
def toggle_staff_status(request, user_id):
    target_user = get_object_or_404(User, id=user_id)
    
    # Zabezpieczenie: Nie pozwalamy ruszać Głównego Administratora (Superusera)
    if target_user.is_superuser:
        messages.error(request, "Nie możesz zmienić uprawnień Głównego Administratora systemu!")
    else:
        # Odwracamy status: Jeśli był True, staje się False. Jeśli False, staje się True.
        target_user.is_staff = not target_user.is_staff
        target_user.save()
        
        rola = "Pracownik (Dostęp do panelu)" if target_user.is_staff else "Zwykły Klient"
        messages.success(request, f"Zmieniono uprawnienia użytkownika {target_user.username} na: {rola}.")
        
    return redirect('dashboard')

# --- FUNKCJA DO SZYBKIEJ REZERWACJI Z TELEFONU ---
@staff_member_required
def quick_book(request):
    if request.method == 'POST':
        service_id = request.POST.get('service')
        staff_id = request.POST.get('staff') # <--- Pobieramy pracownika
        date = request.POST.get('date')
        time = request.POST.get('time')
        client_name = request.POST.get('client_name')

        service = get_object_or_404(Service, id=service_id)
        staff_member = get_object_or_404(Staff, id=staff_id) # <--- Szukamy go w bazie

        Appointment.objects.create(
            client=request.user, 
            service=service,
            staff=staff_member, # <--- Przypisujemy do wizyty (ROZWIĄZUJE BŁĄD BAZY!)
            date=date,
            time=time,
            status='CONFIRMED', 
            internal_notes=f"📞 REZERWACJA TELEFONICZNA: {client_name}"
        )
        messages.success(request, f"Dodano szybką wizytę dla: {client_name}")
        
    return redirect('dashboard')

# --- Funkcja kalenarza w panelu Admina --- 
@staff_member_required
def api_admin_events(request):
    # Pobieramy wszystkie wizyty omijając tylko te odwołane
    appointments = Appointment.objects.exclude(status='CANCELED')
    
    events = []
    for app in appointments:
        # Określamy kolor w zależności od statusu
        color = '#ff9800' # PENDING (Oczekująca)
        if app.status == 'CONFIRMED': color = '#2196f3'
        if app.status == 'COMPLETED': color = '#4caf50'
        if app.status == 'NOSHOW': color = '#6b7280'
        
        # Poprawne formatowanie czasu w Pythonie
        time_str = app.time.strftime('%H:%M')
        full_time_str = app.time.strftime('%H:%M:%S')
        
        events.append({
            'id': app.id,
            'title': f"{time_str} - {app.client.username} ({app.service.name})",
            'start': f"{app.date}T{full_time_str}",
            'color': color,
            'extendedProps': {
                'service': app.service.name,
                'client': app.client.username,
                'status': app.get_status_display()
            }
        })
    return JsonResponse(events, safe=False)

# --- FUNKCJA PRZEŁĄCZANIA OBECNOŚCI PRACOWNIKA ---
@staff_member_required
def toggle_attendance(request, attendance_id):
    # Pobieramy konkretny wpis obecności
    attendance = get_object_or_404(Attendance, id=attendance_id)
    
    # Odwracamy status (z True na False lub odwrotnie)
    attendance.is_present = not attendance.is_present
    attendance.save()
    
    stan = "obecny(a)" if attendance.is_present else "nieobecny(a)"
    messages.success(request, f"Zmieniono status: {attendance.staff.name} jest teraz {stan}.")
    
    return redirect('dashboard')

# -- Funkcja Szczegółow użytkownika
@staff_member_required
def api_user_details(request, user_id):
    # Szukamy klienta w bazie
    user = get_object_or_404(User, id=user_id)
    
    # Pobieramy wszystkie jego wizyty (od najnowszych)
    appointments = Appointment.objects.filter(client=user).order_by('-date', '-time')
    
    # Przygotowujemy listę historii
    history = []
    for app in appointments:
        history.append({
            'date': app.date.strftime('%d.%m.%Y'),
            'time': app.time.strftime('%H:%M'),
            'service': app.service.name,
            'status': app.get_status_display(),
            'status_code': app.status,
            'staff': app.staff.name
        })
        
    # Zliczamy statystyki tego klienta
    stats = {
        'total': appointments.count(),
        'completed': appointments.filter(status='COMPLETED').count(),
        'canceled': appointments.filter(status='CANCELED').count(),
        'noshow': appointments.filter(status='NOSHOW').count(),
    }
    
    # Wysyłamy paczkę danych z powrotem do przeglądarki
    data = {
        'id': user.id,
        'is_active': user.is_active,
        'username': user.username,
        'date_joined': user.date_joined.strftime('%d.%m.%Y'),
        'stats': stats,
        'history': history
    }
    return JsonResponse(data)

# --- ZARZĄDZANIE UŻYTKOWNIKAMI ---

@staff_member_required
def toggle_block_user(request, user_id):
    u = get_object_or_404(User, id=user_id)
    if u.is_superuser:
        messages.error(request, "Nie możesz zablokować głównego administratora!")
    else:
        u.is_active = not u.is_active
        u.save()
        stan = "zablokowany" if not u.is_active else "odblokowany"
        messages.success(request, f"Użytkownik {u.username} został {stan}.")
    return redirect('dashboard')

@staff_member_required
def delete_user(request, user_id):
    u = get_object_or_404(User, id=user_id)
    if u.is_superuser:
        messages.error(request, "Nie możesz usunąć głównego administratora!")
    else:
        username = u.username
        u.delete()
        messages.success(request, f"Użytkownik {username} został trwale usunięty.")
    return redirect('dashboard')

from django.contrib.auth import login
from django.contrib.auth.models import User

def login_demo(request, role):
    # Wybieramy użytkownika na podstawie roli
    username = 'demo_admin' if role == 'admin' else 'demo_user'
    
    try:
        user = User.objects.get(username=username)
        login(request, user)
        if user.is_staff:
            return redirect('dashboard')
        return redirect('index')
    except User.DoesNotExist:
        from django.contrib import messages
        messages.error(request, f"Konto {username} nie istnieje. Stwórz je w panelu /admin!")
        return redirect('index')
    
    # --- ZARZĄDZANIE USŁUGAMI ---

@staff_member_required
def add_service(request):
    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Nowa usługa została pomyślnie dodana!")
        else:
            messages.error(request, "Błąd podczas dodawania usługi. Sprawdź wprowadzane dane.")
    return redirect('dashboard')

@staff_member_required
def edit_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    
    if request.method == 'POST':
        form = ServiceForm(request.POST, instance=service)
        if form.is_valid():
            form.save()
            messages.success(request, f"Zaktualizowano usługę: {service.name}")
            return redirect('dashboard')
    else:
        form = ServiceForm(instance=service)
        
    return render(request, 'bookings/edit_service.html', {'form': form, 'service': service})

@staff_member_required
def delete_service(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    service_name = service.name
    service.delete()
    messages.success(request, f"Usługa '{service_name}' została usunięta.")
    return redirect('dashboard')