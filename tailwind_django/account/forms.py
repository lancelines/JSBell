from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import CustomUser
from inventory.models import Warehouse

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            CustomUser.objects.create(
                user=user,
                role=self.cleaned_data['role']
            )
        return user

class UserLoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

class WarehouseAssignmentForm(forms.Form):
    warehouses = forms.ModelMultipleChoiceField(
        queryset=Warehouse.objects.all(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-multiselect block w-full py-2 px-3 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm'
        }),
        required=False,
        label='Assign Warehouses'
    )

class PermissionsForm(forms.Form):
    # Inventory permissions
    can_add_inventory = forms.BooleanField(required=False, label='Add Inventory')
    can_change_inventory = forms.BooleanField(required=False, label='Change Inventory')
    can_delete_inventory = forms.BooleanField(required=False, label='Delete Inventory')
    can_view_inventory = forms.BooleanField(required=False, label='View Inventory')
    
    # Brand permissions
    can_add_brand = forms.BooleanField(required=False, label='Add Brand')
    can_change_brand = forms.BooleanField(required=False, label='Change Brand')
    can_delete_brand = forms.BooleanField(required=False, label='Delete Brand')
    can_view_brand = forms.BooleanField(required=False, label='View Brand')
    
    # Category permissions
    can_add_category = forms.BooleanField(required=False, label='Add Category')
    can_change_category = forms.BooleanField(required=False, label='Change Category')
    can_delete_category = forms.BooleanField(required=False, label='Delete Category')
    can_view_category = forms.BooleanField(required=False, label='View Category')
    
    # Requisition permissions
    can_add_requisition = forms.BooleanField(required=False, label='Add Requisition')
    can_change_requisition = forms.BooleanField(required=False, label='Change Requisition')
    can_delete_requisition = forms.BooleanField(required=False, label='Delete Requisition')
    can_view_requisition = forms.BooleanField(required=False, label='View Requisition')
    can_approve_requisition = forms.BooleanField(required=False, label='Approve Requisition')