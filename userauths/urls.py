from django.urls import path
from userauths import views

app_name = "userauths"  # 👈 this is important for namespacing

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("account/", views.account_view, name="account"),
    path("update-address/", views.update_address, name="update_address"),
    path('remove-from-wishlist/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
     path('update-profile/', views.update_profile, name='update_profile'),
     path("change-password/", views.change_password, name="change_password"),

]
