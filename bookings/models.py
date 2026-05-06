from django.db import models
from django.contrib.auth.models import User

# 1. Model Pracownika - definiuje kto pracuje w salonie
class Staff(models.Model):
    first_name = models.CharField(max_length=50, verbose_name="Imię")
    last_name = models.CharField(max_length=50, verbose_name="Nazwisko")
    specialization = models.CharField(max_length=100, verbose_name="Specjalizacja")

    def __str__(self):
        # Wyświetla imię i nazwisko w panelu admina
        return f"{self.first_name} {self.last_name}"

# 2. Model Usługi - definiuje ofertę salonu
class Service(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True) # Nowe pole na krótki opis
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_minutes = models.IntegerField()
    # Ikona (użyjemy klas FontAwesome, np. "fa-magic")
    icon_class = models.CharField(max_length=50, default="fa-sparkles")

    def __str__(self):
        return self.name

# 3. Model Wizyty - łączy wszystkie dane w jedną rezerwację
class Appointment(models.Model):
    # ForeignKey łączy wizytę z tabelą użytkowników, pracowników i usług
    client = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Klient")
    staff = models.ForeignKey(Staff, on_delete=models.CASCADE, verbose_name="Pracownik")
    service = models.ForeignKey(Service, on_delete=models.CASCADE, verbose_name="Usługa")
    
    date = models.DateField(verbose_name="Data wizyty")
    time = models.TimeField(verbose_name="Godzina wizyty")
    
    is_confirmed = models.BooleanField(default=False, verbose_name="Czy potwierdzona?")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Zapewnia, że jeden pracownik nie może mieć dwóch wizyt w tym samym czasie
        unique_together = ('staff', 'date', 'time')

    def __str__(self):
        return f"{self.date} {self.time} - {self.client.username} u {self.staff}"