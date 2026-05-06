from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required 
from django.contrib import messages
from .models import Service, Staff, Appointment 
from .forms import AppointmentForm
from django.db.models import Count
from django.utils import timezone
import datetime
import json

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
    first_day_of_month = today.replace(day=1) # Ustawia pierwszy dzień obecnego miesiąca
    
    # 2. Pobieramy wizyty oczekujące (ze statusem PENDING)
    pending_appointments = Appointment.objects.filter(status='PENDING').order_by('date', 'time')
    
    # 3. Pobieramy dzisiejszy grafik (omijamy tylko te odwołane statusem CANCELED)
    today_appointments = Appointment.objects.filter(date=today).exclude(status='CANCELED').order_by('time')
    
    # 4. STATYSTYKI FINANSOWE (Obliczanie przychodów z cen usług)
    # Dzisiejszy utarg to suma cen usług przypisanych do dzisiejszych wizyt
    today_revenue = sum(app.service.price for app in today_appointments)
    
    # Miesięczny utarg liczymy tylko dla wizyt ZAKOŃCZONYCH (COMPLETED) od pierwszego dnia miesiąca
    month_completed = Appointment.objects.filter(date__gte=first_day_of_month, status='COMPLETED')
    month_revenue = sum(app.service.price for app in month_completed)
    
    # 5. DANE DO WYKRESU (Najpopularniejsze usługi)
    # Grupuje wizyty po nazwie usługi i liczy ich ilość w tym miesiącu
    services_data = Appointment.objects.filter(date__gte=first_day_of_month).values('service__name').annotate(count=Count('id'))
    
    # Przekształcamy to na dwie listy: nazwy i ilości
    chart_labels = [item['service__name'] for item in services_data]
    chart_data = [item['count'] for item in services_data]
    
    # PAKIET DANYCH WYSYŁANY DO HTML
    context = {
        'pending_appointments': pending_appointments,
        'today_appointments': today_appointments,
        'today_revenue': today_revenue,
        'month_revenue': month_revenue,
        
        # Konwertujemy listy Pythona na tekst w formacie JSON (żeby JS je poprawnie odczytał)
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
    }
    return render(request, 'bookings/dashboard.html', context)

    # Zmień status wizyty X na Y
@staff_member_required
def update_status(request, appointment_id, new_status):
    # Pobieramy wizytę lub wyrzucamy błąd 404 jeśli nie istnieje
    appointment = get_object_or_404(Appointment, id=appointment_id)
    
    # Lista bezpiecznych statusów
    valid_statuses = ['CONFIRMED', 'COMPLETED', 'CANCELED']
    
    if new_status in valid_statuses:
        appointment.status = new_status
        appointment.save()
        messages.success(request, f"Status wizyty {appointment.client.username} został zmieniony.")
    
    # Przekierowanie z powrotem na pulpit zarządzania
    return redirect('dashboard')