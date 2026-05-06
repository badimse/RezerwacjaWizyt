"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from bookings.views import index, register_view, login_view, logout_view, book_appointment, cancel_appointment

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'), 
    path('rejestracja/', register_view, name='register'),
    path('logowanie/', login_view, name='login'),
    path('wyloguj/', logout_view, name='logout'),
    path('rezerwuj/<int:service_id>/', book_appointment, name='book_appointment'),
    path('cancel/<int:appointment_id>/', cancel_appointment, name='cancel_appointment'),
]