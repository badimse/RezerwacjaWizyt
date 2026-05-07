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

    # Sprytny dodatek: dzięki temu HTML i Views mogą używać 'staff.name'
    @property
    def name(self):
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
    STATUS_CHOICES = [
        ('PENDING', 'Oczekująca (Nowa)'),
        ('CONFIRMED', 'Potwierdzona'),
        ('COMPLETED', 'Zrealizowana'),
        ('CANCELED', 'Odwołana'),
        ('NOSHOW', 'Nieobecność (No-show)'),
    ]

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
        return f"{self.date} {self.time} - {self.client.username} ({self.get_status_display()})"
    
    PAYMENT_METHODS = [
        ('CASH', 'Gotówka'),
        ('CARD', 'Karta'),
        ('BLIK', 'BLIK'),
        ('VOUCHER', 'Voucher'),
        ('OTHER', 'Inna'),
    ]
    
    payment_method = models.CharField(
        max_length=10, 
        choices=PAYMENT_METHODS, 
        null=True, 
        blank=True
    )


# 4. NOWOŚĆ: Model Obecności (Ewidencja czasu pracy)
class Attendance(models.Model):
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, related_name='attendances', verbose_name="Pracownik")
    date = models.DateField(verbose_name="Data")
    is_present = models.BooleanField(default=False, verbose_name="Obecny w pracy")

    class Meta:
        # Zabezpieczenie: dany pracownik może mieć tylko jeden wpis na dany dzień
        unique_together = ('staff', 'date')
        verbose_name = "Obecność"
        verbose_name_plural = "Obecności"

    def __str__(self):
        stan = "Obecny(a)" if self.is_present else "Nieobecny(a)"
        return f"{self.staff.first_name} {self.staff.last_name} - {self.date} - {stan}"