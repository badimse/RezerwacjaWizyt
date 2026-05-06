from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from .models import Service, Staff, Appointment 
from .forms import AppointmentForm

# 1. Strona główna (Cennik + Pobieranie wizyt użytkownika do Modala)
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

# 2. Rejestracja (używana przez Modal w index.html)
def register_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('index')
    return redirect('index')

# 3. Logowanie (używane przez Modal w index.html)
def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('index')
    return redirect('index')

# 4. Wylogowanie
def logout_view(request):
    logout(request)
    return redirect('index')

# 5. REZERWACJA WIZYTY (Tego brakowało!)
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
            return redirect('index')
    else:
        form = AppointmentForm()
        
    return render(request, 'bookings/book.html', {'form': form, 'service': service})

# 6. ODWOŁANIE WIZYTY
@login_required
def cancel_appointment(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, client=request.user)
    appointment.delete()
    return redirect('index')