from django.urls import path
from . import views

app_name = "store"

urlpatterns = [
    path('',views.index, name='index'),
    # path('members/', views.members, name='members'),
    # path('members/details/<int:id>', views.details, name='details'),
    # path('testing/', views.testing, name='testing'),
    path ("details/<slug>/" , views.product_detail, name="product_detail"),
    path('add-to-cart/', views.add_to_cart, name='add_to_cart'),
    path("cart/", views.cart_view, name="cart"),
    path("remove-from-cart/<int:cart_item_id>/", views.remove_from_cart, name="remove_from_cart"),
    path("cart/update-qty/", views.update_cart_qty, name="update_cart_qty"),
    path("cart/count/", views.cart_count, name="cart_count"),
    path('checkout/', views.checkout_view, name="checkout"),
    path("order-success/", views.order_success_view, name="order_success"),
    path("pay/", views.payment_view, name="payment"),
    path('payment/callback/', views.payment_callback, name='payment_callback'), 
    
    path("my_orders/", views.order_detail_view, name="my_orders"),
    path("shop/", views.shop_view, name="shop"),
     path('wishlist/', views.wishlist_view, name='wishlist'),
    #  path('add-to-wishlist/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/add/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'),
    # path('wishlist/remove/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('search/', views.search_view, name='search'),
    path("category/<cid>/", views.category_product_list_view, name="category_product_list"),
    path('about/', views.about_view, name='about'),
    path('wishlist/count/', views.wishlist_count, name='wishlist_count'),
    path("reviews/add/", views.add_review, name="add_review"),
]