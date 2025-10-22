from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db.models import Sum
from django.contrib import messages
from decimal import Decimal
import json, uuid
from django.core.mail import send_mail
from .models import VariantItem
from .models import Variant, VariantItem, Product, Cart  # or however you’re importing models
from .models import Product, Category
from store.models import Product, Cart, Order, OrderItem,Wishlist
from store import models as store_models
# views.py
import razorpay
from django.conf import settings

from django.db.models import Q
# from django.shortcuts import render
# Homepage
from userauths.models import Profile

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def index(request):
    products = store_models.Product.objects.filter(status="Published")
    categories = store_models.Category.objects.all()

    for p in products:
        p.average_rating_value = p.average_rating()

    return render(request, 'store/index.html', {
        "products": products,
        "categories": categories,
    })

from django.http import Http404

def product_detail(request, slug):
    # Get the latest published product if duplicates exist
    product = (Product.objects
               .filter(status="Published", slug=slug)
               .order_by('-id')
               .first())
    if not product:
        raise Http404("Product not found")

    related_product = Product.objects.filter(
        category=product.category, status="Published"
    ).exclude(id=product.id)

    color_variants = VariantItem.objects.filter(
        variant__product=product,
        variant__name__icontains="color"
    )

    product_stock_range = range(1, product.stock + 1)

    return render(request, "store/product_details.html", {
        "product": product,
        "related_product": related_product,
        "product_stock_range": product_stock_range,
        "color_variants": color_variants,
    })

@csrf_exempt
def add_to_cart(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            product_id = data.get("id")
            qty = int(data.get("qty", 1))
            size = data.get("size")
            color = data.get("color")
            image_url = data.get("image")

            if not product_id:
                return JsonResponse({"status": "error", "message": "Product ID is missing!"}, status=400)

            product = Product.objects.get(id=product_id)

            cart_user = request.user if request.user.is_authenticated else None
            cart_id = None if request.user.is_authenticated else data.get("cart_id")

            existing = Cart.objects.filter(
                user=cart_user,
                cart_id=cart_id,
                product=product,
                size=size,
                color=color
            ).first()

            if not existing:
                cart_item = Cart.objects.create(
                    product=product,
                    qty=max(qty, 1),
                    price=product.price,
                    sub_total=Decimal(product.price) * max(qty, 1),
                    shipping=Decimal(product.shipping),
                    total=Decimal(product.price) * max(qty, 1) + Decimal(product.shipping),
                    size=size,
                    color=color,
                    user=cart_user,
                    cart_id=cart_id
                )

                if image_url:
                    from urllib.request import urlopen
                    from django.core.files.base import ContentFile
                    import os
                    image_data = urlopen(image_url).read()
                    file_name = os.path.basename(image_url)
                    cart_item.image.save(file_name, ContentFile(image_data), save=True)

                cart_item.save()
                target_item = cart_item
                message = "Item added to cart!"
            else:
                existing.qty += qty
                if existing.qty <= 0:
                    existing.delete()

                    # 🟢 Recalculate cart totals
                    cart_items = Cart.objects.filter(user=cart_user)
                    subtotal = sum(item.sub_total for item in cart_items)
                    shipping_total = sum(item.shipping for item in cart_items)
                    grand_total = subtotal + shipping_total

                    return JsonResponse({
                        "status": "success",
                        "message": "Item removed from cart",
                        "item_qty": 0,
                        "item_total": 0,
                        "subtotal": float(subtotal),
                        "grand_total": float(grand_total),
                        "removed": True,
                    })

                # ✅ If qty still > 0, update normally
                existing.sub_total = Decimal(product.price) * existing.qty
                existing.shipping = Decimal(product.shipping)
                existing.total = existing.sub_total + existing.shipping
                existing.save()
                target_item = existing
                message = "Item quantity updated!"

            # 🟢 Calculate cart totals
            cart_items = Cart.objects.filter(user=cart_user)
            subtotal = sum(item.sub_total for item in cart_items)
            shipping_total = sum(item.shipping for item in cart_items)
            grand_total = subtotal + shipping_total

            return JsonResponse({
                "status": "success",
                "message": message,
                "item_qty": target_item.qty,
                "item_total": float(target_item.total),
                "subtotal": float(subtotal),
                "grand_total": float(grand_total),
            })

        except Product.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Product not found!"}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)

    return JsonResponse({"status": "error", "message": "Invalid request method!"}, status=405)

# View cart
@login_required(login_url='/login/')
def cart_view(request):
    cart_items = Cart.objects.filter(user=request.user)
    subtotal = sum(item.sub_total for item in cart_items)
    shipping_total = sum(item.shipping for item in cart_items)
    grand_total = subtotal + shipping_total

    return render(request, "store/cart.html", {
        "cart_items": cart_items,
        "subtotal": subtotal,
        "shipping_total": shipping_total,
        "grand_total": grand_total,
    })

# Remove item from cart
@require_POST
@login_required
def remove_from_cart(request, cart_item_id):
    try:
        cart_item = Cart.objects.get(id=cart_item_id, user=request.user)
        cart_item.delete()
    except Cart.DoesNotExist:
        pass
    return redirect('store:cart')

# Update quantity in cart
@csrf_exempt
@login_required
def update_cart_qty(request):
    if request.method == "POST":
        data = json.loads(request.body)
        item_id = data.get("item_id")
        action = data.get("action")

        try:
            cart_item = Cart.objects.get(id=item_id, user=request.user)
            if action == "inc":
                cart_item.qty += 1
            elif action == "dec" and cart_item.qty > 1:
                cart_item.qty -= 1

            cart_item.sub_total = Decimal(cart_item.price) * cart_item.qty
            cart_item.shipping = Decimal(cart_item.product.shipping)
            cart_item.total = cart_item.sub_total + cart_item.shipping
            cart_item.save()

            return JsonResponse({"status": "success"})

        except Cart.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Cart item not found"})

    return JsonResponse({"status": "error", "message": "Invalid request method"})

# Get total cart quantity
@login_required
def cart_count(request):
    total_qty = Cart.objects.filter(user=request.user).aggregate(total=Sum('qty'))['total'] or 0
    return JsonResponse({"count": total_qty})

# @login_required
# def checkout_view(request):
#     cart_items = Cart.objects.filter(user=request.user)

#     if not cart_items.exists():
#         return redirect('store:cart')

#     subtotal = sum(item.sub_total for item in cart_items)
#     shipping = sum(item.shipping for item in cart_items)
#     total = subtotal + shipping

#     if request.method == "POST":
#         payment_method = request.POST.get("payment_method")

#         order = Order.objects.create(
#             customer=request.user,
#             order_id=uuid.uuid4().hex[:10].upper(),
#             sub_total=subtotal,
#             shipping=shipping,
#             total=total,
#             payment_method=payment_method,
#             payment_status="Pending" if payment_method != "COD" else "Paid"
#         )

#         for item in cart_items:
#             OrderItem.objects.create(
#                 order=order,
#                 product=item.product,
#                 qty=item.qty,
#                 price=item.price,
#                 sub_total=item.sub_total
#             )

#         cart_items.delete()
#         messages.success(request, "Order placed successfully!")

#         if payment_method == "COD":
#             return redirect("store:order_success")
#         else:
#             # Razorpay flow (ONLY if selected)
#             client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
#             razorpay_order = client.order.create({
#                 "amount": int(total * 100),
#                 "currency": "INR",
#                 "payment_capture": 1,
#             })
#             return render(request, "store/payment.html", {
#                 "razorpay_order_id": razorpay_order['id'],
#                 "razorpay_key": settings.RAZORPAY_KEY_ID,
#                 "amount": int(total * 100),
#             })

#     return render(request, "store/checkout.html", {
#         "cart_items": cart_items,
#         "subtotal": subtotal,
#         "shipping_total": shipping,
#         "grand_total": total,
#     })

def safe_image_url(image_field, request):
    try:
        if image_field and image_field.name:
            return request.build_absolute_uri(image_field.url)
    except ValueError:
        pass
    return request.build_absolute_uri('/static/images/placeholder.jpg')  # Ensure this file exists

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail, BadHeaderError
from django.shortcuts import render, redirect
from django.contrib import messages
import logging, uuid, razorpay

from .models import Cart, Order, OrderItem, Profile
from .utils import safe_image_url  # assuming this exists

logger = logging.getLogger(__name__)

@login_required
def checkout_view(request):
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items.exists():
        messages.warning(request, "Your cart is empty!")
        return redirect('store:cart')

    subtotal = sum(item.sub_total for item in cart_items)
    shipping = sum(item.shipping for item in cart_items)
    total = subtotal + shipping

    # ✅ Create or fetch user profile
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        # ✅ Save or update address
        profile.full_name = request.POST.get("full_name")
        profile.mobile = request.POST.get("mobile")
        profile.address = request.POST.get("address")
        profile.city = request.POST.get("city")
        profile.state = request.POST.get("state")
        profile.postal_code = request.POST.get("postal_code")
        profile.country = request.POST.get("country")
        profile.save()

        # ✅ Create order
        payment_method = request.POST.get("payment_method")
        order = Order.objects.create(
            customer=request.user,
            order_id=uuid.uuid4().hex[:10].upper(),
            sub_total=subtotal,
            shipping=shipping,
            total=total,
            payment_method=payment_method,
            payment_status="Pending" if payment_method != "COD" else "Paid"
        )

        # ✅ Create order items
        for item in cart_items:
            image_to_save = (
                item.image if item.image and item.image.name else
                item.product.image if item.product.image and item.product.image.name else
                None
            )

            OrderItem.objects.create(
                order=order,
                product=item.product,
                qty=item.qty,
                price=item.price,
                sub_total=item.sub_total,
                color=item.color,
                size=item.size,
                image=image_to_save
            )

        # ✅ Compose email message
        order_items = "\n\n".join([
            f"{item.product.name}\n"
            f"Color: {item.color or 'N/A'} | Size: {item.size or 'N/A'}\n"
            f"Qty: {item.qty} × ₹{item.price:.2f} = ₹{item.sub_total:.2f}\n"
            f"Image: {safe_image_url(item.image or item.product.image, request)}"
            for item in cart_items
        ])

        message = f"""Dear {request.user.username},

Your order {order.order_id} has been placed successfully.

Items:
{order_items}

Total: ₹{order.total}
Payment Method: {order.payment_method}

Thank you for shopping with us!

– Swetha Collections
"""

        # ✅ Send email safely (prevent crash)
        try:
            send_mail(
                "Order Confirmation",
                message,
                settings.DEFAULT_FROM_EMAIL,
                [request.user.email],
                fail_silently=False
            )
        except (BadHeaderError, Exception) as e:
            logger.error(f"❌ Email sending failed for order {order.order_id}: {e}")
            messages.warning(request, "Your order was placed successfully, but the confirmation email could not be sent.")

        # ✅ Clear cart after processing
        cart_items.delete()

        # ✅ COD orders
        if payment_method == "COD":
            messages.success(request, "Your order has been placed successfully!")
            return redirect("store:order_success")

        # ✅ Online payment (Razorpay)
        try:
            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            razorpay_order = client.order.create({
                "amount": int(total * 100),
                "currency": "INR",
                "payment_capture": 1,
            })
            order.razorpay_order_id = razorpay_order['id']
            order.save()
            return render(request, "store/payment.html", {
                "razorpay_order_id": razorpay_order['id'],
                "razorpay_key": settings.RAZORPAY_KEY_ID,
                "amount": int(total * 100),
            })
        except Exception as e:
            logger.error(f"⚠️ Razorpay order creation failed: {e}")
            messages.error(request, "There was an issue connecting to Razorpay. Please try again later.")
            return redirect("store:checkout")

    # ✅ GET request – show prefilled checkout form
    return render(request, "store/checkout.html", {
        "cart_items": cart_items,
        "subtotal": subtotal,
        "shipping_total": shipping,
        "grand_total": total,
        "profile": profile,
    })

# Order success page
@login_required
def order_success_view(request):
    return render(request, "store/order_success.html")




@login_required
def payment_view(request):
    client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

    amount = 50000  # ₹500.00 in paise
    DATA = {
        "amount": amount,
        "currency": "INR",
        "payment_capture": 1
    }

    order = client.order.create(data=DATA)

    context = {
        "order_id": order["id"],
        "amount": amount,
        "razorpay_key": settings.RAZORPAY_KEY_ID
    }


    return render(request, "store/payment.html", context)


@csrf_exempt
def payment_callback(request):
    if request.method == "POST":
        razorpay_order_id = request.POST.get('razorpay_order_id')
        razorpay_payment_id = request.POST.get('razorpay_payment_id')
        razorpay_signature = request.POST.get('razorpay_signature')

        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': razorpay_payment_id,
            'razorpay_signature': razorpay_signature
        }

        try:
            client.utility.verify_payment_signature(params_dict)
            # 🔥 Fetch and update the most recent unpaid order
            order = Order.objects.filter(razorpay_order_id=razorpay_order_id).last()
            if order:
                order.payment_id = razorpay_payment_id
                order.payment_status = "Paid"
                order.save()

            return JsonResponse({'status': 'Payment successful'})
        except razorpay.errors.SignatureVerificationError:
            return JsonResponse({'status': 'Payment verification failed'}, status=400)



@login_required
def order_detail_view(request):
    orders = Order.objects.filter(customer=request.user).order_by('-date')
    return render(request, "store/my_orders.html", {"orders": orders})

from django.shortcuts import render
from store.models import Product, Category, VariantItem

def shop_view(request):
    categories = Category.objects.all()
    products = Product.objects.filter(status="Published")

    category_cid = request.GET.get('category')
    if category_cid:
      products = products.filter(category__cid=category_cid)

    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price and max_price:
        products = products.filter(price__gte=min_price, price__lte=max_price)

    color_param = request.GET.get('color')
    size_param = request.GET.get('size')

    if color_param:
        color_param = color_param.lower()
        matching_color_variants = VariantItem.objects.filter(
            content__icontains=color_param,
            variant__name__icontains="color"
        ).select_related('variant')

        color_product_ids = [
            item.variant.product.id for item in matching_color_variants
            if item.variant and item.variant.product
        ]
        products = products.filter(id__in=color_product_ids)

    if size_param:
        matching_size_variants = VariantItem.objects.filter(
            content__iexact=size_param,
            variant__name__icontains="size"
        ).select_related('variant')

        size_product_ids = [
            item.variant.product.id for item in matching_size_variants
            if item.variant and item.variant.product
        ]
        products = products.filter(id__in=size_product_ids)

    # ✅ Attach variant image URL if color is selected
    filtered_products = []
    for product in products:
        product.variant_image_url = None

        if color_param:
            for variant in product.variants.all():
                if variant.name.lower() == 'color':
                    for item in variant.variant_items.all():
                        if item.content and item.content.lower() == color_param and item.image:
                            product.variant_image_url = item.image.url
                            break
                if product.variant_image_url:
                    break

        filtered_products.append(product)

    sizes = VariantItem.objects.filter(
        variant__name__icontains="size"
    ).values_list('content', flat=True).distinct()

    colors = VariantItem.objects.filter(
        variant__name__icontains="color"
    ).values_list('content', flat=True).distinct()

    context = {
        'categories': categories,
        'products': filtered_products,
        'sizes': sizes,
        'colors': colors,
        
    }

    
    return render(request, 'store/shop.html', context)
  
def about_view(request):
    return render(request, 'store/about.html')

@login_required
def wishlist_view(request):
    items = Wishlist.objects.filter(user=request.user).select_related('product')
    return render(request, "store/wishlist.html", {"wishlist_items": items})


# @login_required
# def add_to_wishlist(request, product_id):
#     product = get_object_or_404(Product, id=product_id)
#     Wishlist.objects.get_or_create(user=request.user, product=product)
#     return redirect('store:wishlist')
# from django.http import JsonResponse

from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

@require_POST
def add_to_wishlist(request, product_id):
    if not request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({"status": "unauthenticated"}, status=403)
        else:
            from django.shortcuts import redirect
            return redirect('userauths:login')

    product = get_object_or_404(Product, id=product_id)
    _, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if created:
        return JsonResponse({"status": "success", "message": "Added to wishlist"})
    else:
        return JsonResponse({"status": "info", "message": "Already in wishlist"})



def index(request):
    products = store_models.Product.objects.filter(status="Published")
    categories = store_models.Category.objects.all()

    for p in products:
        p.average_rating_value = p.average_rating()

    wishlist_ids = []
    wishlist_count = 0

    if request.user.is_authenticated:
        wishlist_ids = Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True)
        wishlist_count = wishlist_ids.count()

    return render(request, 'store/index.html', {
        "products": products,
        "categories": categories,
        "wishlist_ids": wishlist_ids,
        "wishlist_count": wishlist_count,
        'show_wishlist_icon': True,
    })

def search_view(request):
    query = request.GET.get('q')
    products = Product.objects.filter(name__icontains=query)
    return render(request, 'store/search_results.html', {'products': products, 'query': query})


# @login_required
# def remove_from_wishlist(request, product_id):
#     product = get_object_or_404(Product, id=product_id)
#     wishlist_item = Wishlist.objects.filter(user=request.user, product=product).first()

#     if wishlist_item:
#         wishlist_item.delete()

#     return redirect('/my-account/?tab=wishlist')

  # or wherever your wishlist is rendered

from django.shortcuts import render, get_object_or_404
from .models import Category, Product

def category_product_list_view(request, cid):
    from store.models import VariantItem

    category = get_object_or_404(Category, cid=cid)
    products = Product.objects.filter(category=category, status="Published")

    # Filter by price
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        products = products.filter(price__gte=min_price)
    if max_price:
        products = products.filter(price__lte=max_price)

    # Filter by color
    color = request.GET.get('color')
    if color:
        color = color.lower()
        matching_color_variants = VariantItem.objects.filter(
            content__icontains=color,
            variant__name__icontains="color"
        ).select_related('variant')

        product_ids = [
            item.variant.product.id for item in matching_color_variants
            if item.variant and item.variant.product.category == category
        ]
        products = products.filter(id__in=product_ids)

    # Filter by size
    size = request.GET.get('size')
    if size:
        matching_size_variants = VariantItem.objects.filter(
            content__iexact=size,
            variant__name__icontains="size"
        ).select_related('variant')

        product_ids = [
            item.variant.product.id for item in matching_size_variants
            if item.variant and item.variant.product.category == category
        ]
        products = products.filter(id__in=product_ids)

    # Attach variant image if color is selected
    for product in products:
        product.variant_image_url = None
        if color:
            for variant in product.variants.all():
                if variant.name.lower() == 'color':
                    for item in variant.variant_items.all():
                        if item.content and item.content.lower() == color and item.image:
                            product.variant_image_url = item.image.url
                            break
                if product.variant_image_url:
                    break

    categories = Category.objects.all()
    sizes = VariantItem.objects.filter(variant__name__icontains="size").values_list('content', flat=True).distinct()
    colors = VariantItem.objects.filter(variant__name__icontains="color").values_list('content', flat=True).distinct()

    context = {
        "products": products,
        "category": category,
        "categories": categories,
        "colors": colors,
        "sizes": sizes,
    }
    return render(request, 'store/shop.html', context)


def wishlist_count(request):
    if request.user.is_authenticated:
        count = Wishlist.objects.filter(user=request.user).count()
    else:
        count = 0
    return JsonResponse({"count": count})

# from django.contrib.auth.decorators import login_required
# from django.shortcuts import get_object_or_404, redirect
# from django.contrib import messages
# from django.db.models import Q

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from .models import Product, Review
from store.models import OrderItem  # your existing import

@login_required
def add_review(request):
    if request.method != "POST":
        messages.error(request, "Invalid request.")
        return redirect("store:index")

    product_id     = request.POST.get("product_id")
    order_item_id  = request.POST.get("order_item_id")  # <— new
    rating         = int(request.POST.get("rating", 0))
    note           = (request.POST.get("review") or "").strip()

    product = get_object_or_404(Product, id=product_id)

    # 1) Verify the order item exists, belongs to this user, and matches the product
    order_item = get_object_or_404(
        OrderItem,
        id=order_item_id,
        order__customer=request.user,
        product_id=product.id,
    )

    # 2) (Optional) Only allow after delivery
    # if order_item.order.status not in ["Delivered", "Completed"]:
    #     messages.error(request, "You can review after the order is delivered.")
    #     return redirect("store:product_detail", slug=product.slug)

    if not (1 <= rating <= 5):
        messages.error(request, "Please select a rating between 1 and 5 stars.")
        return redirect("store:product_detail", slug=product.slug)

    # 3) Upsert: one review per user per product (you can switch to per-order-item if your model supports it)
    review, created = Review.objects.get_or_create(
        user=request.user,
        product=product,
        defaults={"rating": rating, "review": note},
    )
    if not created:
        review.rating = rating
        review.review = note
        review.save()

    messages.success(request, "Thanks! Your review has been submitted.")
    return redirect("store:product_detail", slug=product.slug)
# from django.contrib.auth.decorators import login_required
# from django.shortcuts import redirect, get_object_or_404
# from django.contrib import messages
# from .models import Order  # adjust import


from store.models import OrderCancellation  # add this import

@login_required
def cancel_order(request):
    if request.method != "POST":
        messages.error(request, "Invalid request.")
        return redirect("userauths:account")

    order_id = request.POST.get("order_id")
    reason   = request.POST.get("reason")
    action   = request.POST.get("action")  # 'refund' or 'reorder'
    upi_id   = (request.POST.get("upi_id") or "").strip()
    bank_name = (request.POST.get("bank_account_name") or "").strip()
    bank_num  = (request.POST.get("bank_account_number") or "").strip()
    bank_ifsc = (request.POST.get("bank_ifsc") or "").strip()

    # Your orders are created with customer=request.user earlier
    order = get_object_or_404(Order, order_id=order_id, customer=request.user)

    blocked_states = {"delivered", "completed", "cancelled", "returned", "refund issued"}
    cancellable_states = {"processing", "pending", "confirmed", "cancellation requested"}

    if order.status and order.status.lower() in blocked_states:
        messages.error(request, "This order can no longer be cancelled.")
        return redirect("userauths:account")

    if order.status and order.status.lower() not in cancellable_states:
        messages.error(request, "This order cannot be cancelled at its current status.")
        return redirect("userauths:account")

    # 1) Update order status only
    order.status = "Cancellation Requested"
    order.save(update_fields=["status"])

    # 2) Upsert cancellation details in a separate table
    OrderCancellation.objects.update_or_create(
        order=order,
        defaults={
            "reason": reason,
            "action": action,
            "refund_upi_id": upi_id or None,
            "refund_bank_account_name": bank_name or None,
            "refund_bank_account_number": bank_num or None,
            "refund_bank_ifsc": bank_ifsc or None,
        },
    )

    if action == "reorder":
        messages.success(request, "Cancellation requested. You can place a new order now.")
        return redirect("store:shop")

    messages.success(request, "Your cancellation/refund request has been submitted.")
    return redirect("userauths:account")
