from django.urls import path
from .views import ProductCreateView, ProductListView, ProductDetailView, delete_product

app_name="catalog"

urlpatterns = [
    path("create/", ProductCreateView.as_view(), name="product_create"),
    path("list/", ProductListView.as_view(), name="product_list"),
    path("delete-product/<int:product_id>/", delete_product, name="delete_product"),
    path("<str:cat_slug>/<int:pk>/", ProductDetailView.as_view(), name="product_detail"),
]
