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
        role = self.cleaned_data['role']
        
        if commit:
            user.save()
            custom_user = CustomUser.objects.create(
                user=user,
                role=role
            )
            
            # Handle warehouse creation and assignment
            from inventory.models import Warehouse
            
            if role == 'manager':
                warehouse_name = 'Manager Warehouse'
            elif role == 'attendance':
                warehouse_name = 'Attendant Warehouse'
            else:
                return user
                
            # Get or create the warehouse
            warehouse, created = Warehouse.objects.get_or_create(
                name=warehouse_name,
                defaults={'is_main': False}
            )
            
            # Assign warehouse to custom user
            custom_user.warehouses.add(warehouse)
            
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
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['can_add_inventory'] = forms.BooleanField(required=False, label='Add Inventory', widget=forms.CheckboxInput(attrs={'class': 'permission-checkbox'}))
        self.fields['can_change_inventory'] = forms.BooleanField(required=False, label='Change Inventory', widget=forms.CheckboxInput(attrs={'class': 'permission-checkbox'}))
        self.fields['can_delete_inventory'] = forms.BooleanField(required=False, label='Delete Inventory', widget=forms.CheckboxInput(attrs={'class': 'permission-checkbox'}))
        self.fields['can_view_inventory'] = forms.BooleanField(required=False, label='View Inventory', widget=forms.CheckboxInput(attrs={'class': 'permission-checkbox'}))
        
        self.fields['can_add_brand'] = forms.BooleanField(required=False, label='Add Brand', widget=forms.CheckboxInput(attrs={'class': 'permission-checkbox'}))
        self.fields['can_change_brand'] = forms.BooleanField(required=False, label='Change Brand', widget=forms.CheckboxInput(attrs={'class': 'permission-checkbox'}))
        self.fields['can_delete_brand'] = forms.BooleanField(required=False, label='Delete Brand', widget=forms.CheckboxInput(attrs={'class': 'permission-checkbox'}))
        self.fields['can_view_brand'] = forms.BooleanField(required=False, label='View Brand', widget=forms.CheckboxInput(attrs={'class': 'permission-checkbox'}))
        
        self.fields['can_add_category'] = forms.BooleanField(required=False, label='Add Category', widget=forms.CheckboxInput(attrs={'class': 'permission-checkbox'}))
        self.fields['can_change_category'] = forms.BooleanField(required=False, label='Change Category', widget=forms.CheckboxInput(attrs={'class': 'permission-checkbox'}))
        self.fields['can_delete_category'] = forms.BooleanField(required=False, label='Delete Category', widget=forms.CheckboxInput(attrs={'class': 'permission-checkbox'}))
        self.fields['can_view_category'] = forms.BooleanField(required=False, label='View Category', widget=forms.CheckboxInput(attrs={'class': 'permission-checkbox'}))