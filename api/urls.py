from django.urls import path, include
from .views import client_transactions, get_clients, login_user, register_user

urlpatterns = [
    path('auth/', include([
        path('login/', login_user, name='login'),
        path('register/', register_user, name='register'),
    ])),

    path('clients/', include([
        path('', get_clients, name='clients'),
        path('<str:client_id>/transactions/', client_transactions, name='client-transactions'),
    ])),
]
