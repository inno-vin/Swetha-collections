from django.contrib import admin
from store import models as store_models
from .models import Order, OrderItem

from .models import OrderCancellation
# Inline Gallery to appear inside Product Admin
class GalleryInline(admin.TabularInline):  
    model = store_models.Gallery
    extra = 1  

class VariantInline(admin.TabularInline):
    model=store_models.Variant

class VariantItemInline(admin.TabularInline):
    model=store_models.VariantItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'qty', 'price', 'sub_total')

# Category Admin
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['title', 'image']
    list_editable = ['image']
    prepopulated_fields = {'slug': ('title',)}

# Product Admin
class ProductAdmin(admin.ModelAdmin):
    def category_title(self, obj):
        return obj.category.title if obj.category else "No Category"
    
    category_title.admin_order_field = 'category__title'
    category_title.short_description = 'Category'

    def get_gallery_id(self, obj):
        """Display Gallery IDs for a Product"""
        galleries = obj.gallery.all()  # Corrected related name reference
        return ", ".join(str(g.id) for g in galleries) if galleries else "No Gallery"

    get_gallery_id.short_description = "Gallery ID"

    list_display = ['name', 'category_title', 'price', 'regular_price', 'stock', 'status', 'feature', 'date', 'get_gallery_id']
    list_display_links = ['name']
    list_editable = ['price', 'stock', 'status', 'feature']
    search_fields = ['name', 'category__title']
    list_filter = ['status', 'feature', 'category']
    inlines = [GalleryInline]  # Gallery appears as an inline
    prepopulated_fields = {'slug': ('name',)}

# Review Admin
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'rating', 'active', 'date']
    search_fields = ['user__username', 'product__name']
    list_filter = ['active', 'rating']

# Gallery Admin (to show Gallery separately)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ['id', 'product', 'image']
    search_fields = ['product__name', 'id']

class VariantAdmin(admin.ModelAdmin):
    list_display = ['product','name']
    search_fields = ['product__name','name',]
    inlines = [VariantItemInline]

class VariantItemAdmin(admin.ModelAdmin):
    list_display=['variant','title','content']
    search_fields=['variant__name','title']

class CartAdmin(admin.ModelAdmin):
    list_display=['cart_id','product','user','qty','price','total','date']
    search_fields=['cart_id','product__name','user__username']
    list_filter=['date','product']

class OrderAdmin(admin.ModelAdmin):
   
    list_display = ('order_id', 'customer', 'status', 'tracking_id', 'total', 'date')
    search_fields = ('order_id', 'customer__username', 'tracking_id')
    list_filter = ('status', 'date')
    inlines = [OrderItemInline]




@admin.register(OrderCancellation)
class OrderCancellationAdmin(admin.ModelAdmin):
    list_display = ("order", "action", "created_at")
    search_fields = ("order__order_id", "refund_upi_id", "refund_bank_ifsc")


# Register Models in Django Admin
admin.site.register(store_models.Category, CategoryAdmin)
admin.site.register(store_models.Product, ProductAdmin)
admin.site.register(store_models.Review, ReviewAdmin)
admin.site.register(store_models.Gallery, GalleryAdmin)  # Register Gallery properly
admin.site.register(store_models.Variant,VariantAdmin)
admin.site.register(store_models.Cart,CartAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem)
