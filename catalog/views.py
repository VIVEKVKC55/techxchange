from django.views.generic import CreateView, ListView, DetailView, View
from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from .models import Category, Product, ProductImage
from .forms import ProductForm
from django.db.models import Q
from django.contrib import messages
from django.utils.timezone import now, timedelta
from django.http import JsonResponse
from customer.models import ProductView  # Import the new model
from django.contrib.auth.decorators import login_required



class ProductCreateView(LoginRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = "default/catalog/product_form.html"
    success_url = reverse_lazy("user:user-products")  # Update with the actual URL name

    def get_max_products(self, user):
        """Returns the max number of products a user can add in 24 hours based on their plan."""
        if hasattr(user, 'subscription') and user.subscription.plan:
            plan = user.subscription.plan
            max_limit = plan.max_products_per_day  # Fetch limit from PlanType

            # ✅ Extra slots apply to all plans
            max_limit += user.subscription.extra_slots  

            return max_limit  # Final dynamic limit
        return 1  # Default limit for free users

    def form_valid(self, form):
        # print('form', form.data)
        user = self.request.user
        time_threshold = now() - timedelta(hours=24)
        recent_product_count = Product.objects.filter(created_by=user, created_at__gte=time_threshold).count()
        max_products = self.get_max_products(user)

        # Check if the user has exceeded their limit
        if recent_product_count >= max_products:
            messages.error(
                self.request, 
                f"You have reached your daily limit of {max_products} products. "
                "Buy more slots or upgrade your plan."
            )
            return redirect("user:subscription_upgrade")  # Redirect to slot purchase page

        # Save product with logged-in user
        product = form.save(commit=False)
        product.created_by = user
        product.save()
        
        # Handling multiple images
        images = self.request.FILES.getlist("images")
        for image in images:
            ProductImage.objects.create(product=product, image=image)

        messages.success(self.request, "Product added successfully!")
        return redirect(self.success_url)


class ProductListView(LoginRequiredMixin, ListView):
    model = Product
    template_name = "default/catalog/product_list.html"
    context_object_name = "products"

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        query = self.request.GET.get("q")
        category_slug = self.request.GET.get("category")

        if query:
            queryset = queryset.filter(
                Q(name__icontains=query) |
                Q(brand__icontains=query) |
                Q(specification__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query)
            )

        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Category.objects.all()
        context["query"] = self.request.GET.get("q", "")
        context["category"] = self.request.GET.get("category", "")
        context["selected_category"] = self.request.GET.get("category", "")
        return context


class ProductDetailView(LoginRequiredMixin, DetailView):
    model = Product
    template_name = "default/catalog/product_detail.html"
    context_object_name = "product"

    def get_queryset(self):
        return Product.objects.filter(is_active=True)

    def get_max_views(self, user):
        """Returns the max number of product views allowed per day based on the user's plan."""
        if hasattr(user, 'subscription') and user.subscription.plan:
            plan = user.subscription.plan
            max_views = plan.max_product_views_per_day  # Get from PlanType

            return float('inf') if max_views == 0 else max_views  # If max_views = 0, allow unlimited
        return 5  # Default limit for free users

    def get(self, request, *args, **kwargs):
        product = self.get_object()
        user = request.user
        time_threshold = now() - timedelta(hours=24)
        # Check if the user has already viewed this product
        existing_view = ProductView.objects.filter(user=user, product=product).first()

        if not existing_view:
            # Count total views within the last 24 hours
            recent_views_count = ProductView.objects.filter(user=user, viewed_at__gte=time_threshold).count()
            max_views = self.get_max_views(user)

            # If limit is reached, return error JSON if AJAX, otherwise show message
            if recent_views_count >= max_views:
                if request.headers.get("X-Requested-With") == "XMLHttpRequest":
                    return JsonResponse({"error": f"You have reached your daily limit of {max_views} product views."}, status=403)
                messages.error(request, f"You have reached your daily limit of {max_views} product views.")
                return self.render_to_response(self.get_context_data())  # Render the same page

        # Store or update the product view in the database
        ProductView.objects.update_or_create(
            user=user, product=product,
            defaults={"viewed_at": now()}  # Always update the timestamp
        )

        # Check if the request is an AJAX request
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return JsonResponse({"redirect_url": request.path})  # Return JSON response with redirect URL

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        """Pass viewed products (last 24 hours) to the template."""
        context = super().get_context_data(**kwargs)
        time_threshold = now() - timedelta(hours=24)
        viewed_products = Product.objects.filter(user_views__user=self.request.user, user_views__viewed_at__gte=time_threshold)
        context["viewed_products"] = viewed_products
        return context

@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    
    if request.method == "POST":
        product.delete()
        return JsonResponse({"success": True})
    
    return JsonResponse({"success": False, "error": "Invalid request method."}, status=400)

