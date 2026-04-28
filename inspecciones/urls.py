from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.index, name='index'),
    path('nuevo/', views.nuevo_registro, name='nuevo_registro'),
    path('detalle/<int:pk>/', views.detalle_registro, name='detalle_registro'),
    path('editar/<int:pk>/', views.editar_registro, name='editar_registro'),
    path('eliminar/<int:pk>/', views.eliminar_registro, name='eliminar_registro'),

    # 🔐 LOGIN
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),

    path('seleccionar/', views.seleccionar_medidores, name='seleccionar'),
    path('generar/', views.generar_informe, name='generar_informe'),
]