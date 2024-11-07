from django.urls import path
from .views import client_transactions, login_user, register_user

urlpatterns = [
    path('clients/<str:client_id>/transactions/', client_transactions, name='client-transactions'),
    path('login', login_user, name='login'),
    path('register', register_user, name='register'),
]