from django.urls import path
from . import views

urlpatterns = [
    path('', views.demo_view),
    path('<int:demo_id>/<str:something>/', views.demo_single),
    path('all', views.all_demos, name="all_demos"),
    path('all/<int:demo_id>', views.single_demo, name="single_demo"),
    path('lv/', views.DemoListView.as_view(), name="demos"),
    path('lv/<int:id>', views.DemoDetailView.as_view(), name="demo"),
]
