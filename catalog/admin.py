from django.contrib import admin
from .models import Category, Product, ProductImage

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'include_in_home', 'is_active', 'created', 'created_by')  # Display these fields
    list_filter = ('is_active', 'include_in_home', 'created')  # Add filters
    search_fields = ('name', 'slug')  # Enable search
    prepopulated_fields = {'slug': ('name',)}  # Auto-fill slug based on name
    ordering = ('-created',)  # Order by newest first
    readonly_fields = ('created', 'updated')  # Prevent editing timestamps

    def save_model(self, request, obj, form, change):
        """Automatically set created_by and updated_by"""
        if not obj.created_by:
            obj.created_by = request.user  # Set created_by only when first created
        obj.updated_by = request.user  # Update updated_by on every save
        super().save_model(request, obj, form, change)

class ProductImageInline(admin.TabularInline):  # Show images inline
    model = ProductImage
    extra = 1  # Allow adding one extra image field

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "brand", "category", "is_active", "created_at", "created_by")
    search_fields = ("name", "brand", "category__name")
    list_filter = ("category", "is_active", "created_at")
    ordering = ("-created_at",)
    inlines = [ProductImageInline]  # Show images inside Product Admin
