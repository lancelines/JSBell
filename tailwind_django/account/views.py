from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Sum, Count, F
from django.utils import timezone
from datetime import timedelta
from inventory.models import InventoryItem, Brand, Category, Warehouse, GlobalSettings
from sales.models import Sale, SaleItem
from .forms import RegistrationForm, AddAccountForm, LoginForm, PermissionManagementForm, WarehouseAssignmentForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import CustomUser

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            CustomUser.objects.create(user=user, role='admin')
            login(request, user)
            return redirect('account:home')
    else:
        form = RegistrationForm()
    return render(request, 'account/register.html', {'form': form})

@login_required
def add_account(request):
    if request.method == 'POST':
        form = AddAccountForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data['role']
            custom_user = CustomUser.objects.create(user=user, role=role)
            
            # Automatically assign warehouses based on role
            attendant_warehouse = Warehouse.objects.filter(name='Attendant Warehouse').first()
            manager_warehouse = Warehouse.objects.filter(name='Manager Warehouse').first()
            
            if role == 'attendance' and attendant_warehouse:
                custom_user.warehouses.add(attendant_warehouse)
            elif role == 'manager' and manager_warehouse:
                custom_user.warehouses.add(manager_warehouse)
            elif role == 'admin':
                # Admin gets access to all warehouses
                if attendant_warehouse:
                    custom_user.warehouses.add(attendant_warehouse)
                if manager_warehouse:
                    custom_user.warehouses.add(manager_warehouse)
            
            return redirect('account:list_accounts')
    else:
        form = AddAccountForm()
    return render(request, 'account/add_account.html', {'form': form})

def home(request):
    if request.user.is_authenticated:
        try:
            custom_user = request.user.customuser
            user_role = custom_user.role
        except:
            user_role = 'admin' if request.user.is_superuser else 'attendance'

        # Get warehouses associated with the user
        if request.user.is_superuser:
            warehouses = Warehouse.objects.all()
        else:
            warehouses = request.user.warehouses.all()
        
        # Get global settings for reorder level
        global_settings = GlobalSettings.objects.first()
        reorder_level = global_settings.reorder_level if global_settings else 10
        
        # Calculate sales statistics
        today = timezone.now()
        thirty_days_ago = today - timedelta(days=30)
        seven_days_ago = today - timedelta(days=7)

        # Get all sales
        all_sales = Sale.objects.all()
        
        # Get recent sales
        monthly_sales = all_sales.filter(sale_date__gte=thirty_days_ago)
        weekly_sales = all_sales.filter(sale_date__gte=seven_days_ago)

        # Calculate total revenue
        total_revenue = all_sales.aggregate(total=Sum('total_price'))['total'] or 0
        monthly_revenue = monthly_sales.aggregate(total=Sum('total_price'))['total'] or 0
        weekly_revenue = weekly_sales.aggregate(total=Sum('total_price'))['total'] or 0

        # Get top selling items
        top_selling_items = (
            SaleItem.objects
            .values('item__item_name')
            .annotate(total_quantity=Sum('quantity'))
            .order_by('-total_quantity')[:5]
        )

        # Get sales growth (compare this month to last month)
        last_month = thirty_days_ago - timedelta(days=30)
        last_month_sales = all_sales.filter(
            sale_date__gte=last_month,
            sale_date__lt=thirty_days_ago
        ).aggregate(total=Sum('total_price'))['total'] or 0
        
        if last_month_sales > 0:
            sales_growth = ((monthly_revenue - last_month_sales) / last_month_sales) * 100
        else:
            sales_growth = 100  # If no sales last month, consider it 100% growth

        # Initialize stats dictionary with sales data
        stats = {
            'total_sales': all_sales.count(),
            'monthly_sales': monthly_sales.count(),
            'weekly_sales': weekly_sales.count(),
            'total_revenue': total_revenue,
            'monthly_revenue': monthly_revenue,
            'weekly_revenue': weekly_revenue,
            'sales_growth': sales_growth,
            'top_selling_items': top_selling_items,
        }

        # Add inventory stats only for admin and manager roles
        if user_role in ['admin', 'manager']:
            items_query = InventoryItem.objects.filter(warehouse__in=warehouses)
            total_value = sum(item.price * item.stock for item in items_query)
            
            stats.update({
                'total_items': items_query.count(),
                'total_value': total_value,
                'low_stock_items': items_query.filter(stock__lte=reorder_level).count(),
                'total_categories': Category.objects.count(),
                'low_stock_items_list': items_query.filter(
                    stock__lte=reorder_level
                ).select_related('brand', 'category').order_by('stock')[:5],
            })
        
        return render(request, 'account/home.html', {
            'stats': stats,
            'reorder_level': reorder_level,
            'user_role': user_role
        })
    return render(request, 'account/home.html')

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('account:home')
    else:
        form = LoginForm()
    return render(request, 'account/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('account:login')

@login_required
def list_accounts(request):
    accounts = CustomUser.objects.all()
    return render(request, 'account/list_accounts.html', {'accounts': accounts})

def is_admin(user):
    return user.is_authenticated and CustomUser.objects.filter(user=user, role='admin').exists()

@login_required
@user_passes_test(is_admin)
def manage_permissions(request, user_id):
    user = get_object_or_404(User, id=user_id)
    inventory_content_type = ContentType.objects.get_for_model(InventoryItem)
    brand_content_type = ContentType.objects.get_for_model(Brand)
    category_content_type = ContentType.objects.get_for_model(Category)
    warehouse_content_type = ContentType.objects.get_for_model(Warehouse)
    
    if request.method == 'POST':
        perm_form = PermissionManagementForm(request.POST, prefix='perm')
        warehouse_form = WarehouseAssignmentForm(request.POST, prefix='warehouse')
        
        if perm_form.is_valid() and warehouse_form.is_valid():
            # Handle permissions
            permissions = {
                'add_inventoryitem': perm_form.cleaned_data['can_add_inventory'],
                'change_inventoryitem': perm_form.cleaned_data['can_change_inventory'],
                'delete_inventoryitem': perm_form.cleaned_data['can_delete_inventory'],
                'view_inventoryitem': perm_form.cleaned_data['can_view_inventory'],
                'add_brand': perm_form.cleaned_data['can_add_brand'],
                'add_category': perm_form.cleaned_data['can_add_category'],
                'add_warehouse': perm_form.cleaned_data['can_add_warehouse'],
                'change_warehouse': perm_form.cleaned_data['can_change_warehouse'],
                'delete_warehouse': perm_form.cleaned_data['can_delete_warehouse'],
                'view_warehouse': perm_form.cleaned_data['can_view_warehouse'],
            }
            for codename, value in permissions.items():
                if codename.startswith('add_brand'):
                    content_type = brand_content_type
                elif codename.startswith('add_category'):
                    content_type = category_content_type
                elif codename.endswith('warehouse'):
                    content_type = warehouse_content_type
                else:
                    content_type = inventory_content_type
                
                permission = Permission.objects.get(content_type=content_type, codename=codename)
                if value:
                    user.user_permissions.add(permission)
                else:
                    user.user_permissions.remove(permission)
            
            # Handle warehouse assignments
            selected_warehouses = warehouse_form.cleaned_data['warehouses']
            user.warehouses.set(selected_warehouses)
            
            return redirect('account:list_accounts')
    else:
        perm_initial = {
            'can_add_inventory': user.has_perm('inventory.add_inventoryitem'),
            'can_change_inventory': user.has_perm('inventory.change_inventoryitem'),
            'can_delete_inventory': user.has_perm('inventory.delete_inventoryitem'),
            'can_view_inventory': user.has_perm('inventory.view_inventoryitem'),
            'can_add_brand': user.has_perm('inventory.add_brand'),
            'can_add_category': user.has_perm('inventory.add_category'),
            'can_add_warehouse': user.has_perm('inventory.add_warehouse'),
            'can_change_warehouse': user.has_perm('inventory.change_warehouse'),
            'can_delete_warehouse': user.has_perm('inventory.delete_warehouse'),
            'can_view_warehouse': user.has_perm('inventory.view_warehouse'),
        }
        perm_form = PermissionManagementForm(initial=perm_initial, prefix='perm')
        warehouse_form = WarehouseAssignmentForm(initial={'warehouses': user.warehouses.all()}, prefix='warehouse')
    context = {
        'perm_form': perm_form,
        'warehouse_form': warehouse_form,
        'managed_user': user
    }
    return render(request, 'account/manage_permissions.html', context)