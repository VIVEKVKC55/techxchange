from django import forms
from .models import Subscription, PlanType, SubscriptionDuration, SubscriptionPlan, PaymentRecord
from catalog.models import Category

class SubscriptionUpgradeForm(forms.ModelForm):
    plan = forms.ModelChoiceField(queryset=PlanType.objects.all(), required=True, label="Plan Type")
    duration = forms.ModelChoiceField(queryset=SubscriptionDuration.objects.all(), required=True, label="Subscription Duration")

    class Meta:
        model = Subscription
        fields = ["plan", "duration"]

    def clean(self):
        cleaned_data = super().clean()
        plan = cleaned_data.get("plan")
        duration = cleaned_data.get("duration")

        if not plan or not duration:
            raise forms.ValidationError("Both plan type and duration are required.")

        # Validate if the selected plan-duration combination exists in SubscriptionPlan
        if not SubscriptionPlan.objects.filter(plan_type=plan, duration_days=duration).exists():
            raise forms.ValidationError("Invalid plan and duration combination.")

        return cleaned_data


class PaymentRecordEmailForm(forms.ModelForm):
    class Meta:
        model = PaymentRecord
        fields = '__all__'


BUSINESS_TYPE_CHOICES = [
    ("importer", "Importer"),
    ("trader", "Trader"),
    ("both", "Both"),
]

class RegistrationForm(forms.Form):
    name = forms.CharField(max_length=255, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Owner's Name"}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': "Email ID"}))
    phone_number = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Mobile Number"}))
    address = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Address"}))
    business_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Business Name"}))
    business_location = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'id': 'business_location', 'placeholder': 'Business Location'}))
    latitude = forms.FloatField(required=False, widget=forms.HiddenInput(attrs={'id': 'latitude'}))
    longitude = forms.FloatField(required=False, widget=forms.HiddenInput(attrs={'id': 'longitude'}))
    business_type = forms.ChoiceField(choices=BUSINESS_TYPE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    dealing_with = forms.ModelMultipleChoiceField(
    queryset=Category.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        required=True
    )
