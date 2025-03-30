from django import forms
from .models import Subscription, PlanType, SubscriptionDuration, SubscriptionPlan

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
