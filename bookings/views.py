from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Service, Staff, Appointment 
from .forms import AppointmentForm
from django.http import JsonResponse

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

# 5. Rezerwacja wizyty (Tu był błąd wcięć)
@login_required 
def book_appointment(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    
    if request.method == 'POST':
        form = AppointmentForm(request.POST)
        if form.is_valid():
            appointment = form.save(commit=False)
            appointment.client = request.user
            appointment.service = service
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
    appointment.delete()
    messages.info(request, "Wizyta została odwołana.")
    return redirect('index')

# 7. Wyciągnięcie danych z kalenarza dla użytkownika
def get_appointments_by_date(request):
    selected_date = request.GET.get('date')
    # Pobieramy wizyty z bazy danych dla wybranej daty
    appointments = Appointment.objects.filter(date=selected_date).order_by('time')
    
    data = []
    for app in appointments:
        data.append({
            'time': app.time.strftime('%H:%M'),
            'service_name': app.service.name,
            'client': app.user.username
        })
        
    return JsonResponse(data, safe=False)