# Create your views here.
from .models import Order, PaymentStatus  # Adjust the import path as needed
from django.shortcuts import render
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import *
from django.core.paginator import Paginator
from django.conf import settings
from django.core.mail import send_mail
from django.views.decorators.csrf import csrf_exempt
import razorpay
from django.urls import reverse
from django.db.models import Q
from datetime import datetime, timedelta
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import random
from .vectorize import vectorize_product_with_reviews,vectorize_user_with_search,pd
import json
from .read_content import *
from django.db.models import Case, When








def admin_view(request):
    products = Product.objects.all()
    context = {
        'products': products
    }
    return render(request, 'admin/main.html', context)


def admin_add_product(request):
    categories = ShoeCategory.objects.all()
    genders = Gender.objects.all()

    if request.method == 'POST':
        # --- Handle category addition ---
        if 'add_category' in request.POST:
            category_name = request.POST.get('new_category_name')
            if category_name:
                ShoeCategory.objects.get_or_create(name=category_name)
                messages.success(request, f'Category "{category_name}" added successfully!')
            else:
                messages.error(request, 'Category name cannot be empty.')
            return redirect('add_product')

        # --- Handle gender addition ---
        elif 'add_gender' in request.POST:
            gender_name = request.POST.get('new_gender_name')
            if gender_name:
                Gender.objects.get_or_create(name=gender_name)
                messages.success(request, f'Gender "{gender_name}" added successfully!')
            else:
                messages.error(request, 'Gender name cannot be empty.')
            return redirect('add_product')

        # --- Add new product ---
        name = request.POST.get('product_name')
        price = int(request.POST.get('price') or 0)
        offerprice = int(request.POST.get('offer_price') or 0)
        color = request.POST.get('color')
        description = request.POST.get('description')
        shoe_category_id = request.POST.get('shoe_category')
        gender_id = request.POST.get('gender')
        priority = int(request.POST.get('priority') or 0)
        sizes = request.POST.getlist('size[]')
        stock_values = request.POST.getlist('size_stock[]')

        try:
            shoe_category = ShoeCategory.objects.get(id=shoe_category_id)
            gender = Gender.objects.get(id=gender_id)
            print(shoe_category, gender)
            product = Product.objects.create(
                name=name,
                price=price,
                offerprice=offerprice,
                color=color,
                description=description,
                shoe_category=shoe_category,
                gender=gender,
                priority=priority,
                rating=0,
            )

            # Handle image uploads
            product.image = request.FILES.get('image1') or product.image
            product.image1 = request.FILES.get('image2') or product.image1
            product.image2 = request.FILES.get('image3') or product.image2
            product.image3 = request.FILES.get('image4') or product.image3
            product.image4 = request.FILES.get('image5') or product.image4
            product.image5 = request.FILES.get('image6') or product.image5

            product.save()

            # Vectorization
            df = pd.DataFrame([{
                "id": product.id,
                "name": name,
                "rating": 0,
                "shoe_category": shoe_category.name,
                "description": description,
                "reviews": '',
            }])
            product_vector = vectorize_product_with_reviews(df)
            print(product_vector)
            product.vector_data = json.dumps(product_vector[0].tolist())
            product.save()

            # Create sizes
            for i, size in enumerate(sizes):
                stock = int(stock_values[i]) if i < len(stock_values) else 0
                ProductSize.objects.create(product=product, size=int(size), Stock=stock)

            messages.success(request, 'Product added successfully!')
            return redirect('admin_view')

        except Exception as e:
            messages.error(request, f'Error adding product: {str(e)}')

    available_sizes = [6, 7, 8, 9, 10, 11]

    return render(request, 'admin/add.html', {
        'categories': categories,
        'genders': genders,
        'available_sizes': available_sizes
    })




# =====================================================================================================================================



# ======================================================================================================================================


def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, "Product deleted successfully!")
    return redirect('admin_view')


def admin_edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    categories = ShoeCategory.objects.all()
    genders = Gender.objects.all()
    available_sizes = [6, 7, 8, 9, 10, 11]

    if request.method == 'POST':
        try:
            # Basic product info
            product.name = request.POST.get('product_name')
            product.price = request.POST.get('price')
            product.offerprice = request.POST.get('offer_price', 0)
            product.color = request.POST.get('color')
            product.description = request.POST.get('description')
            product.priority = int(request.POST.get('priority', 0))

            # Foreign keys
            product.shoe_category = ShoeCategory.objects.get(
                id=request.POST.get('shoe_category'))
            product.gender = Gender.objects.get(id=request.POST.get('gender'))

            # Images (only update if a new image is uploaded)
            if 'image1' in request.FILES:
                product.image = request.FILES['image1']
            if 'image2' in request.FILES:
                product.image1 = request.FILES['image2']
            if 'image3' in request.FILES:
                product.image2 = request.FILES['image3']
            if 'image4' in request.FILES:
                product.image3 = request.FILES['image4']
            if 'image5' in request.FILES:
                product.image4 = request.FILES['image5']
            if 'image6' in request.FILES:
                product.image5 = request.FILES['image6']

            product.save()

            # Update sizes
            sizes = request.POST.getlist('size[]')
            stock_values = request.POST.getlist('size_stock[]')

            # Delete previous size records
            ProductSize.objects.filter(product=product).delete()

            # Create new ones
            for i, size in enumerate(sizes):
                stock = stock_values[i] if i < len(stock_values) else 0
                ProductSize.objects.create(
                    product=product,
                    size=int(size),
                    Stock=int(stock)
                )

            messages.success(request, 'Product updated successfully!')
            return redirect('edit')

        except Exception as e:
            messages.error(request, f'Error updating product: {str(e)}')

    # Pre-select existing sizes and stocks
    product_sizes = ProductSize.objects.filter(product=product)
    selected_sizes = {ps.size: ps.Stock for ps in product_sizes}

    context = {
        'product': product,
        'categories': categories,
        'genders': genders,
        'available_sizes': available_sizes,
        'selected_sizes': selected_sizes
    }
    return render(request, 'admin/edit.html', context)

# ----------------------------------------------------------------------------------------------------------------------------


def delete_category(request, category_id):
    category = ShoeCategory.objects.filter(
        id=category_id).first()  # Check if the category exists

    if not category:
        messages.error(request, "Category not found.")
        return redirect('admin_view')

    if request.method == "POST":
        category.delete()
        messages.success(request, "Category deleted successfully!")

    return redirect('add_product')  # Redirect back to admin page


def admin_manage_product_sizes(request, product_id):
    # Get the product or return 404 if not found
    product = get_object_or_404(Product, id=product_id)
    # Query all sizes for this product
    product_sizes = ProductSize.objects.filter(product=product)

    if request.method == 'POST':
        # Handle adding a new size
        if 'add_size' in request.POST:
            size = request.POST.get('size')
            stock = request.POST.get('stock')

            if size and stock:
                try:
                    # Check if size already exists for this product
                    existing_size = product_sizes.filter(size=size).first()
                    if existing_size:
                        # Update stock if size exists
                        existing_size.Stock = stock
                        existing_size.save()
                        messages.success(
                            request, f'Size {size} stock updated successfully!')
                    else:
                        # Create new size
                        ProductSize.objects.create(
                            product=product,
                            size=size,
                            Stock=stock
                        )
                        messages.success(
                            request, f'Size {size} added successfully!')
                    # Redirect to avoid form resubmission
                    return redirect('manage_product_sizes', product_id=product_id)
                except Exception as e:
                    messages.error(request, f'Error adding size: {str(e)}')
            else:
                messages.error(request, 'Both size and stock are required.')

        # Handle updating existing sizes
        elif 'update_sizes' in request.POST:
            size_ids = request.POST.getlist('size_id[]')
            sizes = request.POST.getlist('existing_size[]')
            stocks = request.POST.getlist('existing_stock[]')

            try:
                # Ensure we have data to process
                if size_ids and sizes and stocks and len(size_ids) == len(sizes) == len(stocks):
                    for i in range(len(size_ids)):
                        if size_ids[i] and sizes[i] and stocks[i]:
                            size_obj = ProductSize.objects.get(
                                id=size_ids[i], product=product)
                            size_obj.size = sizes[i]
                            size_obj.Stock = stocks[i]
                            size_obj.save()

                    messages.success(
                        request, 'All sizes updated successfully!')
                else:
                    messages.error(
                        request, 'Invalid data received for updating sizes.')
                # Redirect to avoid form resubmission
                return redirect('manage_product_sizes', product_id=product_id)
            except Exception as e:
                messages.error(request, f'Error updating sizes: {str(e)}')

        # Handle deleting a size
        elif 'delete_size' in request.POST:
            size_id = request.POST.get('size_id')
            try:
                # Ensure the size belongs to this product before deleting
                size_obj = ProductSize.objects.get(id=size_id, product=product)
                size_value = size_obj.size  # Store size value for message
                size_obj.delete()
                messages.success(
                    request, f'Size {size_value} deleted successfully!')
                # Redirect to avoid form resubmission
                return redirect('manage_product_sizes', product_id=product_id)
            except ProductSize.DoesNotExist:
                messages.error(
                    request, 'Size not found or does not belong to this product.')
            except Exception as e:
                messages.error(request, f'Error deleting size: {str(e)}')

    # Always refresh the sizes query after any operation
    product_sizes = ProductSize.objects.filter(product=product)

    context = {
        'product': product,
        'product_sizes': product_sizes
    }

    return render(request, 'admin/manage_product_sizes.html', context)
# --------------View booking details -----------------------------------------------------------------------------------------------------------------


@login_required
def view_bookings(request):
    """
    Superuser sees all orders; normal users see only their own.
    Supports sorting, status filtering, and pagination.
    """
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    valid_sort_fields = ['created_at',
                         '-created_at', 'amount', '-amount', 'status']
    if sort_by not in valid_sort_fields:
        sort_by = '-created_at'

    # Order queryset
    if request.user.is_superuser:
        orders = Order.objects.all().order_by(sort_by)
    else:
        orders = Order.objects.filter(user=request.user).order_by(sort_by)

    # Status filter
    status_filter = request.GET.get('status')
    if status_filter in [PaymentStatus.SUCCESS, PaymentStatus.FAILURE, PaymentStatus.PENDING]:
        orders = orders.filter(status=status_filter)

    # Pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(orders, 10)

    try:
        orders_page = paginator.page(page)
    except PageNotAnInteger:
        orders_page = paginator.page(1)
    except EmptyPage:
        orders_page = paginator.page(paginator.num_pages)

    context = {
        'orders': orders_page,
        'current_sort': sort_by,
        'current_status': status_filter,
        'payment_statuses': [PaymentStatus.SUCCESS, PaymentStatus.FAILURE, PaymentStatus.PENDING],
    }

    return render(request, 'admin/view_bookings.html', context)


# =============================USER--SIDE====================================================================================================

def register_view(request):
    if request.method == 'POST' and 'register' in request.POST:  
        try:
            username = request.POST.get('username')
            password = request.POST.get('password')
            comfirm_password = request.POST.get('comfirm_password')
            email = request.POST.get('email')
            address = request.POST.get('address')

            # Check if username is present
            if not username:
                messages.error(request, "Username is required.")
                return render(request, 'user/account.html')

            # Password validation
            if len(password) < 8:
                messages.error(
                    request, "Password must be at least 8 characters long.")
                return render(request, 'user/account.html')

            # Check for at least one digit
            # if not any(char.isdigit() for char in password):
            #     messages.error(
            #         request, "Password must contain at least one number.")
            #     return render(request, 'user/account.html')

            # Check for at least one uppercase letter
            # if not any(char.isupper() for char in password):
            #     messages.error(
            #         request, "Password must contain at least one uppercase letter.")
            #     return render(request, 'user/account.html')

            # Check for at least one lowercase letter
            # if not any(char.islower() for char in password):
            #     messages.error(
            #         request, "Password must contain at least one lowercase letter.")
            #     return render(request, 'user/account.html')

            # # Check for at least one special character
            # special_chars = "!@#$%^&*()-_=+[]{}|;:'\",.<>/?"
            # if not any(char in special_chars for char in password):
            #     messages.error(
            #         request, "Password must contain at least one special character.")
            #     return render(request, 'user/account.html')

            # Check if passwords match
            if password != comfirm_password:
                messages.error(request, "Passwords do not match.")
                return render(request, 'user/account.html')

            # Check if username already exists
            if User.objects.filter(username=username).exists():
                messages.error(request, "Username already exists.")
                return render(request, 'user/account.html')

            # Check if email already exists
            if User.objects.filter(email=email).exists():
                messages.error(request, "Email already exists.")
                return render(request, 'user/account.html')

            # Create user
            user = User.objects.create_user(
                username=username, password=password, email=email)
            user.save()
            dt=users.objects.create(name=user)
            dt.save()
            user_datas =  [{
                "user_id": user.id,
                "product":'',
                "search":'',
            }]
            df=pd.DataFrame(user_datas)
            user_vectors=vectorize_user_with_search(df)
            dt.vector_data=json.dumps(user_vectors[0].tolist())
            dt.save()


            Address.objects.create(
                user=user,
                name=username,  # Using username as name
                address=address,
                phone=""  # Empty phone number
            )

            # Optional: Send email after registration
            try:
                send_mail(
                    'LOFT Registration',
                    '🎉 Welcome to LOFT Shoe World! Your account has been created successfully.',
                    settings.EMAIL_HOST_USER,
                    [email],
                    fail_silently=False
                )
            except Exception as email_error:
                # Log the email error but don't stop the registration process
                print(f"Email sending failed: {email_error}")

            # Store session data: Save user information in session
            request.session['user'] = user.username
            request.session['user_id'] = user.id

            messages.success(
                request, "Account created successfully! Please log in.")
            # Redirect after successful registration to login page
            return redirect('login')  # Changed from 'account' to 'login'

        except Exception as e:
            messages.error(
                request, f"An error occurred while creating your account.")
            print(f"Registration error: {e}")

    if request.method == 'POST' and 'login' in request.POST:
        # Login process
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        print(user)
        if user:
            login(request, user)

            # Store session data after successful login
            request.session['user'] = user.username
            request.session['user_id'] = user.id

            if user.is_superuser:
                # Redirect admin users to the admin panel
                return redirect('admin_view')
            else:
                # Redirect normal users to their home page
                return redirect('user')
        else:
            messages.error(request, 'Invalid username or password.')

    # Add password validation requirements to context
    context = {
        'password_requirements': {
            'min_length': 8,
            'needs_digit': True,
            'needs_uppercase': True,
            'needs_lowercase': True,
            'needs_special': True,
        }
    }
    return render(request, 'user/account.html', context)



# ------------------------------------------------------------------------------------------------------------------------------------------


# ===============================Landing-page==============================================================================================================

def loft_view(request):
    data = Product.objects.all()
    size_data = ProductSize.objects.all()

    featured = Product.objects.order_by('priority')[:4]
    latest = Product.objects.order_by('-id')[:4]

    # Prepare product vectors
    product_ids = [product.pk for product in data]
    product_vectors = [json.loads(product.vector_data) for product in data]
    product_vectors = np.array(product_vectors)
    product_vectors = torch.tensor(product_vectors)

    # Default price mapping
    price_data = filter_price(data, size_data)

    # Check if user is logged in
    if 'user' in request.session:
        try:
            user = User.objects.get(username=request.session.get('user'))
            user_data = users.objects.get(name=user)
            user_vector = json.loads(user_data.vector_data)

            # Get recommendations
            recommended_products = recommend_product(user_vector, product_vectors, product_ids, top_n=12)
            recommended_ids = [item[0] for item in recommended_products]

            # Preserve recommended order
            preserved_order = Case(*[When(pk=pk, then=pos) for pos, pk in enumerate(recommended_ids)])
            recommended_queryset = Product.objects.filter(pk__in=recommended_ids).order_by(preserved_order)

            price_data = filter_price(recommended_queryset, size_data)

        except (User.DoesNotExist, users.DoesNotExist, KeyError, json.JSONDecodeError):
            pass

    context = {
        'price': price_data,
        'featured': featured,
        'latest': latest,
    }

    return render(request, 'user/loft.html', context)

# ===================ALL--PRODUCTS--VIEW==========================================================================================================


def Product_view(request):
    product_list = Product.objects.all()  # This is a QuerySet of products
    product_paginator = Paginator(product_list, 8)  # Show 2 products per page
    # Get the page number from the request, default to page 1
    page_number = request.GET.get('page', 1)
    page_obj = product_paginator.get_page(
        page_number)  # Get the requested page
    # Pass the paginated products to the template
    context = {'products': page_obj}
    return render(request, 'user/product.html', context)
# -------Recommendation-------------------------------------------------------------------------------------------

# ---------------------------------------------------------------------------------------------------------------------
def product_list_by_gender(request, gender_id):
    try:
        gender = Gender.objects.get(id=gender_id)
    except Gender.DoesNotExist:
        raise Http404("Gender not found")

    product_list = Product.objects.filter(gender=gender)
    product_paginator = Paginator(product_list, 8)
    page_number = request.GET.get('page', 1)
    page_obj = product_paginator.get_page(page_number)

    context = {'products': page_obj, 'gender': gender}
    return render(request, 'user/product.html', context)
# -----------------Aboutus-------------------------------------------------------------------------------------------------------------------------


def aboutus(request):

    return render(request, 'user/aboutus.html')
# ------------product-details view--------------------------------------------------------------------------------------------------------------------------


# def product_detail_view(request, pk):
#     product = get_object_or_404(Product, id=pk)

#     cart_product_ids = []
#     wishlist_product_ids = []
#     cart_item_count = 0
#     sizes = product.sizes.all()
#     in_stock = any(size.Stock > 0 for size in sizes)

#     if request.user.is_authenticated:
#         cart_items = Cart.objects.filter(user=request.user)
#         wishlist_items = Wishlist.objects.filter(user=request.user)

#         cart_product_ids = list(cart_items.values_list('product_id', flat=True))
#         wishlist_product_ids = list(wishlist_items.values_list('product_id', flat=True))
#         cart_item_count = cart_items.count()


#     context = {
#         'product': product,
#         'sizes': sizes,
#         'in_stock': in_stock,
#         'cart_product_ids': cart_product_ids,
#         'wishlist_product_ids': wishlist_product_ids,
#         'cart_item_count': cart_item_count,
#     }

#     return render(request, 'user/product_description.html', context)
def product_detail_view(request, pk):
    product = get_object_or_404(Product, pk=pk)

    if not request.user.is_authenticated:
        return render(request, 'user/product_description.html', {
            'product': product,
            'error': 'User not logged in'
        })

    user = request.user
    user_name, created = users.objects.get_or_create(name=user)

    # Track view history
    ViewHistory.objects.create(user=user_name, product=product)

    # Prepare view history data for vectorization
    existing_user_data = ViewHistory.objects.filter(user=user_name)
    existing_products = [history.product.name for history in existing_user_data]
    data = [{
        'user_id': user_name.id,
        'product': ','.join(existing_products),
        'search': ''
    }]
    df = pd.DataFrame(data)

    # Vectorize and save
    try:
        user_vectors = vectorize_user_with_search(df)
        user_name.vector_data = json.dumps(user_vectors[0].tolist())
        user_name.save()
    except Exception as e:
        print(f"Vectorization failed: {e}")

    # Fetch reviews
    rs = reviews.objects.filter(pname=product)
    
    # ✅ FIX: Check if user has reviewed instead of trying to get specific review
    isReviewed = reviews.objects.filter(uname=user_name, pname=product).exists()

    # Access sizes related to the product
    sizes = product.sizes.all()
    in_stock = any(size.Stock > 0 for size in sizes)

    cart_product_ids = []
    wishlist_product_ids = []
    cart_item_count = 0

    if user.is_authenticated:
        cart_items = Cart.objects.filter(user=user)
        wishlist_items = Wishlist.objects.filter(user=user)

        cart_product_ids = list(cart_items.values_list('product_id', flat=True))
        wishlist_product_ids = list(wishlist_items.values_list('product_id', flat=True))
        cart_item_count = cart_items.count()

    context = {
        'product': product,
        'sizes': sizes,
        'in_stock': in_stock,
        'cart_product_ids': cart_product_ids,
        'wishlist_product_ids': wishlist_product_ids,
        'cart_item_count': cart_item_count,
        'isReviewed': isReviewed,
        'reviews': rs,
    }

    return render(request, 'user/product_description.html', context)

# ===========================CART=================================================================================================================
# Add these imports at the top of your views.py file


# Updated Cart_view function that uses offerprice instead of price
def Cart_view(request):
    cart_items = Cart.objects.filter(user=request.user)
    for item in cart_items:
        item.total_price = item.product.offerprice * \
            item.quantity  # Using offerprice instead of price
    total_price = sum(item.product.offerprice *
                      item.quantity for item in cart_items)
    cart_item_count = cart_items.count()
    return render(request, 'user/cart.html', {'cart_items': cart_items, 'total_price': total_price, 'cart_item_count': cart_item_count})

# Updated update_cart_quantity view


def update_cart_quantity(request):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        new_quantity = int(request.POST.get('quantity'))

        cart_item = get_object_or_404(Cart, id=item_id, user=request.user)
        product_size = cart_item.product_size

        if product_size is None:
            messages.error(
                request, "This product size is no longer available.")
            cart_item.delete()  # optional: you may want to remove invalid cart item
            return redirect('cart')

        old_quantity = cart_item.quantity
        quantity_diff = new_quantity - old_quantity

        if quantity_diff == 0:
            messages.info(request, "No change in quantity.")
            return redirect('cart')

        # If trying to increase, check stock
        if quantity_diff > 0:
            if product_size.Stock < quantity_diff:
                messages.error(
                    request, f"Only {product_size.Stock} items left in stock.")
                return redirect('cart')
            product_size.Stock -= quantity_diff

        # If decreasing, return stock
        elif quantity_diff < 0:
            product_size.Stock += abs(quantity_diff)

        # Save updated values
        product_size.save()
        cart_item.quantity = new_quantity
        cart_item.save()

        messages.success(request, "Cart updated successfully.")
        return redirect('cart')


@login_required(login_url='register')
def add_to_cart(request, product_id):
    if request.method == 'POST':
        size_value = request.POST.get('selected_size')
        quantity = int(request.POST.get('quantity', 1))

        product = get_object_or_404(Product, id=product_id)
        product_size = get_object_or_404(
            ProductSize, product=product, size=size_value)

        # Check available stock
        if product_size.Stock < quantity:
            messages.error(
                request, f'Only {product_size.Stock} left in stock for size {product_size.size}.')
            return redirect('product_detail', pk=product.id)

        # Check if item with same size is already in cart
        cart_item, created = Cart.objects.get_or_create(
            user=request.user,
            product=product,
            product_size=product_size
        )

        # Check if updating existing cart item will exceed stock
        if not created:
            new_quantity = cart_item.quantity + quantity
            if product_size.Stock < new_quantity:
                messages.error(
                    request, f'Not enough stock to update quantity. Only {product_size.Stock} left.')
                return redirect('product_detail', pk=product.id)
            cart_item.quantity = new_quantity
        else:
            cart_item.quantity = quantity

        # Save cart item and update stock
        cart_item.total_price = product.offerprice * cart_item.quantity
        cart_item.save()

        product_size.Stock -= quantity
        product_size.save()

        messages.success(request, 'Product added to cart successfully!')
        return redirect('cart')


def remove_from_cart(request, item_id):
    item = get_object_or_404(Cart, id=item_id, user=request.user)
    item.delete()
    return redirect('cart')

# ============WHISHLIST========================================================================================================================


@login_required
def add_to_wishlist(request, id):
    product = get_object_or_404(Product, id=id)

    # Check if the product is already in the wishlist
    wishlist_item, created = Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )

    # Redirect back to the product page
    return redirect('product_detail', pk=id)


@login_required
def remove_from_wishlist(request, id):
    product = get_object_or_404(Product, id=id)
    try:
        wishlist_item = Wishlist.objects.get(
            user=request.user, product=product)
        wishlist_item.delete()
    except Wishlist.DoesNotExist:
        pass
    # Check if "next" parameter exists in URL
    next_url = request.GET.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('product_detail', pk=id)


@login_required
def view_wishlist(request):
    wishlist_items = Wishlist.objects.filter(
        user=request.user).select_related('product')

    context = {
        'wishlist_items': wishlist_items
    }

    return render(request, 'user/wishlist.html', context)

# ===========================================================================================================================================def getuser(request):




def getuser(request):
    return request.session.get('user')


def filter_price(data, price):
    price2 = []
    for i in data:
        for j in price:
            if i.pk == j.product.pk:
                price2.append(j)
                break
    return price2


def types(request):
    type2 = []
    for i in Product.objects.all():
        if i.shoe_category and i.shoe_category.name not in type2:
            type2.append(i.shoe_category.name)
    return type2

def search_func(request):
    if request.method == 'POST':
        inp = request.POST['search']
        price2 = []

        auth_user = None
        users_data = None

        if 'user' in request.session:
            try:
                auth_user = User.objects.get(username=request.session['user'])
                users_data = users.objects.get(name=auth_user)
            except (User.DoesNotExist, users.DoesNotExist):
                auth_user = None
                users_data = None

            if users_data and auth_user:
                # Save search query
                SearchHistory.objects.create(query=inp, user=users_data)

                # Get user search history
                user_search = SearchHistory.objects.filter(user=users_data)
                user_search = [s.query for s in user_search]

                # Get view history
                user_products = ViewHistory.objects.filter(user=users_data)
                user_products = [s.product.name for s in user_products]

                # Prepare data for vectorization
                user_data = [{
                    'user_id': auth_user.id,
                    'product': ','.join(user_products) if user_products else '',
                    'search': ','.join(user_search) if user_search else ''
                }]

                df = pd.DataFrame(user_data)

                # Vectorize
                user_vectors = vectorize_user_with_search(df)
                users_data.vector_data = json.dumps(user_vectors[0].tolist())
                users_data.save()

        # Search for products by name or category
        products_by_name = Product.objects.filter(name__icontains=inp)  # Changed from iexact to icontains
        products_by_category = Product.objects.filter(shoe_category__name__icontains=inp)  # Changed from iexact to icontains
        pro_name = (products_by_name | products_by_category).distinct()

        # Match with size info
        price = ProductSize.objects.all()
        if pro_name.exists():  # Check if any products were found
            price2 = filter_price(pro_name, price)

        return render(request, 'user/search_result.html', {
            'price': price2,
            'shoe_category': types(request),
            'user': getuser(request),
            'query': inp,
            'products': pro_name
        })
    
    # Handle GET requests - redirect to home or show empty search
    return redirect('user')  # Or another appropriate action

# def search(request):    
#     query = request.GET.get('q', '')  # Get search query from GET request
#     # Filter products by name (case insensitive)
#     products = Product.objects.filter(name__icontains=query)

#     return render(request, 'user/search_result.html', {
#         'products': products,
#         'query': query,
#     })



# ======================Logout==================================================================================================================


@login_required(login_url='register')
def logout_view(request):
    logout(request)
    request.session.flush()
    return redirect('user')


# ------------------------------MY PROFILE--------------------------------------------------------------------------------------------------@login_required
def profile_view(request):
    """View to display user profile with addresses"""
    # Get all addresses for the logged-in user
    addresses = Address.objects.filter(user=request.user)

    context = {
        'addresses': addresses,
        'email': request.user.email,
    }
    return render(request, 'profile/profile.html', context)


@login_required
def add_address(request):
    """View to add a new address without using Django forms"""
    if request.method == 'POST':
        name = request.POST.get('name', '')
        address = request.POST.get('address', '')
        phone = request.POST.get('phone', '')

        # Basic validation
        errors = {}
        if not name:
            errors['name'] = 'Name is required.'
        if not address:
            errors['address'] = 'Address is required.'
        if not phone:
            errors['phone'] = 'Phone number is required.'

        if not errors:
            # Create new address
            Address.objects.create(
                user=request.user,
                name=name,
                address=address,
                phone=phone
            )
            messages.success(request, 'Address added successfully!')
            return redirect('profile')
        else:
            # If there are errors, pass them to the template
            return render(request, 'address_form.html', {
                'errors': errors,
                'name': name,
                'address': address,
                'phone': phone,
                'action': 'Add'
            })

    return render(request, 'profile/address_form.html', {'action': 'Add'})


@login_required
def edit_address(request, address_id):
    """View to edit an existing address without using Django forms"""
    # Get address or return 404 if not found
    address_obj = get_object_or_404(Address, id=address_id, user=request.user)

    if request.method == 'POST':
        name = request.POST.get('name', '')
        address = request.POST.get('address', '')
        phone = request.POST.get('phone', '')

        # Basic validation
        errors = {}
        if not name:
            errors['name'] = 'Name is required.'
        if not address:
            errors['address'] = 'Address is required.'
        if not phone:
            errors['phone'] = 'Phone number is required.'

        if not errors:
            # Update address
            address_obj.name = name
            address_obj.address = address
            address_obj.phone = phone
            address_obj.save()
            messages.success(request, 'Address updated successfully!')
            return redirect('profile')
        else:
            # If there are errors, pass them to the template
            return render(request, 'profile/address_form.html', {
                'errors': errors,
                'name': name,
                'address': address,
                'phone': phone,
                'action': 'Edit'
            })

    # Pre-fill form with existing data
    return render(request, 'profile/address_form.html', {
        'name': address_obj.name,
        'address': address_obj.address,
        'phone': address_obj.phone,
        'action': 'Edit'
    })


@login_required
def delete_address(request, address_id):
    """View to delete an address"""
    address = get_object_or_404(Address, id=address_id, user=request.user)

    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Address deleted successfully!')
        return redirect('profile')

    return render(request, 'profile/confirm_delete.html', {'address': address})


@login_required
def edit_email(request):
    """View to edit user's email"""
    user = request.user

    if request.method == 'POST':
        email = request.POST.get('email', '')

        # Basic validation
        errors = {}
        if not email:
            errors['email'] = 'Email is required.'
        elif '@' not in email:
            errors['email'] = 'Please enter a valid email address.'

        if not errors:
            # Update email
            user.email = email
            user.save()
            messages.success(request, 'Email updated successfully!')
            return redirect('profile')
        else:
            # If there are errors, pass them to the template
            return render(request, 'profile/email_form.html', {
                'errors': errors,
                'email': email
            })

    # Pre-fill form with existing email
    return render(request, 'profile/email_form.html', {
        'email': user.email
    })


@login_required
def edit_username(request):
    """View to edit user's username"""
    user = request.user

    if request.method == 'POST':
        username = request.POST.get('username', '')

        # Basic validation
        errors = {}
        if not username:
            errors['username'] = 'Username is required.'
        elif len(username) < 4:
            errors['username'] = 'Username should be at least 4 characters long.'
        elif User.objects.filter(username=username).exists():
            errors['username'] = 'This username is already taken.'

        if not errors:
            # Update username
            user.username = username
            user.save()
            messages.success(request, 'Username updated successfully!')
            return redirect('profile')
        else:
            # If there are errors, pass them to the template
            return render(request, 'profile/username_form.html', {
                'errors': errors,
                'username': username
            })

    # Pre-fill form with existing username
    return render(request, 'profile/username_form.html', {
        'username': user.username
    })


@login_required
def my_orders(request):
    # Get all orders for the logged-in user
    orders = Order.objects.all().order_by('-created_at')  # optional ordering
    return render(request, 'user/my_orders.html', {'orders': orders})

# ========================Product BUY=============================================================================================


@csrf_exempt
def callback(request):
    """
    Handle Razorpay payment callback
    """
    if request.method == "POST":
        if "razorpay_signature" in request.POST:
            payment_id = request.POST.get("razorpay_payment_id", "")
            provider_order_id = request.POST.get("razorpay_order_id", "")
            signature_id = request.POST.get("razorpay_signature", "")

            try:
                order = Order.objects.get(provider_order_id=provider_order_id)
                order.payment_id = payment_id
                order.signature_id = signature_id

                # Verify signature
                client = razorpay.Client(
                    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

                try:
                    params_dict = {
                        'razorpay_order_id': provider_order_id,
                        'razorpay_payment_id': payment_id,
                        'razorpay_signature': signature_id
                    }
                    client.utility.verify_payment_signature(params_dict)
                    order.status = PaymentStatus.SUCCESS

                    # Find and update Buy record
                    buy_record = Buy.objects.filter(
                        user=order.user,
                        product=order.product,
                        is_confirmed=False
                    ).order_by('-date').first()

                    if buy_record:
                        buy_record.is_confirmed = True
                        buy_record.save()

                    status = "success"

                except Exception as e:
                    order.status = PaymentStatus.FAILED
                    status = "failure"
                    print(f"Payment verification failed: {e}")

                order.save()
                return render(request, "user/singlepro/callback.html", context={"status": status})

            except Order.DoesNotExist:
                return render(request, "user/singlepro/callback.html", context={"status": "failure"})

        else:
            print("Error in callback: Missing Razorpay signature.")
            return render(request, "user/singlepro/callback.html", context={"status": "failure"})

    return render(request, "user/singlepro/callback.html", context={"status": "invalid_request"})


def process_payment(request, product_id):
    if request.method != 'POST':
        return redirect('product_detail', id=product_id)

    user = request.user
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    address_id = request.POST.get('address_id')

    if not address_id:
        messages.error(request, "Please select an address")
        return redirect('select_address', product_id=product_id)

    address = get_object_or_404(Address, id=address_id, user=user)

    # Calculate amount
    amount = product.offerprice * quantity

    # Initialize Razorpay client
    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    # Create Razorpay order
    razorpay_order = client.order.create({
        "amount": int(amount) * 100,  # Amount in paise
        "currency": "INR",
        "payment_capture": "1"
    })

    order_id = razorpay_order['id']

    # Create order record in the database
    order = Order.objects.create(
        user=user,
        amount=amount,
        provider_order_id=order_id,
        product=product,
        quantity=quantity,
        status=PaymentStatus.PENDING
    )

    # Create Buy record
    buy = Buy.objects.create(
        user=user,
        product=product,
        address=address,
        quantity=quantity,
        price=amount,
        is_confirmed=False
    )

    # Use the correct URL name 'razorpay_callback'
    callback_url = request.build_absolute_uri(reverse('razorpay_callback'))

    return render(
        request,
        "user/singlepro/payment.html",
        {
            "callback_url": callback_url,
            "razorpay_key": settings.RAZORPAY_KEY_ID,
            "order": order,
            "product": product,
            "address": address
        },
    )


def buy_now_payment(request):
    """
    Handles the direct purchase payment flow.
    """
    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        quantity = request.POST.get('quantity', 1)
        selected_size = request.POST.get('selected_size', None)

        # Redirect to address selection with these parameters
        return redirect('select_address', product_id=product_id)

    # If not POST, redirect to home
    return redirect('index')


def select_address(request, product_id):
    if not request.user.is_authenticated:
        return redirect('login')

    product = get_object_or_404(Product, id=product_id)
    quantity = request.POST.get('quantity', 1)
    size_id = request.POST.get(
        'selected_size') or request.GET.get('selected_size')
    selected_size = None

    if size_id:
        try:
            size_obj = ProductSize.objects.get(id=size_id)
            selected_size = size_obj.size
        except ProductSize.DoesNotExist:
            selected_size = None

    # Get all addresses for the user
    addresses = Address.objects.filter(user=request.user)

    context = {
        'product': product,
        'addresses': addresses,
        'quantity': quantity,
        'selected_size': selected_size,
    }

    return render(request, 'user/singlepro/select_address.html', context)


def process_payment(request, product_id):
    if request.method != 'POST':
        return redirect('product_detail', product_id=product_id)

    user = request.user
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    address_id = request.POST.get('address_id')

    if not address_id:
        messages.error(request, "Please select an address")
        return redirect('select_address', product_id=product_id)

    address = get_object_or_404(Address, id=address_id, user=user)

    # Calculate amount
    amount = product.offerprice * quantity

    # Initialize Razorpay client
    client = razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    # Create Razorpay order
    razorpay_order = client.order.create({
        "amount": int(amount) * 100,  # Amount in paise
        "currency": "INR",
        "payment_capture": "1"
    })

    order_id = razorpay_order['id']

    # Create order record in the database
    order = Order.objects.create(
        user=user,
        amount=amount,
        provider_order_id=order_id,
        product=product,
        quantity=quantity,
        status=PaymentStatus.PENDING
    )

    # Create Buy record
    buy = Buy.objects.create(
        user=user,
        product=product,
        address=address,
        quantity=quantity,
        price=amount,
        is_confirmed=False
    )

    # Prepare callback URL
    callback_url = request.build_absolute_uri(reverse('razorpay_callback'))

    return render(
        request,
        "user/singlepro/payment.html",
        {
            "callback_url": callback_url,
            "razorpay_key": settings.RAZORPAY_KEY_ID,
            "order": order,
            "product": product,
            "address": address
        },
    )

# -----------------cart product-----------------------------------------------------------------------------------------


@login_required
def checkout_cart(request):
    """
    Checkout page for cart items
    """
    # Get all addresses for the user
    addresses = Address.objects.filter(user=request.user)

    # Get cart items
    cart_items = Cart.objects.filter(user=request.user)

    if not cart_items.exists():
        messages.error(request, "Your cart is empty")
        return redirect('cart')

    # Calculate total price for each cart item and total amount
    total_amount = 0
    for item in cart_items:
        item.totalprice = item.product.offerprice * \
            item.quantity  # Calculate per item total
        item.save()  # Save the updated totalprice in the database
        total_amount += item.totalprice  # Add to total amount

    if request.method == 'POST':
        address_id = request.POST.get('address_id')

        if not address_id:
            messages.error(request, "Please select an address")
            return redirect('checkout_cart')
        else:
            try:
                # Get the selected address
                address = get_object_or_404(
                    Address, id=address_id, user=request.user)

                # Ensure total amount is at least ₹1 (100 paise)
                if total_amount < 1:
                    messages.error(
                        request, "Total amount is too low. Please add more items to proceed.")
                    return redirect('checkout_cart')

                # Convert to paise (multiply by 100)
                total_amount_in_paise = int(total_amount * 100)

                # Initialize Razorpay client
                client = razorpay.Client(
                    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

                # Create Razorpay order
                razorpay_order = client.order.create({
                    "amount": total_amount_in_paise,  # In paise
                    "currency": "INR",
                    "payment_capture": "1"
                })

                order_id = razorpay_order['id']

                # Create order record for the first product
                first_item = cart_items.first()
                order = Order.objects.create(
                    user=request.user,
                    product=first_item.product,
                    quantity=first_item.quantity,
                    amount=total_amount,
                    provider_order_id=order_id,
                    status=PaymentStatus.PENDING
                )

                # Create Buy records for each cart item (unconfirmed)
                for item in cart_items:
                    Buy.objects.create(
                        user=request.user,
                        product=item.product,
                        address=address,
                        quantity=item.quantity,
                        price=item.totalprice,
                        is_confirmed=False
                    )

                # Save the order ID in session for reference in callback
                request.session['cart_order_id'] = order.id

                # Prepare callback URL
                callback_url = request.build_absolute_uri(
                    reverse('razorpay_callback'))

                context = {
                    "callback_url": callback_url,
                    "razorpay_key": settings.RAZORPAY_KEY_ID,
                    "order": order,
                    "cart_items": cart_items,
                    "total_amount": total_amount,
                    "address": address,
                    "total_amount_in_paise": total_amount_in_paise
                }

                return render(request, "user/cart/payment.html", context)

            except Exception as e:
                messages.error(request, f"Payment error: {str(e)}")
                return redirect('checkout_cart')

    context = {
        'addresses': addresses,
        'cart_items': cart_items,
        'total_amount': total_amount,
    }

    return render(request, 'user/cart/checkout.html', context)


def process_cart_payment(request, address_id, total_amount):
    """
    Process payment for all items in the cart
    """
    user = request.user
    address = get_object_or_404(Address, id=address_id, user=user)

    # Get cart items
    cart_items = Cart.objects.filter(user=user)

    if not cart_items.exists():
        messages.error(request, "Your cart is empty")
        return redirect('cart')  # Fixed: 'view_cart' to 'cart'

    # Ensure total amount is at least ₹1 (100 paise)
    if total_amount < 1:
        messages.error(
            request, "Total amount is too low. Please add more items to proceed.")
        return redirect('checkout_cart')

    # Convert to paise (multiply by 100)
    total_amount_in_paise = int(total_amount * 100)

    try:
        # Initialize Razorpay client
        client = razorpay.Client(
            auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

        # Create Razorpay order
        razorpay_order = client.order.create({
            "amount": total_amount_in_paise,  # In paise
            "currency": "INR",
            "payment_capture": "1"
        })

        order_id = razorpay_order['id']

        # Create order record for the first product
        first_item = cart_items.first()
        order = Order.objects.create(
            user=user,
            product=first_item.product,
            quantity=first_item.quantity,
            amount=total_amount,
            provider_order_id=order_id,
            status=PaymentStatus.PENDING
        )

        # Create Buy records for each cart item (unconfirmed)
        for item in cart_items:
            Buy.objects.create(
                user=user,
                product=item.product,
                address=address,
                quantity=item.quantity,
                price=item.totalprice,
                is_confirmed=False
            )

        # Save the order ID in session for reference in callback
        request.session['cart_order_id'] = order.id

        # Prepare callback URL
        callback_url = request.build_absolute_uri(reverse('razorpay_callback'))

        return render(
            request,
            "user/cart/payment.html",
            {
                "callback_url": callback_url,
                "razorpay_key": settings.RAZORPAY_KEY_ID,
                "order": order,
                "cart_items": cart_items,
                "total_amount": total_amount,
                "address": address
            },
        )
    except Exception as e:
        messages.error(request, f"Payment error: {str(e)}")
        return redirect('checkout_cart')


@csrf_exempt
def cart_payment_callback(request):
    """
    Handle Razorpay payment callback for cart checkout
    """
    # Get payment details from POST data
    payment_id = request.POST.get("razorpay_payment_id", "")
    provider_order_id = request.POST.get("razorpay_order_id", "")
    signature_id = request.POST.get("razorpay_signature", "")

    # If no signature found, check query parameters (for redirect cases)
    if not signature_id and request.method == "GET":
        payment_id = request.GET.get("payment_id", "")
        provider_order_id = request.GET.get("order_id", "")
        signature_id = request.GET.get("signature", "")

    # Proceed only if we have the order ID
    if provider_order_id:
        try:
            # Find the order
            order = Order.objects.get(provider_order_id=provider_order_id)
            order.payment_id = payment_id
            order.signature_id = signature_id

            # Get the cart items
            cart_items = Cart.objects.filter(user=order.user)

            # Verify signature if we have all required parameters
            status = "failure"
            if payment_id and signature_id:
                client = razorpay.Client(
                    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

                try:
                    params_dict = {
                        'razorpay_order_id': provider_order_id,
                        'razorpay_payment_id': payment_id,
                        'razorpay_signature': signature_id
                    }
                    client.utility.verify_payment_signature(params_dict)
                    order.status = PaymentStatus.SUCCESS

                    # Find and update all Buy records with the same products as in the cart
                    for cart_item in cart_items:
                        buy_records = Buy.objects.filter(
                            user=order.user,
                            product=cart_item.product,
                            is_confirmed=False
                            # Get the most recent unconfirmed buy
                        ).order_by('-date')[:1]

                        for buy_record in buy_records:
                            buy_record.is_confirmed = True
                            buy_record.save()

                    # Clear the cart after successful payment
                    cart_items.delete()

                    status = "success"

                except Exception as e:
                    order.status = PaymentStatus.FAILURE
                    print(f"Payment verification failed: {e}")

            order.save()
            return render(request, "user/cart/callback.html", {"status": status})

        except Order.DoesNotExist:
            return render(request, "user/cart/callback.html", {"status": "failure"})

    return render(request, "user/cart/callback.html", {"status": "invalid_request"})


def payment_failed(request):
    """
    View to show a payment failure message.
    """
    return render(request, "user/cart/payment_failed.html")


# ------------------forgot password------------------------------------------------------------------

def getusername(request):
    if request.method == "POST":
        username = request.POST.get('username')
        try:
            user = User.objects.get(username=username)
            request.session['email'] = user.email
            request.session['reset_username'] = username  # Store username for later use
            
            # Generate OTP here rather than in verifyotp GET request
            otp = ''.join(random.choices('123456789', k=6))
            request.session['otp'] = otp
            request.session['otp_time'] = datetime.now().isoformat()
            
            # Send email
            message = f'Your email verification code is: {otp}'
            email_from = settings.EMAIL_HOST_USER
            recipient_list = [user.email]
            
            try:
                send_mail('Email Verification', message, email_from, recipient_list)
                return redirect('verifyotp')
            except Exception as e:
                messages.error(request, "Unable to send email. Please contact support.")
                print(f"Email error: {str(e)}")
                return redirect('getusername')
        except User.DoesNotExist:
            messages.error(request, "Username does not exist.")
            return redirect('getusername')

    return render(request, 'forgot/getusername.html')


def verifyotp(request):
    # Check if email exists in session
    if 'email' not in request.session:
        messages.error(request, "Please enter your username first.")
        return redirect('getusername')
        
    if request.method == "POST":
        otp = request.POST.get('otp')
        stored_otp = request.session.get('otp')
        otp_time_str = request.session.get('otp_time')

        if not stored_otp or not otp_time_str:
            messages.error(request, "OTP session expired. Please request a new one.")
            return redirect('getusername')

        # Check OTP expiration
        otp_time = datetime.fromisoformat(otp_time_str)
        otp_expiry_time = otp_time + timedelta(minutes=5)
        if datetime.now() > otp_expiry_time:
            messages.error(request, 'OTP has expired. Please request a new one.')
            # Keep email in session but remove expired OTP
            if 'otp' in request.session:
                del request.session['otp']
            if 'otp_time' in request.session:
                del request.session['otp_time']
            return redirect('getusername')

        # Verify OTP
        if otp == stored_otp:
            # Remove OTP from session but keep email for password reset
            if 'otp' in request.session:
                del request.session['otp']
            if 'otp_time' in request.session:
                del request.session['otp_time']
            return redirect('passwordreset')
        else:
            messages.error(request, 'Invalid OTP. Please try again.')

    # For GET requests, just display the form
    # Do NOT generate a new OTP here
    return render(request, "forgot/otp.html")


def passwordreset(request):

    # Check if email exists in session
    if 'email' not in request.session:
        messages.error(request, "Your session has expired. Please start over.")
        return redirect('getusername')
        
    if request.method == 'POST':
        password = request.POST.get('password')
        confirmpassword = request.POST.get('confpassword')

        if confirmpassword != password:
            messages.error(request, "Passwords do not match.")
        else:
            email = request.session.get('email')
            username = request.session.get('reset_username')
            
            try:
                # Try to get user by email first
                user = User.objects.get(email=email)
                
                # Additional check to ensure we're changing password for the right user
                if username and user.username != username:
                    messages.error(request, "User verification failed. Please try again.")
                    return redirect('getusername')
                    
                user.set_password(password)
                user.save()
                
                # Clean up session
                if 'email' in request.session:
                    del request.session['email']
                if 'reset_username' in request.session:
                    del request.session['reset_username']
                    
                messages.success(request, "Your password has been reset successfully.")

                # Authenticate and log in user
                user = authenticate(username=user.username, password=password)
                if user is not None:
                    login(request, user)
                    return redirect('home')  # Consider redirecting to login or home
                else:
                    return redirect('signin')  # Fallback to login page if auto-login fails
                
            except User.DoesNotExist:
                messages.error(request, "No user found with that email address.")
                return redirect('getusername')

    return render(request, "forgot/passwordreset.html")

def addReview(request, pk):
    if request.method == 'POST':
        rating = request.POST.get('rating')
        description = request.POST.get('description')
        
        prod = get_object_or_404(Product, pk=pk)
        userss = get_object_or_404(User, username=request.session.get('user'))
        user = get_object_or_404(users, name=userss)

        # Save review
        data = reviews.objects.create(rating=rating, description=description, uname=user, pname=prod)
        data.save()

        # Update average rating
        rev = reviews.objects.filter(pname=prod)
        total = [i.rating for i in rev] 
        prod.rating = round(sum(total) / len(total), 1) if total else rating
        prod.save()

        # Prepare data for vectorization
        comments = [i.description for i in rev]
        pro_data = [{
            "pro_id": prod.id,
            "name": prod.name,
            "rating": prod.rating,
            "shoe_category": prod.shoe_category.name if prod.shoe_category else "",  # ✅ Safe foreign key access
            "description": prod.description,
            "reviews": ','.join(comments)
        }]
        print(pro_data)
        df = pd.DataFrame(pro_data)
        product_vector = vectorize_product_with_reviews(df)
        prod.vector_data = json.dumps(product_vector[0].tolist())
        prod.save()

        return redirect(reverse('product_detail', args=[pk]))
    
    return redirect(reverse('product_detail', args=[pk]))  # fallback redirect