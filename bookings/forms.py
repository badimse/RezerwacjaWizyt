from django import forms
from .models import Appointment
from django.utils import timezone
from django.core.exceptions import ValidationError

class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ['staff', 'date', 'time']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'staff': forms.Select(attrs={'class': 'form-control'}),
        }

    # 1. Walidacja daty (brak przeszłości)
    def clean_date(self):
        date = self.cleaned_data.get('date')
        if date < timezone.now().date():
            raise ValidationError("Nie możesz zarezerwować wizyty w przeszłości!")
        return date

    # 2. Walidacja dostępności terminu
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        time = cleaned_data.get('time')
        staff = cleaned_data.get('staff')

        if date and time and staff:
            # Szukamy w bazie MySQL czy istnieje już taki wpis
            exists = Appointment.objects.filter(
                date=date,
                time=time,
                staff=staff
            ).exists()
            
            if exists:
                raise ValidationError(f"Przepraszamy, {staff.name} ma już zajęty ten termin.")
        
        return cleaned_data