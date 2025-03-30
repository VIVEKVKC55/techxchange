from django.views.generic import TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from catalog.models import Product
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from django.views import View
from django.shortcuts import render, redirect, get_object_or_404
from customer.models import ProductView, Subscription, SubscriptionPlan, PlanType, SubscriptionDuration
from django.http import JsonResponse
from django.utils.timezone import now
from django.contrib import messages


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "default/customer/dashboard/profile.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page'] = 'profile'
        return context


class UserProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = "default/customer/dashboard/products.html"
    context_object_name = "products"

    def get_queryset(self):
        return Product.objects.filter(created_by=self.request.user)

class CustomPasswordChangeView(SuccessMessageMixin, PasswordChangeView):
    template_name = "default/customer/dashboard/change_password.html"  # Update with your template path
    success_url = reverse_lazy("user:profile")  # Redirect to profile page after password change
    success_message = "Your password has been successfully updated!"


class UserViewedProductsView(LoginRequiredMixin, View):
    def get(self, request):
        """Retrieve products the logged-in user has viewed."""
        viewed_products = Product.objects.filter(user_views__user=request.user).distinct()

        return render(request, "default/customer/dashboard/viewed_products.html", {"viewed_products": viewed_products})


class UsersWhoViewedMyProductsView(LoginRequiredMixin, View):
    def get(self, request):
        """Retrieve users who have viewed my products."""
        my_products = Product.objects.filter(created_by=request.user)
        product_views = ProductView.objects.filter(product__in=my_products).select_related("user", "product")

        user_product_views = {}
        for view in product_views:
            if view.product not in user_product_views:
                user_product_views[view.product] = []
            user_product_views[view.product].append(view.user)

        return render(request, "default/customer/dashboard/users_who_viewed_my_products.html", {"user_product_views": user_product_views})


class SubscriptionUpgradeView(LoginRequiredMixin, View):
    template_name = "default/customer/dashboard/upgrade.html"

    def get(self, request, *args, **kwargs):
        user = request.user

        # Ensure user has a subscription, if not assign Basic Plan
        subscription, created = Subscription.objects.get_or_create(
            user=user,
            defaults={
                "plan": PlanType.objects.get(id=1),  # Assign Basic Plan
                "duration_days": None,
                "amount_paid": 0,
                "start_date": now(),
                "end_date": None,  # Unlimited for Basic
                "is_approved": True,
            }
        )

        # Fetch all plan types except 'Basic' (ID=1)
        plans = PlanType.objects.exclude(id=1)
        premium_plans = plans.get(name="Premium (Plan A)")

        # Fetch all available subscription durations
        durations = SubscriptionDuration.objects.all()

        # Fetch subscription prices
        plan_prices = {}
        for plan in plans:
            prices = {dur.duration_days: "-" for dur in durations}  # Default "-"
            for sub_plan in SubscriptionPlan.objects.filter(plan_type=plan):
                prices[sub_plan.duration_days.duration_days] = sub_plan.price
            plan_prices[plan.name] = prices

        context = {
            "subscription": subscription,
            "plans": plans,
            "premium_plans": premium_plans,
            "durations": durations,
            "plan_prices": plan_prices,
        }
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        """Handles plan upgrade request"""
        user = request.user
        plan_id = request.POST.get("plan")
        duration_id = request.POST.get("duration")

        if not plan_id or not duration_id:
            messages.error(request, "Invalid plan or duration selection.")
            return redirect("user:subscription_upgrade")  # Replace with your actual URL name

        # Get selected plan and duration
        plan = get_object_or_404(PlanType, id=plan_id)
        duration = get_object_or_404(SubscriptionDuration, id=duration_id)

        # Fetch price from SubscriptionPlan table
        subscription_plan = SubscriptionPlan.objects.filter(plan_type=plan, duration_days=duration).first()
        if not subscription_plan:
            messages.error(request, "Selected plan and duration not available.")
            return redirect("user:subscription_upgrade")  # Replace with your actual URL name

        # Update subscription
        subscription = Subscription.objects.get(user=user)
        subscription.pending_plan = plan  # Set pending plan
        subscription.pending_duration = duration
        subscription.amount_paid = subscription_plan.price
        subscription.is_approved = False  # Await admin approval
        subscription.save()

        messages.success(request, "Upgrade request submitted successfully!")
        return redirect("user:subscription_upgrade")  # Replace with your actual URL name


def get_plan_price(request):
    plan_id = request.GET.get("plan_id")
    duration_id = request.GET.get("duration_id")

    if not plan_id or not duration_id:
        return JsonResponse({"error": "Invalid selection"}, status=400)

    try:
        # Ensure valid PlanType and SubscriptionDuration exist
        plan = get_object_or_404(PlanType, id=plan_id)
        duration = get_object_or_404(SubscriptionDuration, id=duration_id)

        # Fetch price from SubscriptionPlan
        subscription_plan = SubscriptionPlan.objects.filter(
            plan_type=plan, duration_days=duration
        ).first()

        if subscription_plan:
            return JsonResponse({"price": float(subscription_plan.price)})
        else:
            return JsonResponse({"price": "Not Available"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


