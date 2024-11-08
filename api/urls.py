from django.urls import path, include
from .views import client_transactions, login_user, register_user

urlpatterns = [
    path('auth/', include([
        path('login/', login_user, name='login'),
        path('register/', register_user, name='register'),
    ])),

    path('clients/<str:client_id>/transactions/', client_transactions, name='client-transactions'),
]