console.log("Plik JS został pomyślnie załadowany!");

// Funkcja obsługująca zamykanie alertów po 3 sekundach
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            setTimeout(() => alert.style.display = 'none', 500);
        }, 3000);
    });
});

// Funkcje obsługi modali
function openModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.style.display = "block";
    }
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (modal) {
        modal.style.display = "none";
    }
}

// Inicjalizacja kalendarza
document.addEventListener('DOMContentLoaded', function() {
    var calendarEl = document.getElementById('calendar');

    // Generujemy dzisiejszą datę w formacie RRRR-MM-DD
    // Musimy uwzględnić lokalną strefę czasową, żeby nie było przesunięć o 1 dzień
    var tzoffset = (new Date()).getTimezoneOffset() * 60000;
    var localISOTime = (new Date(Date.now() - tzoffset)).toISOString().split('T')[0];

    if (calendarEl) {
        var calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            locale: 'pl',
            headerToolbar: {
                left: 'prev',
                center: 'title',
                right: 'next'
            },
            height: 'auto',
            firstDay: 1,
            buttonText: {
                today: 'dzisiaj'
            },
            
            // --- BLOKADA PRZESZŁOŚCI ---
            // Ustawiamy validRange, aby kalendarz zablokował dni przed 'dzisiaj'
            validRange: {
                start: localISOTime 
            },
            
            dateClick: function(info) {
                console.log("Kliknięto datę: " + info.dateStr);
                pobierzWizytyDnia(info.dateStr);
            },

            // Usunąłem "sztywne" zdarzenie testowe, bo będziemy je pobierać dynamicznie
            events: [] 
        });
        calendar.render();
    }
});

/**
 * Pobiera dane o wizytach z Django dla konkretnej daty
 */
function pobierzWizytyDnia(dataStr) {
    fetch(`/api/wizyty/${dataStr}/`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Serwer zwrócił błąd ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            wyswietlSzczegolyDnia(data, dataStr);
        })
        .catch(error => {
            console.error('Błąd podczas pobierania danych:', error);
            alert("Nie udało się pobrać szczegółów dnia. Sprawdź konsolę (F12).");
        });
}

/**
 * Wstawia dane do modalu i go otwiera
 */
function wyswietlSzczegolyDnia(zajeteWizyty, dataStr) {
    const kontener = document.getElementById('dayDetailsContent');
    if (!kontener) return;

    // Definiujemy godziny otwarcia salonu
    const godzinyPracy = ["08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00"];
    
    // Pobieramy same godziny z zajętych wizyt dla łatwego porównania
    const zajeteGodziny = zajeteWizyty.map(w => w.godzina);

    let html = `<h3>Terminy na dzień: ${dataStr}</h3>`;
    html += '<div class="time-slot-container">';

    godzinyPracy.forEach(godzina => {
        const czyZajete = zajeteGodziny.includes(godzina);
        
        if (czyZajete) {
            // --- OCHRONA PRYWATNOŚCI ---
            // Zamiast nazwy usługi i klienta, wyświetlamy ogólny komunikat
            html += `
                <div class="time-slot occupied">
                    <span>${godzina}</span>
                    <small>Termin zajęty</small>
                </div>`;
        } else {
            // Wolny termin
            html += `
                <div class="time-slot free" onclick="alert('Tu będzie formularz rezerwacji na ${godzina}')">
                    <span>${godzina}</span>
                    <small>Wolny</small>
                </div>`;
        }
    });

    html += '</div>';
    kontener.innerHTML = html;
    openModal('dayDetailsModal');
}

/* =========================================
   LOGIKA MODALU REZERWACJI (WPROST Z USŁUG)
   ========================================= */

function otworzModalRezerwacji(serviceId, serviceName) {
    // 1. Ustaw tytuł
    document.getElementById('bookingModalTitle').innerText = 'Rezerwacja: ' + serviceName;
    
    // 2. Ustaw adres, na który poleci formularz (zależy od Twojego urls.py)
    document.getElementById('bookingForm').action = '/rezerwuj/' + serviceId + '/';
    
    // 3. Zablokuj daty z przeszłości w kalendarzyku
    const dzisiaj = new Date();
    const tzoffset = dzisiaj.getTimezoneOffset() * 60000;
    const lokalnaData = new Date(dzisiaj - tzoffset).toISOString().split('T')[0];
    document.getElementById('bookingDate').setAttribute('min', lokalnaData);
    
    // 4. Zresetuj zawartość modalu
    document.getElementById('bookingDate').value = '';
    document.getElementById('bookingTime').value = '';
    document.getElementById('bookingTimeSlots').innerHTML = '<p style="color: #777; font-style: italic;">Najpierw wybierz datę z pola powyżej.</p>';
    document.getElementById('submitBookingBtn').disabled = true;
    document.getElementById('submitBookingBtn').style.opacity = '0.5';

    // 5. Pokaż modal
    openModal('bookingModal');
}

// Reakcja na zmianę daty w polu <input type="date">
document.addEventListener('DOMContentLoaded', function() {
    const dateInput = document.getElementById('bookingDate');
    if (dateInput) {
        dateInput.addEventListener('change', function() {
            const wybranaData = this.value;
            if (wybranaData) {
                // Wykorzystujemy API z poprzedniego kroku!
                pobierzGodzinyDoRezerwacji(wybranaData);
            }
        });
    }
});

function pobierzGodzinyDoRezerwacji(dataStr) {
    const kontener = document.getElementById('bookingTimeSlots');
    kontener.innerHTML = '<p>Sprawdzam dostępność...</p>';
    
    fetch(`/api/wizyty/${dataStr}/`)
        .then(response => {
            if (!response.ok) throw new Error("Błąd serwera");
            return response.json();
        })
        .then(zajeteWizyty => {
            generujKafelkiRezerwacji(zajeteWizyty);
        })
        .catch(error => {
            kontener.innerHTML = '<p style="color: red;">Nie udało się załadować terminów.</p>';
        });
}

function generujKafelkiRezerwacji(zajeteWizyty) {
    const kontener = document.getElementById('bookingTimeSlots');
    const godzinyPracy = ["08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00"];
    
    // Wyciągamy tylko listę godzin z zajętych wizyt
    const zajeteGodziny = zajeteWizyty.map(w => w.godzina);
    
    let html = '';
    
    godzinyPracy.forEach(godzina => {
        if (zajeteGodziny.includes(godzina)) {
            // Termin zajęty (czerwony)
            html += `
                <div class="time-slot occupied">
                    <span>${godzina}</span>
                    <small>Zajęte</small>
                </div>`;
        } else {
            // Termin wolny (zielony) - dodajemy akcję kliknięcia
            html += `
                <div class="time-slot free" onclick="wybierzGodzine(this, '${godzina}')">
                    <span>${godzina}</span>
                    <small>Wybierz</small>
                </div>`;
        }
    });
    
    kontener.innerHTML = html;
}

function wybierzGodzine(kliknietyElement, godzina) {
    // 1. Zresetuj styl wszystkich innych kafelków
    const wszystkieKafelki = document.querySelectorAll('#bookingTimeSlots .time-slot.free');
    wszystkieKafelki.forEach(kafelek => {
        kafelek.style.backgroundColor = '#f0fff4';
        kafelek.style.color = '#28a745';
        kafelek.style.borderColor = '#28a745';
    });
    
    // 2. Zmień wygląd klikniętego kafelka na "zaznaczony" (różowy motyw)
    kliknietyElement.style.backgroundColor = '#d63384';
    kliknietyElement.style.color = 'white';
    kliknietyElement.style.borderColor = '#d63384';
    
    // 3. Wpisz godzinę do ukrytego pola, by Django ją odczytało
    document.getElementById('bookingTime').value = godzina;
    
    // 4. Odblokuj przycisk zatwierdzenia rezerwacji
    const btnSubmit = document.getElementById('submitBookingBtn');
    btnSubmit.disabled = false;
    btnSubmit.style.opacity = '1';
}

