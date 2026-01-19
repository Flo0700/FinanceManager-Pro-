from django.urls import path
from . import views

app_name = 'treasury'

urlpatterns = [
    # Dashboard
    path('dashboard', views.treasury_dashboard, name='dashboard'),
    
    # Bank Transactions
    path('bank-transactions', views.transaction_list, name='transaction_list'),
    path('bank-transactions/create', views.transaction_create, name='transaction_create'),
    
    # Reconciliations
    path('reconciliations', views.reconciliation_list, name='reconciliation_list'),
    path('reconciliations/create', views.reconciliation_create, name='reconciliation_create'),
    path('reconciliations/<uuid:reconciliation_id>', views.reconciliation_delete, name='reconciliation_delete'),
]
