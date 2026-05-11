from django.contrib.auth import views as auth_views
from django.contrib import admin
from django.urls import path
from bookings.views import (
    index, login_demo, register_view, login_view, logout_view, 
    book_appointment, cancel_appointment, api_wizyty_dnia, 
    custom_dashboard, update_status, update_notes, 
    toggle_staff_status, quick_book, api_admin_events, toggle_attendance, api_user_details,
    toggle_block_user,
    delete_user, add_service, edit_service, delete_service
)

admin.site.site_header = "Panel Zarządzania Salonem"
admin.site.site_title = "Admin Salonu"
admin.site.index_title = "Witaj w centrum dowodzenia"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'), 
    path('rejestracja/', register_view, name='register'),
    path('logowanie/', login_view, name='login'),
    path('wyloguj/', logout_view, name='logout'),
    path('rezerwuj/<int:service_id>/', book_appointment, name='book_appointment'),
    path('cancel/<int:appointment_id>/', cancel_appointment, name='cancel_appointment'),
    path('api/wizyty/<str:data_str>/', api_wizyty_dnia, name='api_wizyty_dnia'),
    path('dashboard/', custom_dashboard, name='dashboard'),
    path('update-status/<int:appointment_id>/<str:new_status>/', update_status, name='update_status'),
    path('update-notes/<int:appointment_id>/', update_notes, name='update_notes'),
    path('toggle-staff/<int:user_id>/', toggle_staff_status, name='toggle_staff'),
    path('quick-book/', quick_book, name='quick_book'),
    path('api/admin/events/', api_admin_events, name='api_admin_events'),
    path('toggle-attendance/<int:attendance_id>/', toggle_attendance, name='toggle_attendance'),
    path('api/user/<int:user_id>/', api_user_details, name='api_user_details'),
    path('block-user/<int:user_id>/', toggle_block_user, name='toggle_block_user'),
    path('delete-user/<int:user_id>/', delete_user, name='delete_user'),
    # 1. Zmiana hasła (użytkownik jest zalogowany)
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='bookings/registration/password_change_form.html'), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='bookings/registration/password_change_done.html'), name='password_change_done'),
    # 2. Resetowanie hasła (użytkownik zapomniał hasła)
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='bookings/registration/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='bookings/registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='bookings/registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='bookings/registration/password_reset_complete.html'), name='password_reset_complete'),
    path('demo-login/<str:role>/', login_demo, name='demo_login'), 
    path('add-service/', add_service, name='add_service'),
    path('edit-service/<int:service_id>/', edit_service, name='edit_service'),
    path('delete-service/<int:service_id>/', delete_service, name='delete_service'),

]