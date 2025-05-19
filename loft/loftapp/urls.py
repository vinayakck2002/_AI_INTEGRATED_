from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [

    # Custom Admin URLs
    path('adm', views.admin_view, name='admin_view'),
    path('admin_add_product', views.admin_add_product, name='add_product'),
    path('delete/<int:product_id>/', views.delete_product, name='delete'),
    path('delete-category/<int:category_id>/',
         views.delete_category, name='delete_category'),
    path('edit/<int:product_id>/', views.admin_edit_product, name='edit'),

    path('admin/product/<int:product_id>/sizes/',
         views.admin_manage_product_sizes, name='admin_manage_product_sizes'),
    path('view_bookings/', views.view_bookings, name='view_bookings'),


    # User URLs



    path('', views.loft_view, name='user'),
    path('register', views.register_view, name='register'),
    path('login/', views.register_view, name='login'),  # ✅ Add this
    path('aboutus/', views.aboutus, name='aboutus'),

    #Review
# urls.py
     path('addReview/<int:pk>/', views.addReview, name='addReview'),


    path('cart', views.Cart_view, name='cart'),
    path('add_to_cart/<int:product_id>/',
         views.add_to_cart, name='add_to_cart'),
    path('product', views.Product_view, name='product'),
    path('product/gender/<int:gender_id>/',
         views.product_list_by_gender, name='product_list_by_gender'),
    path('remove-from-cart/<int:item_id>/',
         views.remove_from_cart, name='remove_from_cart'),
    path('productdetails/<int:pk>/',
         views.product_detail_view, name='product_detail'),
    path('search/', views.search_func, name='search_func'),
    path('logout', views.logout_view, name='logout'),
    path('update_cart_quantity/', views.update_cart_quantity,
         name='update_cart_quantity'),
    path('wishlist/', views.view_wishlist, name='wishlist'),
    path('add_to_wishlist/<int:id>/',
         views.add_to_wishlist, name='add_to_wishlist'),
    path('remove_from_wishlist/<int:id>/',
         views.remove_from_wishlist, name='remove_from_wishlist'),
    path('my-orders/', views.my_orders, name='my_orders'),

    path('profile/', views.profile_view, name='profile'),
    path('profile/address/add/', views.add_address, name='add_address'),
    path('profile/address/edit/<int:address_id>/',
         views.edit_address, name='edit_address'),
    path('profile/address/delete/<int:address_id>/',
         views.delete_address, name='delete_address'),
    path('profile/edit-email/', views.edit_email, name='edit_email'),
    path('edit_username/', views.edit_username, name='edit_username'),


    path('forgotpassword', views.getusername, name='forgotpassword'),
    path('verifyotp', views.verifyotp, name='verifyotp'),
    path('passwordreset', views.passwordreset, name='passwordreset'),
    path('getusername/', views.getusername, name='getusername'),





    path('select-address/<int:product_id>/',
         views.select_address, name='select_address'),
    path('process-payment/<int:product_id>/',
         views.process_payment, name='process_payment'),
    path('buy-now-payment/', views.buy_now_payment, name='buy_now_payment'),
    path('razorpay/callback/', views.callback, name='razorpay_callback'),



    path('cart/checkout/', views.checkout_cart, name='checkout_cart'),
    path('cart/payment/callback/', views.cart_payment_callback,
         name='razorpay_callback'),
    path('payment_failed/', views.payment_failed, name='payment_failed')
]


# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
