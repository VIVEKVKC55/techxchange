from django.shortcuts import render
from catalog.models import Category
from .models import PromotionBanner

def home_page(request):
    categories = Category.objects.filter(is_active=True, include_in_home=True).order_by("id")
    promotion_banners = PromotionBanner.objects.filter(is_active=True)[:4]  # Fetch only 4 active banners
    return render(request, 'default/home/home.html', {'categories': categories, 'promotion_banners': promotion_banners})
