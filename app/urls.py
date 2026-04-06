from django.urls import path 
from app import views 

urlpatterns = [
    path('', views.index, name='index'),
    path('about', views.about, name='about'), 
    path('register', views.register, name='register'), 
    path('login', views.login, name='login'),
    path('submit_code', views.submit_code, name='submit_code'),
    path('generate_code', views.generate_code, name='generate_code'),
    path('analyze_code', views.analyze_code, name='analyze_code'),
    path("profile", views.profile, name="profile"),
    path('logout', views.logout, name='logout'),
    path('download/<int:id>/', views.download_result, name='download_result'),
    # path('verify-otp', views.verify_otp, name='verify_otp'),
]