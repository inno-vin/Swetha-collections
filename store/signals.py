from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Order

@receiver(pre_save, sender=Order)
def send_tracking_email(sender, instance, **kwargs):
    # This block prevents the signal from running on a new order creation
    if not instance.pk:
        return

    try:
        previous = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return

    # Option 1: Send an email if the tracking ID has been changed to a new value
    if previous.tracking_id != instance.tracking_id:
        print("✅ Signal triggered! Sending tracking email to:", instance.customer.email)

        # You can modify the subject and message to reflect the update
        if instance.tracking_id:
            subject = f"🚚 Your Order #{instance.order_id} tracking ID has been updated"
            message = f"""
Dear {instance.customer.get_full_name() or instance.customer.username},

The tracking ID for your order #{instance.order_id} has been updated.

🚚 New Tracking ID: {instance.tracking_id}

You can view your updated order details in your account.

Visit:https://www.dtdc.in/trace.asp to track your order.

Thank you for shopping with us!

Regards,
Swetha Collections
"""
        else:
            # Optionally, send a different email if the tracking ID is removed
            subject = f"ℹ️ Your Order #{instance.order_id} tracking ID has been removed"
            message = f"""
Dear {instance.customer.get_full_name() or instance.customer.username},

The tracking ID for your order #{instance.order_id} has been removed. Please contact us for more information.

Regards,
Swetha Collections
"""
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [instance.customer.email],
            fail_silently=False,
        )