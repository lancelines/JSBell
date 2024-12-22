from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count

from .models import InventoryItem, Brand, Category, Warehouse, GlobalSettings
from .forms import InventoryItemForm, BrandForm, CategoryForm, WarehouseForm, GlobalSettingsForm

@login_required(login_url='account:login')
def inventory_list(request):
    if not request.user.warehouses.exists():
        return render(request, 'inventory/no_warehouse.html')
    
    # Get or create global settings
    global_settings, created = GlobalSettings.objects.get_or_create()
    
    # Handle global settings update
    if request.method == 'POST' and request.user.has_perm('inventory.change_globalsettings'):
        form = GlobalSettingsForm(request.POST, instance=global_settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Global settings updated successfully.')
            return redirect('inventory:list')
        else:
            messages.error(request, 'Error updating global settings.')
    
    # Initialize the form for the template
    global_settings_form = GlobalSettingsForm(instance=global_settings)
    
    # Get user role
    user_role = request.user.customuser.role if hasattr(request.user, 'customuser') else None
    
    # For attendants, initially show only their assigned warehouse
    if user_role == 'attendance':
        assigned_warehouse = request.user.warehouses.first()
        # Always filter by assigned warehouse for attendants unless they're making a request
        items = InventoryItem.objects.filter(warehouse=assigned_warehouse).select_related(
            'warehouse', 'brand', 'category'
        )
    else:
        # For managers and admins, show all their warehouses
        warehouses = request.user.warehouses.all()
        items = InventoryItem.objects.filter(warehouse__in=warehouses).select_related(
            'warehouse', 'brand', 'category'
        )
    
    # Search functionality
    query = request.GET.get('q')
    if query:
        items = items.filter(
            Q(item_name__icontains=query) |
            Q(model__icontains=query) |
            Q(brand__name__icontains=query) |
            Q(category__name__icontains=query)
        )
    
    # Filter handling
    selected_warehouse = request.GET.get('warehouse')
    selected_brand = request.GET.get('brand')
    selected_category = request.GET.get('category')
    filter_type = request.GET.get('filter', 'all')  # New filter type parameter
    
    # For attendants, only apply warehouse filter when explicitly selected
    if user_role == 'attendance':
        if selected_warehouse:
            # When requesting from another warehouse
            items = InventoryItem.objects.filter(warehouse_id=selected_warehouse).select_related(
                'warehouse', 'brand', 'category'
            )
    else:
        if selected_warehouse:
            items = items.filter(warehouse_id=selected_warehouse)
    
    # Apply category and brand filters
    if selected_brand:
        items = items.filter(brand_id=selected_brand)
    if selected_category:
        items = items.filter(category_id=selected_category)
    
    # Apply quick filters
    if filter_type == 'low_stock':
        items = items.filter(stock__lte=global_settings.reorder_level)
    elif filter_type == 'no_price':
        items = items.filter(Q(price__isnull=True) | Q(price=0))
    
    # Get names for active filters (for display)
    selected_category_name = Category.objects.filter(id=selected_category).values_list('name', flat=True).first() if selected_category else None
    selected_brand_name = Brand.objects.filter(id=selected_brand).values_list('name', flat=True).first() if selected_brand else None
    
    # Count active filters
    active_filters = sum(1 for x in [selected_warehouse, selected_brand, selected_category, filter_type != 'all'] if x)
    
    # Pagination
    paginator = Paginator(items, 10)
    page_number = request.GET.get('page')
    items = paginator.get_page(page_number)
    
    context = {
        'items': items,
        'all_warehouses': request.user.warehouses.all(),
        'all_brands': Brand.objects.all(),
        'all_categories': Category.objects.all(),
        'selected_warehouse': selected_warehouse,
        'selected_brand': selected_brand,
        'selected_category': selected_category,
        'selected_category_name': selected_category_name,
        'selected_brand_name': selected_brand_name,
        'filter_type': filter_type,
        'query': query,
        'active_filters': active_filters,
        'global_settings': global_settings,
        'global_settings_form': global_settings_form,
        'is_main_warehouse': request.user.warehouses.filter(is_main=True).exists(),
        'user_role': user_role,
        'table_headers': ['Image', 'Item Name', 'Category', 'Brand', 'Stock', 'Unit Price', 'Actions'],
    }
    return render(request, 'inventory/inventory_list.html', context)

@login_required(login_url='account:login')
@permission_required('inventory.view_inventoryitem', raise_exception=True)
def inventory_detail(request, pk):
    item = get_object_or_404(
        InventoryItem.objects.select_related('warehouse', 'brand', 'category'),
        pk=pk
    )
    if item.warehouse not in request.user.warehouses.all():
        raise PermissionDenied
    return render(request, 'inventory/inventory_detail.html', {'item': item})

@login_required(login_url='account:login')
@permission_required('inventory.add_inventoryitem', raise_exception=True)
def inventory_create(request):
    if not request.user.warehouses.exists():
        raise PermissionDenied
    
    if request.method == 'POST':
        form = InventoryItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            if item.warehouse not in request.user.warehouses.all():
                raise PermissionDenied
            item.save()
            messages.success(request, 'Item created successfully.')
            return redirect('inventory:list')
        else:
            messages.error(request, 'Error creating item. Please check the form.')
    else:
        form = InventoryItemForm()
        form.fields['warehouse'].queryset = request.user.warehouses.all()
    
    return render(request, 'inventory/inventory_form.html', {'form': form, 'action': 'Create'})

@login_required(login_url='account:login')
@permission_required('inventory.change_inventoryitem', raise_exception=True)
def inventory_update(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if item.warehouse not in request.user.warehouses.all():
        raise PermissionDenied
    
    if request.method == 'POST':
        form = InventoryItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            updated_item = form.save(commit=False)
            if updated_item.warehouse not in request.user.warehouses.all():
                raise PermissionDenied
            updated_item.save()
            messages.success(request, 'Item updated successfully.')
            return redirect('inventory:list')
        else:
            messages.error(request, 'Error updating item. Please check the form.')
    else:
        form = InventoryItemForm(instance=item)
        form.fields['warehouse'].queryset = request.user.warehouses.all()
    
    return render(request, 'inventory/inventory_form.html', {'form': form, 'action': 'Update'})

@login_required(login_url='account:login')
@permission_required('inventory.delete_inventoryitem', raise_exception=True)
def inventory_delete(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if item.warehouse not in request.user.warehouses.all():
        raise PermissionDenied
    
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Item deleted successfully.')
        return redirect('inventory:list')
    return render(request, 'inventory/inventory_confirm_delete.html', {'item': item})

@login_required(login_url='account:login')
@permission_required('inventory.add_brand', raise_exception=True)
def create_brand(request):
    if request.method == 'POST':
        form = BrandForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Brand created successfully.')
            return redirect('inventory:list')
        else:
            messages.error(request, 'Error creating brand. Please check the form.')
    else:
        form = BrandForm()
    return render(request, 'inventory/brand_form.html', {'form': form})

@login_required(login_url='account:login')
@permission_required('inventory.add_category', raise_exception=True)
def create_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully.')
            return redirect('inventory:list')
        else:
            messages.error(request, 'Error creating category. Please check the form.')
    else:
        form = CategoryForm()
    return render(request, 'inventory/category_form.html', {'form': form})

@login_required(login_url='account:login')
@permission_required('inventory.add_warehouse', raise_exception=True)
def create_warehouse(request):
    if request.method == 'POST':
        form = WarehouseForm(request.POST)
        if form.is_valid():
            warehouse = form.save()
            messages.success(request, 'Warehouse created successfully.')
            return redirect('inventory:list')
        else:
            messages.error(request, 'Error creating warehouse. Please check the form.')
    else:
        form = WarehouseForm()
    return render(request, 'inventory/warehouse_form.html', {'form': form})

@login_required(login_url='account:login')
def set_price(request, pk):
    item = get_object_or_404(InventoryItem, pk=pk)
    if item.warehouse not in request.user.warehouses.all():
        raise PermissionDenied
    
    if request.method == 'POST':
        try:
            new_price = request.POST.get('price')
            if new_price is not None:
                item.price = new_price
                item.save()
                messages.success(request, f'Price for {item.item_name} set successfully.')
            else:
                messages.error(request, 'Price value is required.')
        except ValueError:
            messages.error(request, 'Invalid price value.')
        return redirect('inventory:list')
    
    return render(request, 'inventory/set_price.html', {'item': item})

@login_required(login_url='account:login')
def dashboard(request):
    if not request.user.warehouses.exists():
        return render(request, 'inventory/no_warehouse.html')
    
    # Get warehouse items
    warehouse = request.user.warehouses.first()
    items = InventoryItem.objects.filter(warehouse=warehouse)
    
    # Calculate statistics
    total_items = items.count()
    total_value = items.aggregate(total=Sum('price'))['total'] or 0
    categories_count = Category.objects.count()
    
    # Get low stock items
    global_settings = GlobalSettings.objects.first()
    reorder_level = global_settings.reorder_level if global_settings else 2
    low_stock_items = items.filter(current_stock__lte=reorder_level)
    low_stock_count = low_stock_items.count()
    
    context = {
        'total_items': total_items,
        'total_value': total_value,
        'categories_count': categories_count,
        'low_stock_items': low_stock_items,
        'low_stock_count': low_stock_count,
    }
    
    return render(request, 'inventory/dashboard.html', context)