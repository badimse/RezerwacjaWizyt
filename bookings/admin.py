from django.contrib import admin
from .models import Staff, Service, Appointment

# Konfiguracja widoku Pracowników
@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    # Kolumny wyświetlane na liście
    list_display = ('first_name', 'last_name', 'specialization')
    # Możliwość wyszukiwania po nazwisku
    search_fields = ('last_name', 'specialization')

# Konfiguracja widoku Usług
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_minutes')
    # Dodaje wyszukiwarkę usług
    search_fields = ('name',)

# Konfiguracja widoku Wizyt
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    # Kolumny widoczne w tabeli wizyt
    list_display = ('date', 'time', 'staff', 'client', 'service', 'is_confirmed')
    # Filtry boczne (bardzo przydatne przy dużej ilości wizyt)
    list_filter = ('date', 'staff', 'is_confirmed')
    # Możliwość zmiany statusu "potwierdzona" bezpośrednio z listy
    list_editable = ('is_confirmed',)