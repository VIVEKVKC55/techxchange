from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404, redirect
from django.core.mail import send_mail
from django.utils.timezone import now
from datetime import timedelta
from django.utils.html import format_html
from django.urls import path, reverse
from .models import Subscription, UserProfile, SubscriptionPlan, PlanType, SubscriptionDuration
from django.conf import settings
from django.contrib.auth.admin import UserAdmin as DefaultUserAdmin
from django.utils.safestring import mark_safe
import secrets
import string
from django.http import HttpResponse
from docx import Document

User = get_user_model()

admin.site.index_title = "TechXchange Dashboard"      # Dashboard subtitle

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
    actions = ["approve_users", "download_filtered_user_data"]  # Add bulk actions

    def user_category(self, obj):
        if hasattr(obj, "subscription"):
            if obj.subscription.plan.name == "Premium (Plan A)":
                return "Premium (Plan A)"
            elif obj.subscription.plan.name == "Premium (Plan B)":
                return "Premium (Plan B)"
            return "Paid User"
        return "Free User"

    user_category.short_description = "User Type"

    def phone_number(self, obj):
        return obj.profile.phone_number if hasattr(obj, "profile") and obj.profile else "N/A"

    phone_number.short_description = "Phone"

    def location(self, obj):
        return obj.profile.location if hasattr(obj, "profile") and obj.profile else "N/A"

    location.short_description = "Location"

    def is_verified(self, obj):
        return obj.profile.is_verified if hasattr(obj, "profile") and obj.profile else False

    is_verified.short_description = "Verified"
    is_verified.boolean = True

    def profile_picture_preview(self, obj):
        if hasattr(obj, "profile") and obj.profile and obj.profile.profile_picture:
            return format_html(f'<img src="{obj.profile.profile_picture.url}" width="40" height="40" style="border-radius:50%;">')
        return "No Image"

    profile_picture_preview.short_description = "Profile Pic"

    @admin.action(description="Approve selected users and send login details")
    def approve_users(self, request, queryset):
        for user in queryset:
            if not user.is_active:
                characters = string.ascii_letters + string.digits + string.punctuation
                default_password = ''.join(secrets.choice(characters) for _ in range(6))
                user.set_password(default_password)
                user.is_active = True
                user.profile.set_password(default_password)
                user.save()

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

    @admin.action(description="Download filtered user data as Excel")
    def download_filtered_user_data(self, request, queryset):
        import openpyxl
        from openpyxl.utils import get_column_letter

        changelist = self.get_changelist_instance(request)
        filtered_queryset = changelist.get_queryset(request)

        workbook = openpyxl.Workbook()
        sheet = workbook.active
        sheet.title = 'Filtered Users'

        headers = [
            "Full Name", "Username", "Email", "User Plan Category", "Phone", "Location",
            "Verified", "Active", "Date Joined"
        ]
        for col_num, header in enumerate(headers, 1):
            col_letter = get_column_letter(col_num)
            sheet[f"{col_letter}1"] = header

        for row_num, user in enumerate(filtered_queryset, 2):
            profile = getattr(user, 'profile', None)
            sheet[f"A{row_num}"] = user.get_full_name() or 'N/A'
            sheet[f"B{row_num}"] = user.username
            sheet[f"C{row_num}"] = user.email
            sheet[f"D{row_num}"] = self.user_category(user)
            sheet[f"E{row_num}"] = getattr(profile, 'phone_number', 'N/A')
            sheet[f"F{row_num}"] = getattr(profile, 'location', 'N/A')
            sheet[f"G{row_num}"] = "Yes" if getattr(profile, 'is_verified', False) else "No"
            sheet[f"H{row_num}"] = "Yes" if user.is_active else "No"
            sheet[f"I{row_num}"] = user.date_joined.strftime('%Y-%m-%d %H:%M')

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        )
        response['Content-Disposition'] = 'attachment; filename=filtered_user_data.xlsx'
        workbook.save(response)
        return response

    def change_view(self, request, object_id, form_url='', extra_context=None):
        user = get_object_or_404(User, pk=object_id)
        decrypted_password = None
        if hasattr(user, "profile") and user.profile and user.profile.encrypted_password:
            try:
                decrypted_password = user.profile.get_password()
            except Exception:
                decrypted_password = "[Could not decrypt password]"

        extra_context = extra_context or {}
        extra_context['decrypted_password'] = decrypted_password
        return super().change_view(request, object_id, form_url, extra_context=extra_context)


# Unregister the default User model if already registered
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


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
            url = reverse('admin:approve_subscription', args=[obj.id])  # ✅ Ensure correct URL
            return mark_safe(
                f'<button class="button approve-btn" data-url="{url}" data-id="{obj.id}" data-amount="{obj.amount_paid}" style="background: green; color: white; padding: 5px 10px; border-radius: 4px;">Approve</button>'
            )
        return "No pending request"

    def reject_button(self, obj):
        if obj.pending_plan:
            url = reverse('admin:reject_subscription', args=[obj.id])  # ✅ Ensure correct URL
            return mark_safe(
                f'<button class="button reject-btn" data-url="{url}" data-id="{obj.id}" style="background: red; color: white; padding: 5px 10px; border-radius: 4px;">Reject</button>'
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