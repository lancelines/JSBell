from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from inventory.models import Warehouse

class RegistrationForm(UserCreationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_tailwind_classes()

    def apply_tailwind_classes(self):
        for field in self.fields.values():
            field.widget.attrs['class'] = 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

class AddAccountForm(UserCreationForm):
    ROLE_CHOICES = [
        ('manager', 'Manager'),
        ('attendance', 'Attendance'),
        ('admin', 'Admin'),
    ]
    role = forms.ChoiceField(choices=ROLE_CHOICES)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_tailwind_classes()

    def apply_tailwind_classes(self):
        for field in self.fields.values():
            field.widget.attrs['class'] = 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'role')

class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
        'placeholder': 'Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'appearance-none block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm',
        'placeholder': 'Password'
    }))

class PermissionManagementForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        checkbox_class = 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
        for field in self.fields.values():
            field.widget.attrs['class'] = checkbox_class

    can_add_inventory = forms.BooleanField(required=False)
    can_change_inventory = forms.BooleanField(required=False)
    can_delete_inventory = forms.BooleanField(required=False)
    can_view_inventory = forms.BooleanField(required=False)
    can_add_brand = forms.BooleanField(required=False)
    can_add_category = forms.BooleanField(required=False)
    can_add_warehouse = forms.BooleanField(required=False)
    can_change_warehouse = forms.BooleanField(required=False)
    can_delete_warehouse = forms.BooleanField(required=False)
    can_view_warehouse = forms.BooleanField(required=False)

class WarehouseAssignmentForm(forms.Form):
    warehouses = forms.ModelMultipleChoiceField(
        queryset=Warehouse.objects.all(),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded'
        }),
        required=False
    )