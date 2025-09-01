from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.urls import reverse, reverse_lazy
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.hashers import make_password
from .models import UserProfile, BusinessProfile
from django.http import JsonResponse
import logging
logger = logging.getLogger(__name__)

Customer = get_user_model()

def register(request):
    if request.method == "POST":
        name = request.POST["name"] 
        email = request.POST["email"]
        phone_number = request.POST.get("phone_number", "")
        address = request.POST.get("address", "")
        business_location = request.POST.get("business_location", "")
        business_name = request.POST.get("business_name", "")
        business_type = request.POST.get("business_type", "")
        dealing_with = request.POST.get("dealing_with", "")

        if Customer.objects.filter(email=email).exists():
            messages.error(request, "Email already in use!")
            return redirect("user:register")

        # Split full name into first and last name
        name_parts = name.strip().split(" ", 1)  # Split at first space
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""  # Handle cases where there's only a first name

        # Create user with is_active=False (User needs admin approval)
        user = Customer.objects.create_user(username=email, email=email, password="")  # No password initially
        user.first_name = first_name
        user.last_name = last_name
        user.is_active = False  # User is inactive until admin approval
        user.save()

        # Create associated UserProfile
        UserProfile.objects.create(
            user=user,
            phone_number=phone_number,
            address=address,
            is_verified=False  # Verification status remains false initially
        )

        BusinessProfile.objects.create(
            user=user,
            business_name=business_name,
            business_type=business_type,
            dealing_with=dealing_with,
            business_location=business_location
        )

        # ✅ Send email to admin
        subject = "New User Registration Pending Approval"
        message = f"""A new user has registered and requires admin approval.
                    Name: {name}
                    Email: {email}
                    Phone: {phone_number}
                    Address: {address}
                    You can activate the account in the admin panel."""

        admin_email = settings.DEFAULT_FROM_EMAIL  # Or use a fixed email like 'admin@example.com'
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [admin_email])

        messages.success(request, "Registration successful! Admin approval is required before activation.")
        return redirect("user:login")

    return render(request, "default/customer/register.html")



def user_login(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful!")

            # Check if there is a 'next' parameter, otherwise default to home
            next_url = request.GET.get('next', reverse_lazy('home:home'))
            return redirect(next_url)  # Redirect to the original page or home
        else:
            messages.error(request, "Invalid username or password")

    return render(request, "default/customer/login.html")


@login_required
def user_logout(request):
    logout(request)
    messages.success(request, "Logout successful!")
    return redirect("user:login")

def forgot_password_request(request):
    if request.method == "POST":
        email = request.POST.get("email")
        try:
            user = Customer.objects.get(email=email)
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            reset_link = request.build_absolute_uri(reverse("user:reset_password", kwargs={"uidb64": uid, "token": token}))

            # Send email with reset link
            send_mail(
                "Password Reset Link",
                f"Click the link below to reset your password:\n{reset_link}",
                "no-reply@yourdomain.com",
                [user.email],
                fail_silently=False,
            )

            messages.success(request, "Password reset link sent to your email.")
            return redirect("user:login")

        except Customer.DoesNotExist:
            messages.error(request, "No account found with this email.")

    return render(request, "default/customer/forgot_password.html")

def reset_password(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Customer.objects.get(pk=uid)

        if not default_token_generator.check_token(user, token):
            messages.error(request, "Invalid or expired password reset link.")
            return redirect("user:forgot_password")

    except (TypeError, ValueError, OverflowError, Customer.DoesNotExist):
        messages.error(request, "Invalid request.")
        return redirect("user:forgot_password")

    if request.method == "POST":
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return redirect(request.path)

        user.password = make_password(password)  # Hash password
        user.profile.set_password(confirm_password)
        user.save()

        messages.success(request, "Password reset successful. You can now log in.")
        return redirect("user:login")

    return render(request, "default/customer/reset_password.html")

@login_required
def upload_profile_picture(request):
    """Handles user profile picture upload and update"""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"}, status=400)

    if not request.FILES.get("profile_picture"):
        return JsonResponse({"success": False, "error": "No file uploaded"}, status=400)

    profile_picture = request.FILES["profile_picture"]
    user = request.user

    try:
        # Get or create user profile
        profile, created = UserProfile.objects.get_or_create(user=user)
        
        # Delete old profile picture if exists
        if profile.profile_picture:
            try:
                profile.profile_picture.delete(save=False)
            except Exception as e:
                logger.error(f"Failed to delete old profile picture: {str(e)}")

        # Save new profile picture
        profile.profile_picture = profile_picture
        profile.save()

        return JsonResponse({
            "success": True, 
            "image_url": profile.profile_picture.url
        })

    except Exception as e:
        logger.error(f"Profile picture upload error: {str(e)}")
        return JsonResponse({
            "success": False, 
            "error": "An error occurred while updating your profile picture"
        }, status=500)