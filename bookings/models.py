from django.db import models
from django.contrib.auth.models import User

# 1. Model Pracownika
class Staff(models.Model):
    first_name = models.CharField(max_length=50, verbose_name="Imię")
    last_name = models.CharField(max_length=50, verbose_name="Nazwisko")
    specialization = models.CharField(max_length=100, verbose_name="Specjalizacja")

    class Meta:
        verbose_name = "Pracownik"
        verbose_name_plural = "Pracownicy"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

# 2. Model Usługi 
class Service(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nazwa usługi")
    description = models.TextField(blank=True, null=True, verbose_name="Opis")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Cena")
    duration_minutes = models.IntegerField(verbose_name="Czas trwania (min)")
    icon_class = models.CharField(max_length=50, default="fa-sparkles", verbose_name="Ikona (FontAwesome)")

    class Meta:
        verbose_name = "Usługa"
        verbose_name_plural = "Usługi"

    def __str__(self):
        return self.name

# 3. Model Wizyty 
class Appointment(models.Model):
    # Definicja dostępnych statusów wizyty
    STATUS_CHOICES = [
        ('PENDING', 'Oczekująca (Nowa)'),
        ('CONFIRMED', 'Potwierdzona'),
        ('COMPLETED', 'Zrealizowana'),
        ('CANCELED', 'Odwołana'),
        ('NOSHOW', 'Nieobecność (No-show)'),
    ]

    # Definicja źródeł rezerwacji
    SOURCE_CHOICES = [
        ('ONLINE', 'Strona WWW (Online)'),
        ('PHONE', 'Telefonicznie'),
        ('WALKIN', 'Osobiście (W salonie)'),
    ]

    client = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Klient")
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, verbose_name="Pracownik")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="Usługa")
    
    date = models.DateField(verbose_name="Data wizyty")
    time = models.TimeField(verbose_name="Godzina wizyty")
    
    # Zastępujemy proste 'is_confirmed' nowym systemem statusów
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='PENDING', 
        verbose_name="Status wizyty"
    )
    
    source = models.CharField(
        max_length=10, 
        choices=SOURCE_CHOICES, 
        default='ONLINE', 
        verbose_name="Źródło rezerwacji"
    )

    # Nowe pole CRM: Notatki dla pracownika
    internal_notes = models.TextField(
        blank=True, 
        null=True, 
        verbose_name="Notatki personelu (widoczne tylko w panelu)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data utworzenia zapisu")

    class Meta:
        unique_together = ('staff', 'date', 'time')
        verbose_name = "Wizyta"
        verbose_name_plural = "Wizyty"

    def __str__(self):
        # Używamy get_status_display(), aby pokazać ładną nazwę zamiast kodu (np. 'Potwierdzona')
        return f"{self.date} {self.time} - {self.client.username} ({self.get_status_display()})"