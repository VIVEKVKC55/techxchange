from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.core.mail import send_mail
from django.utils.timezone import now
from datetime import timedelta
from django.utils.html import format_html
from django.urls import path
from .models import Subscription, UserProfile, SubscriptionPlan, PlanType, SubscriptionDuration
from django.conf import settings
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin

User = get_user_model()

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "phone_number", "is_verified", "created_at")
    search_fields = ("user__username", "phone_number")
    list_filter = ("is_verified", "created_at")


class CustomUserAdmin(DefaultUserAdmin):
    list_display = (
        "email", "username", "user_category", "phone_number",
        "location", "profile_picture_preview", "is_verified",
        "date_joined", "is_active"
    )
    list_filter = ("subscription__plan", "is_active", "profile__is_verified")
    search_fields = ("email", "username", "profile__phone_number", "profile__location")
    actions = ["approve_users"]  # Add bulk approval option

    def user_category(self, obj):
        """Determine if user is Free or Paid and their plan type."""
        if hasattr(obj, "subscription"):
            if obj.subscription.plan == "premium":
                return "Paid - Category A"
            elif obj.subscription.plan == "scalable":
                return "Paid - Category B"
            return "Paid User"
        return "Free User"
    
    user_category.short_description = "User Type"

    def phone_number(self, obj):
        """Retrieve phone number from UserProfile"""
        return obj.profile.phone_number if hasattr(obj, "profile") and obj.profile else "N/A"
    
    phone_number.short_description = "Phone"

    def location(self, obj):
        """Retrieve location from UserProfile"""
        return obj.profile.location if hasattr(obj, "profile") and obj.profile else "N/A"
    
    location.short_description = "Location"

    def is_verified(self, obj):
        """Check if profile is verified"""
        return obj.profile.is_verified if hasattr(obj, "profile") and obj.profile else False
    
    is_verified.short_description = "Verified"
    is_verified.boolean = True  # Show as a checkbox in admin

    def profile_picture_preview(self, obj):
        """Display Profile Picture in Admin Panel"""
        if hasattr(obj, "profile") and obj.profile and obj.profile.profile_picture:
            return format_html(f'<img src="{obj.profile.profile_picture.url}" width="40" height="40" style="border-radius:50%;">')
        return "No Image"
    
    profile_picture_preview.short_description = "Profile Pic"

    @admin.action(description="Approve selected users and send login details")
    def approve_users(self, request, queryset):
        """Approves selected users and sends them login credentials via email"""
        for user in queryset:
            if not user.is_active:  # Approve only inactive users
                default_password = "123456"  # Default password
                user.set_password(default_password)  # Set default password
                user.is_active = True
                user.save()

                # Send email with login details
                subject = "Your Account is Approved!"
                message = f"""
                Dear {user.first_name},

                Your account has been approved by the admin.

                You can now log in with the following details:

                Email: {user.email}
                Password: {default_password}

                Please change your password after logging in.

                Thank you!
                """
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

        self.message_user(request, "Selected users have been approved and notified via email.")

# Unregister the default User model if already registered
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


from django.utils.safestring import mark_safe

class SubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        "user", "approve_button", "amount_paid", "plan", "duration_days", "is_approved", 
        "pending_plan", "pending_duration", "start_date", "end_date", 
        "reject_button"
    )
    list_filter = ("plan", "is_approved")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('approve/<int:subscription_id>/', self.admin_site.admin_view(self.approve_subscription), name="approve_subscription"),
            path('reject/<int:subscription_id>/', self.admin_site.admin_view(self.reject_subscription), name="reject_subscription"),
        ]
        return custom_urls + urls

    def approve_subscription(self, request, subscription_id):
        subscription = get_object_or_404(Subscription, id=subscription_id)

        if subscription.amount_paid <= 0:  # ✅ Check if payment is collected
            messages.error(request, "Cannot approve. Payment not received yet.")
            return redirect('/admin/customer/subscription/')

        if subscription.pending_plan and subscription.pending_duration:
            plan_type = subscription.pending_plan
            duration = subscription.pending_duration

            try:
                subscription_plan = SubscriptionPlan.objects.get(plan_type=plan_type, duration_days=duration)
            except SubscriptionPlan.DoesNotExist:
                messages.error(request, "The selected plan-duration combination is invalid.")
                return redirect('/admin/customer/subscription/')

            subscription.plan = plan_type
            subscription.duration_days = duration
            subscription.start_date = now()
            subscription.end_date = now() + timedelta(days=duration.duration_days)
            subscription.is_approved = True
            
            # Clear pending request fields
            subscription.pending_plan = None
            subscription.pending_duration = None
            subscription.save()

            send_mail(
                "Subscription Approved",
                f"Dear {subscription.user.username},\n\n"
                f"Your subscription has been upgraded to {plan_type.name} for {duration.duration_days} days at ${subscription_plan.price}.\n\n"
                "Best Regards,\nSupport Team",
                "support@example.com",
                [subscription.user.email],
                fail_silently=True,
            )

            messages.success(request, f"Subscription for {subscription.user.username} approved successfully!")
        return redirect('/admin/customer/subscription/')

    def reject_subscription(self, request, subscription_id):
        subscription = get_object_or_404(Subscription, id=subscription_id)
        if subscription.pending_plan:
            subscription.pending_plan = None
            subscription.pending_duration = None
            subscription.is_approved = False
            subscription.save()

            send_mail(
                "Subscription Upgrade Rejected",
                f"Dear {subscription.user.username},\n\n"
                "Your subscription upgrade request was rejected.\n\n"
                "Best Regards,\nSupport Team",
                "support@example.com",
                [subscription.user.email],
                fail_silently=True,
            )

            messages.warning(request, f"Subscription for {subscription.user.username} rejected.")
        return redirect('/admin/customer/subscription/')

    def approve_button(self, obj):
        if obj.pending_plan:
            return mark_safe(
                f'<button class="button approve-btn" data-id="{obj.id}" data-amount="{obj.amount_paid}">Approve</button>'
            )
        return "No pending request"

    def reject_button(self, obj):
        if obj.pending_plan:
            return mark_safe(
                f'<button class="button reject-btn" style="color: red;" data-id="{obj.id}">Reject</button>'
            )
        return "No pending request"

    approve_button.short_description = "Approve"
    reject_button.short_description = "Reject"

    class Media:
        js = ("admin/js/sweetalert2.min.js", "admin/js/subscription_actions.js")  # ✅ Load JavaScript for SweetAlert

admin.site.register(Subscription, SubscriptionAdmin)




@admin.register(PlanType)
class PlanTypeAdmin(admin.ModelAdmin):
    """Admin configuration for subscription plan types."""
    list_display = ("name", "max_products_per_day", "base_slots", "max_product_views_per_day")
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(SubscriptionDuration)
class SubscriptionDurationAdmin(admin.ModelAdmin):
    """Admin configuration for subscription durations."""
    list_display = ("duration_days",)
    ordering = ("duration_days",)


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    """Admin configuration for subscription plans (mapping plan type & duration)."""
    list_display = ("plan_type", "duration_days", "price")
    list_filter = ("plan_type", "duration_days")
    search_fields = ("plan_type__name",)
    ordering = ("plan_type", "duration_days")