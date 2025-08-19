from django.db import models
from shortuuid.django_fields import ShortUUIDField
from django.utils import timezone
from django.utils.text import slugify
from django_ckeditor_5.fields import CKEditor5Field
from django.db.models import Avg  # Import Avg function
from userauths import models as user_models
import shortuuid
from userauths.models import User
import uuid

STATUS = (
    ("Published", "Published"),
    ("Draft", "Draft"),
    ("Disabled", "Disabled"),
)

PAYMENT_STATUS = (
    ("Paid", "Paid"),
    ("Processing", "Processing"),
    ("Failed", "Failed"),
)

PAYMENT_METHOD = (
    ("Paypal", "Paypal"),
    ("Stripe", "Stripe"),
    ("Flutterwave", "Flutterwave"),
    ("Paystack", "Paystack"),
    ("RazorPay", "RazorPay"),
)

ORDER_STATUS = (
    ("Pending", "Pending"),
    ("Processing", "Processing"),
    ("Shipped", "Shipped"),
    ("Fulfilled", "Fulfilled"),
    ("Cancelled", "Cancelled"),
)

SHIPPING_SERVICE = (
    ("DHL", "DHL"),
    ("FedEx", "FedEx"),
    ("UPS", "UPS"),
    ("GIG Logistics", "GIG Logistics"),
)

RATING = (
    (1, "★☆☆☆☆"),
    (2, "★★☆☆☆"),
    (3, "★★★☆☆"),
    (4, "★★★★☆"),
    (5, "★★★★★"),
)

class Category(models.Model):
    title = models.CharField(max_length=100)
    image = models.ImageField(upload_to="images/", null=True, blank=True)

    slug = models.SlugField(unique=True)
    cid = models.SlugField(max_length=255, unique=True)
  # TEMPORARILY allow null
    
    def save(self, *args, **kwargs):
        if not self.cid:
            self.cid = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Categories"  # Fixed Typo
        ordering = ['title']

class Product(models.Model):
    name = models.CharField(max_length=100)
    image = models.FileField(upload_to="images/", blank=True, null=True, default="images/product.jpg")
    description = CKEditor5Field('Text', config_name='extends')

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)

    price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True)
    regular_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True)
    stock = models.PositiveIntegerField(default=0, null=True, blank=True)
    shipping = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, null=True, blank=True)

    status = models.CharField(choices=[("Published", "Published"), ("Draft", "Draft")], max_length=50, default="Published")
    feature = models.BooleanField(default=False, verbose_name="Marketplace Featured")

    sku = ShortUUIDField(unique=True, length=5, max_length=50, prefix="SKU", alphabet="1234567890")
    slug = models.SlugField(null=True, blank=True)

    date = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.name

    def average_rating(self):
        return self.reviews.aggregate(avg_rating=Avg('rating'))['avg_rating'] or 0  # Fixed `Avg` aggregation alias

    def reviews(self):
        return self.review_set.all()  # Changed `Review.objects.filter(product=self)`

    def gallery(self):
        return self.gallery.all()  # Using related_name from Gallery model
    
    def variants(self):
        return Variant.objects.filter(product=self)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name) + "-" + str(shortuuid.uuid()[:2])
        super(Product, self).save(*args, **kwargs)

class Gallery(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='gallery')  # Fixed related_name
    image = models.ImageField(upload_to='gallery_images/')

    def __str__(self):
        return f"Gallery Image for {self.product.name}"

class Review(models.Model):
    user = models.ForeignKey(user_models.User, on_delete=models.SET_NULL, blank=True, null=True)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, blank=True, null=True, related_name="reviews")  # Added related_name
    review = models.TextField(null=True, blank=True)
    reply = models.TextField(null=True, blank=True)
    rating = models.IntegerField(choices=RATING, default=3)
    active = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    
    @property
    def rating_int(self):
        try:
            return int(self.rating)
        except (TypeError, ValueError):
            return 0

    def __str__(self):
        user_name = self.user.username if self.user else "Anonymous"
        product_name = self.product.name if self.product else "Unknown Product"
        return f"{user_name} review on {product_name}"  # Fixed NoneType Error


class Variant(models.Model):
    # product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants") 
    name = models.CharField(max_length=1000, verbose_name="Variant Name", null=True, blank=True)

    def items(self):
        return VariantItem.objects.filter(variant=self)

    def __str__(self):
        return self.name if self.name else "Unnamed Variant"

class VariantItem(models.Model):
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE, related_name='variant_items')
    title = models.CharField(max_length=1000, verbose_name="Item Title", null=True, blank=True)
    content = models.CharField(max_length=1000, verbose_name="Item Content", null=True, blank=True)
    image = models.ImageField(upload_to='variant_images/', null=True, blank=True)


    def __str__(self):
        return str(self.variant.name) if self.variant and self.variant.name else "Unnamed Variant Item"
    

class Cart(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(user_models.User, on_delete=models.SET_NULL, null=True, blank=True)
    qty = models.PositiveIntegerField(default=0, null=True, blank=True)
    price = models.DecimalField(decimal_places=2, max_digits=12, default=0.00, null=True, blank=True)
    sub_total = models.DecimalField(decimal_places=2, max_digits=12, default=0.00, null=True, blank=True)
    shipping = models.DecimalField(decimal_places=2, max_digits=12, default=0.00, null=True, blank=True)
    tax = models.DecimalField(decimal_places=2, max_digits=12, default=0.00, null=True, blank=True)
    total = models.DecimalField(decimal_places=2, max_digits=12, default=0.00, null=True, blank=True)
    size = models.CharField(max_length=100, null=True, blank=True)
    color = models.CharField(max_length=100, null=True, blank=True)
    cart_id = models.CharField(max_length=1000, null=True, blank=True)
    date = models.DateTimeField(auto_now_add=True)
    # variant_image = models.ImageField(upload_to='variant_selected/', null=True, blank=True)
    image = models.ImageField(upload_to="cart_images/", null=True, blank=True)


    def __str__(self):
        return f"{self.product.name} ({self.color or 'No Color'}) - Qty: {self.qty}"

    
class Order(models.Model):
    customer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="orders")
    order_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    sub_total = models.DecimalField(default=0.00, max_digits=12, decimal_places=2)
    shipping = models.DecimalField(default=0.00,     max_digits=12, decimal_places=2)
    total = models.DecimalField(default=0.00, max_digits=12, decimal_places=2)
    status = models.CharField(max_length=100, default="Processing") 
     # e.g. Processing, Shipped, Delivered
    tracking_id = models.CharField(max_length=100, null=True, blank=True)

    date = models.DateTimeField(default=timezone.now)
    # In Order model
    payment_status = models.CharField(
        max_length=20,
        choices=[("Pending", "Pending"), ("Paid", "Paid"), ("Failed", "Failed")],
        default="Pending"
    )

    payment_method = models.CharField(
        max_length=50,
        choices=[("COD", "Cash on Delivery"), ("Card", "Credit/Debit Card"), ("UPI", "UPI")],
        default="COD"
    )
    
    payment_id = models.CharField(max_length=100, null=True, blank=True)
    razorpay_order_id = models.CharField(max_length=100, null=True, blank=True)


    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Order {self.order_id} by {self.customer}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True)
    qty = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    sub_total = models.DecimalField(max_digits=12, decimal_places=2)
    color = models.CharField(max_length=100, null=True, blank=True)
    size = models.CharField(max_length=100, null=True, blank=True)
    image = models.ImageField(upload_to="order_images/", null=True, blank=True)


    def __str__(self):
        return f"{self.qty} × {self.product.name} (Order {self.order.order_id})"
    

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')

    def __str__(self):
        return f"{self.user.username} likes {self.product.name}"
