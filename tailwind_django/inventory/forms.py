from django import forms
from .models import InventoryItem, Brand, Category, Warehouse, GlobalSettings

class InventoryItemForm(forms.ModelForm):
    brand = forms.ModelChoiceField(queryset=Brand.objects.all(), empty_label="Select a brand")
    category = forms.ModelChoiceField(queryset=Category.objects.all(), empty_label="Select a category")
    warehouse = forms.ModelChoiceField(queryset=Warehouse.objects.all(), empty_label="Select a warehouse")

    class Meta:
        model = InventoryItem
        fields = ['brand', 'category', 'model', 'item_name', 'price', 'stock', 'availability', 'warehouse', 'image', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            if user.is_superuser or (hasattr(user, 'customuser') and user.customuser.role == 'admin'):
                self.fields['warehouse'].queryset = Warehouse.objects.all()
            elif hasattr(user, 'customuser'):
                self.fields['warehouse'].queryset = user.customuser.warehouses.all()
                if self.fields['warehouse'].queryset.count() == 1:
                    self.fields['warehouse'].initial = self.fields['warehouse'].queryset.first()
                    self.fields['warehouse'].widget = forms.HiddenInput()

class GlobalSettingsForm(forms.ModelForm):
    class Meta:
        model = GlobalSettings
        fields = ['reorder_level']
        widgets = {
            'reorder_level': forms.NumberInput(attrs={
                'class': 'block w-full rounded-lg border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500',
                'min': '0',
                'step': '1'
            })
        }

class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name']

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']