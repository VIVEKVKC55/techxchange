from django.db import models
from django.contrib.auth.models import User
from catalog.models import Product
from django.utils.timezone import now
from datetime import timedelta
from storages.backends.s3boto3 import S3Boto3Storage
import logging
logger = logging.getLogger(__name__)

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    profile_picture = models.ImageField(upload_to="profile_pictures/", storage=S3Boto3Storage(), blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    location = models.TextField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def delete(self, *args, **kwargs):
        """Delete profile picture from S3 when the UserProfile is deleted"""
        if self.profile_picture:
            try:
                self.profile_picture.delete(save=False)
            except Exception as e:
                # Log the error but continue with deletion
                logger.error(f"Failed to delete profile picture from S3: {str(e)}")
        super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
class PlanType(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)  # e.g., 'Premium A', 'Premium B'
    max_products_per_day = models.PositiveIntegerField(default=1)  # Default 1 for free users
    base_slots = models.PositiveIntegerField(default=0)  # Extra slots for scalable users
    max_product_views_per_day = models.PositiveIntegerField(default=5)  # Default 5 for free users (∞ for premium)

    def __str__(self):
        return self.name


class SubscriptionDuration(models.Model):
    duration_days = models.PositiveIntegerField(unique=True)  # e.g., 30, 180, 365

    def __str__(self):
        return f"{self.duration_days} Days"
    

class SubscriptionPlan(models.Model):
    plan_type = models.ForeignKey(PlanType, on_delete=models.CASCADE)  # Dynamic plan type
    duration_days = models.ForeignKey(SubscriptionDuration, on_delete=models.CASCADE)  # Dynamic duration
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.plan_type.name} - {self.duration_days.duration_days} Days - ${self.price}"


class Subscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    plan = models.ForeignKey(PlanType, on_delete=models.SET_NULL, null=True, blank=True)  # Active plan
    duration_days = models.ForeignKey(SubscriptionDuration, on_delete=models.SET_NULL, null=True, blank=True)  # Active duration
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    extra_slots = models.PositiveIntegerField(default=0)  # Purchased slots
    start_date = models.DateTimeField(default=now)
    end_date = models.DateTimeField(blank=True, null=True)  # Nullable for Basic plan
    is_approved = models.BooleanField(default=False)  # Approval status
    
    # ✅ Store pending upgrade request properly
    pending_plan = models.ForeignKey(PlanType, on_delete=models.SET_NULL, null=True, blank=True, related_name="pending_subscriptions")
    pending_duration = models.ForeignKey(SubscriptionDuration, on_delete=models.SET_NULL, null=True, blank=True, related_name="pending_subscriptions")

    def save(self, *args, **kwargs):
        """Apply pending upgrades only when approved."""
        if self.is_approved and self.pending_plan and self.pending_duration:
            self.plan = self.pending_plan
            self.duration_days = self.pending_duration
            self.start_date = now()
            self.end_date = now() + timedelta(days=self.duration_days.duration_days)  # Get actual days from model
            self.pending_plan = None  # Clear pending request
            self.pending_duration = None
        super().save(*args, **kwargs)

    def is_active(self):
        """Check if the subscription is still valid and approved."""
        if not self.plan:
            return True  # Basic users are always active
        return self.end_date is None or self.end_date >= now()  # Check expiration

    def remaining_days(self):
        """Calculate remaining days if end_date exists."""
        if self.end_date:
            delta = (self.end_date - now()).days
            return max(delta, 0)  # Avoid negative values
        return "Unlimited"

    def __str__(self):
        return f"{self.user.username} - {self.plan.name if self.plan else 'Basic'} ({self.duration_days.duration_days if self.duration_days else 'Free'})"



class ProductView(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="viewed_products")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="user_views")
    viewed_at = models.DateTimeField(default=now)

    class Meta:
        unique_together = ("user", "product")  # Prevent duplicate views per user per product

    def __str__(self):
        return f"{self.user.username} viewed {self.product.name}"
