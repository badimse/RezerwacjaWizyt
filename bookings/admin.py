from django.contrib import admin
from django.utils.html import format_html
from .models import Staff, Service, Appointment

# 1. Konfiguracja widoku Pracowników
@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'specialization')
    search_fields = ('last_name', 'specialization')
    ordering = ('last_name',)

# 2. Konfiguracja widoku Usług
@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_minutes', 'icon_preview')
    search_fields = ('name',)
    
    # Mały bonus: podgląd ikony w panelu
    def icon_preview(self, obj):
        return format_html('<i class="fas {}" style="font-size: 1.2rem; color: #d63384;"></i>', obj.icon_class)
    icon_preview.short_description = "Ikona"

# 3. Konfiguracja widoku Wizyt - TWOJE CENTRUM DOWODZENIA
@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    # Usunęliśmy 'is_confirmed' i dodaliśmy 'status_colored' oraz 'source'
    list_display = ('date', 'time', 'client', 'service', 'status', 'status_colored', 'source', 'created_at')
    
    list_filter = ('status', 'source', 'date', 'staff', 'service')
    
    list_editable = ('status',)
    
    search_fields = ('client__username', 'client__first_name', 'client__last_name', 'service__name')
    
    fieldsets = (
        ('Główne informacje', {
            'fields': ('status', 'source', 'client', 'service', 'staff')
        }),
        ('Termin wizyty', {
            'fields': ('date', 'time')
        }),
        ('Notatki i historia (CRM)', {
            'fields': ('internal_notes',),
            'description': 'Notatki widoczne tylko dla pracowników salonu.'
        }),
    )

    def status_colored(self, obj):
        colors = {
            'PENDING': '#ff9800',   # Pomarańczowy
            'CONFIRMED': '#2196f3', # Niebieski
            'COMPLETED': '#4caf50', # Zielony
            'CANCELED': '#f44336',  # Czerwony
            'NOSHOW': '#9e9e9e',    # Szary
        }
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 10px; border-radius: 10px; font-weight: bold; font-size: 0.8rem;">{}</span>',
            colors.get(obj.status, '#000'),
            obj.get_status_display()
        )
    status_colored.short_description = "Status"