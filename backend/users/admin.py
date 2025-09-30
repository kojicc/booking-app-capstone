from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django import forms
from .models import User


class SimpleUserCreationForm(forms.ModelForm):
    """A lightweight user creation form for the admin that accepts a
    plain-text password and sets it correctly on save. This avoids the
    more heavyweight password1/password2 flow while still providing a
    friendly admin experience.
    """
    password = forms.CharField(label='Password', required=False, widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'role', 'password')

    def save(self, commit=True):
        user = super().save(commit=False)
        raw_password = self.cleaned_data.get('password')
        if raw_password:
            user.set_password(raw_password)
        if commit:
            user.save()
            self.save_m2m()
        return user


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    # Use Django's default forms; username is optional on the model
    model = User
    list_display = ("id", "email", "username", "role", "is_staff")
    list_display_links = ("email", "username")
    list_editable = ("role",)
    list_filter = ("role", "is_staff")
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("first_name", "last_name", "username")} ),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")} ),
        ("Important dates", {"fields": ("last_login", "date_joined")} ),
    )
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            # Use a simple set of fields for creating users in admin. Django's
            # default admin uses custom creation forms that include password1/password2.
            # Since we removed the temporary custom forms, use a single 'password' field
            # and allow the admin to set it via the user change form if needed.
            "fields": ("email", "username", "first_name", "last_name", "role", "password"),
        }),
    )
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("email",)
    readonly_fields = ("last_login", "date_joined")
    list_per_page = 25
    add_form = SimpleUserCreationForm

    def get_form(self, request, obj=None, **kwargs):
        # Use our simpler add form when creating a new user in admin
        defaults = {}
        if obj is None:
            defaults['form'] = self.add_form
        defaults.update(kwargs)
        return super().get_form(request, obj, **defaults)

    def save_model(self, request, obj, form, change):
        # If password supplied in the simple form, it's already set in form.save();
        # otherwise, if an admin left password blank on creation, keep it unset.
        super().save_model(request, obj, form, change)
