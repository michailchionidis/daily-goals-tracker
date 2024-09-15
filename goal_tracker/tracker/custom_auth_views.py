from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.template.loader import render_to_string

User = get_user_model()

def custom_password_reset(request):
    if request.method == "POST":
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            user = User.objects.filter(email=email).first()
            if user:
                subject = "Password Reset Requested"
                email_template_name = "registration/password_reset_email.html"
                c = {
                    "email": user.email,
                    'domain': request.META['HTTP_HOST'],
                    'site_name': 'Your Site',
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "user": user,
                    'token': default_token_generator.make_token(user),
                    'protocol': 'http',
                }
                email = render_to_string(email_template_name, c)
                send_mail(subject, email, 'admin@example.com', [user.email], fail_silently=False)
            return redirect("password_reset_done")
    else:
        form = PasswordResetForm()
    return render(request, "registration/password_reset_form.html", {"form": form})

def custom_password_reset_done(request):
    return render(request, "registration/password_reset_done.html")

def custom_password_reset_confirm(request, uidb64, token):
    # Εδώ θα πρέπει να υλοποιήσετε τη λογική για την επιβεβαίωση του token
    # και την αλλαγή του κωδικού. Για απλότητα, απλά κάνουμε render το template.
    return render(request, "registration/password_reset_confirm.html")

def custom_password_reset_complete(request):
    return render(request, "registration/password_reset_complete.html")