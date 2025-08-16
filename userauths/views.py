from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from userauths.forms import UserRegisterForm, UserLoginForm
from userauths.models import Profile, User
from store.models import Order
from django.db.models import Sum
from store.models import Wishlist,Product
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
def register_view(request):
    if request.user.is_authenticated:
        return redirect("store:index")

    form = UserRegisterForm()

    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.create(user=user)  # create profile on registration
            messages.success(request, "Account created successfully!")
            login(request, user)
            return redirect("store:index")
        else:
            messages.error(request, "Please correct the errors below.")

    return render(request, "userauths/register.html", {"form": form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect("store:index")

    form = UserLoginForm(request, data=request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            email = form.cleaned_data.get("username")  # it's email actually
            password = form.cleaned_data.get("password")
            user = authenticate(request, email=email, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f"Welcome back, {user.username}!")
                return redirect("store:index")
            else:
                messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Invalid form data.")

    return render(request, "userauths/login.html", {"form": form})


@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You’ve been logged out.")
    return redirect("userauths:login")




# @login_required
# def account_view(request):
#     # orders = Order.objects.filter(customer=request.user).order_by('-date')
#     orders = Order.objects.select_related('product', 'product__vendor').filter(customer=request.user).order_by('-date')

#     # print("✅ orders for", request.user, "=", orders)
#     return render(request, "userauths/account.html", {"orders": orders})


# @login_required
# def account_view(request):
#     orders = Order.objects.prefetch_related('items__product').filter(customer=request.user).order_by('-date')
#     return render(request, "userauths/account.html", {"orders": orders})
    



# @login_required
# def account_view(request):
#     orders = Order.objects.prefetch_related('items__product').filter(customer=request.user).order_by('-date')
#     total_spent = orders.aggregate(total=Sum('total'))['total'] or 0
#     wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
#     profile, _ = Profile.objects.get_or_create(user=request.user)
#     return render(request, "userauths/account.html", {
#         "orders": orders,
#         "total_spent": total_spent,
#         "wishlist_items": wishlist_items,
#          "profile": profile,
#     })

@login_required
def account_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    orders = Order.objects.prefetch_related('items__product').filter(customer=request.user).order_by('-date')
    total_spent = orders.aggregate(total=Sum('total'))['total'] or 0
    wishlist_items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, "userauths/account.html", {
        "orders": orders,
        "total_spent": total_spent,
        "wishlist_items": wishlist_items,
        "profile": profile,
    })



@login_required
def add_to_wishlist(request):
    if request.method == "POST":
        product_id = request.POST.get("product_id")
        product = Product.objects.get(id=product_id)
        wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
        if created:
            return JsonResponse({"message": "Added to wishlist"}, status=200)
        else:
            return JsonResponse({"message": "Already in wishlist"}, status=200)
    return JsonResponse({"error": "Invalid request"}, status=400)





from userauths.models import Profile

@login_required
def update_address(request):
    if request.method == "POST":
        profile, _ = Profile.objects.get_or_create(user=request.user)
        profile.full_name = request.POST.get("full_name")
        profile.mobile = request.POST.get("mobile")
        profile.address = request.POST.get("address")
        profile.city = request.POST.get("city")
        profile.state = request.POST.get("state")
        profile.postal_code = request.POST.get("postal_code")
        profile.country = request.POST.get("country")
        profile.save()
        messages.success(request, "Address updated successfully!")
    return redirect("userauths:account")


def remove_from_wishlist(request, product_id):
    if request.user.is_authenticated:
        product = get_object_or_404(Product, id=product_id)
        Wishlist.objects.filter(user=request.user, product=product).delete()
    return redirect('/auth/account/?tab=wishlist')  # or wherever you want to redirect



@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        profile = user.profile  # Only if you're using a Profile model

        name = request.POST.get('name')
        mobile = request.POST.get('mobile')
        avatar = request.FILES.get('avatar')

        if name:
            user.first_name = name
        if mobile:
            profile.mobile = mobile
        if avatar:
            profile.avatar = avatar

        user.save()
        profile.save()
        return redirect('userauths:account')  # or wherever your account page is


from django.contrib.auth import update_session_auth_hash
from django.contrib import messages

@login_required
def change_password(request):
    if request.method == "POST":
        user = request.user
        current = request.POST.get("current_password")
        new = request.POST.get("new_password")
        confirm = request.POST.get("confirm_password")

        if not user.check_password(current):
            messages.error(request, "Current password is incorrect.")
        elif new != confirm:
            messages.error(request, "New passwords do not match.")
        else:
            user.set_password(new)
            user.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            messages.success(request, "✅ Password changed successfully!")

        return redirect("userauths:account")  # Or wherever your account page is