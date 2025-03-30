# -*- coding: utf-8 -*-

# /**
# * @package: Catalog
# * @copyright: 2025. All rights reserved.
# * @author: VIVEK CHAUHAN
# * @license: Proprietary and confidential, Unauthorized
# * copying of this file, via any medium is strictly prohibited
# */

from django import forms
from .models import Product, Category
from tinymce.widgets import TinyMCE

class ProductForm(forms.ModelForm):
    specification = forms.CharField(widget=TinyMCE())

    description = forms.CharField(widget=TinyMCE())

    class Meta:
        model = Product
        fields = ['name', 'category', 'brand', 'specification', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product Name'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'brand': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product Brand'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
