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
            
            // NOWOŚĆ: Reakcja na kliknięcie w dzień
            navLinks: true, 
            dateClick: function(info) {
                // info.dateStr to data w formacie RRRR-MM-DD
                console.log("Kliknięto datę: " + info.dateStr);
                pobierzWizytyDnia(info.dateStr);
            },

            events: [
                {
                    title: 'Dostępne',
                    start: '2026-05-10',
                    color: '#d63384'
                }
            ]
        });
        calendar.render();
    }
});

/**
 * Pobiera dane o wizytach z Django dla konkretnej daty
 */
function pobierzWizytyDnia(dataStr) {
    // Wysyłamy zapytanie do specjalnego adresu w Django
    fetch(`/api/wizyty/${dataStr}/`)
        .then(response => response.json())
        .then(data => {
            wyswietlSzczegolyDnia(data, dataStr);
        })
        .catch(error => {
            console.error('Błąd podczas pobierania danych:', error);
            alert("Nie udało się pobrać szczegółów dnia.");
        });
}

/**
 * Wstawia dane do modalu i go otwiera
 */
function wyswietlSzczegolyDnia(wizyty, dataStr) {
    const kontener = document.getElementById('dayDetailsContent');
    if (!kontener) return;

    let html = `<h3>Plan na dzień: ${dataStr}</h3>`;

    if (wizyty.length === 0) {
        html += '<p>Brak zarezerwowanych wizyt na ten dzień.</p>';
    } else {
        html += '<ul style="list-style: none; padding: 0;">';
        wizyty.forEach(w => {
            html += `
                <li style="border-bottom: 1px solid #eee; padding: 10px 0;">
                    <strong>${w.godzina}</strong> — ${w.usluga} <br>
                    <small>Klient: ${w.klient}</small>
                </li>`;
        });
        html += '</ul>';
    }

    kontener.innerHTML = html;
    openModal('dayDetailsModal');
}