from django.urls import path
from . import views

app_name = 'requests'

urlpatterns = [
    path('create/<int:company_id>/', views.CreateRequestView.as_view(), name='create'),
    path('<int:pk>/', views.RequestDetailView.as_view(), name='detail'),
    path('list/', views.RequestListView.as_view(), name='list'),
    path('process/<int:pk>/', views.ProcessRequestView.as_view(), name='process'),
    path('reply/<int:request_id>/', views.CreateRequestReplyView.as_view(), name='reply'),
    path('company/<int:company_id>/', views.CompanyRequestListView.as_view(), name='company_requests'),
]
