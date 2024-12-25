from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User, Permission
from django.db.models import Q, Sum, Count
from django.utils import timezone
from datetime import datetime, timedelta
from .forms import UserRegistrationForm, UserLoginForm, PermissionsForm, WarehouseAssignmentForm
from requisition.models import Requisition
from sales.models import Sale, ReturnItem, SaleItem
from .models import CustomUser
from django.contrib.contenttypes.models import ContentType

def index(request):
    if request.user.is_authenticated:
        return redirect('account:home')
    return redirect('account:login')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('account:home')
    else:
        form = UserRegistrationForm()
    return render(request, 'account/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                return redirect('account:home')
            else:
                messages.error(request, 'Invalid username or password')
    else:
        form = UserLoginForm()
    return render(request, 'account/login.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('account:login')

@login_required
def home(request):
    user = request.user
    requisitions = []
    
    # Get current month's start and end dates
    today = timezone.now()
    month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if today.month == 12:
        month_end = today.replace(year=today.year + 1, month=1, day=1, hour=23, minute=59, second=59, microsecond=999999) - timedelta(days=1)
    else:
        month_end = today.replace(month=today.month + 1, day=1, hour=23, minute=59, second=59, microsecond=999999) - timedelta(days=1)

    # Get sales statistics
    monthly_sales = Sale.objects.filter(sale_date__range=(month_start, month_end))
    total_sales = monthly_sales.aggregate(
        total_amount=Sum('total_price'),
        total_count=Count('id')
    )

    # Get returned items statistics for this month's sales
    monthly_returns = ReturnItem.objects.filter(
        return_date__range=(month_start, month_end)
    )
    total_returns = monthly_returns.aggregate(
        total_count=Count('id'),
        total_amount=Sum('sale_item__price_per_unit')
    )

    # Get top selling items
    top_selling_items = SaleItem.objects.filter(
        sale__sale_date__range=(month_start, month_end)
    ).values('item__item_name').annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum('quantity') * Sum('price_per_unit')
    ).order_by('-total_quantity')[:5]

    if user.is_superuser:
        requisitions = Requisition.objects.all().order_by('-created_at')[:5]
    else:
        requisitions = Requisition.objects.filter(
            Q(requester=user)
        ).order_by('-created_at')[:5]
    
    context = {
        'requisitions': requisitions,
        'monthly_sales': {
            'total_amount': total_sales['total_amount'] or 0,
            'total_count': total_sales['total_count'] or 0,
        },
        'monthly_returns': {
            'total_count': total_returns['total_count'] or 0,
            'total_amount': total_returns['total_amount'] or 0,
        },
        'top_selling_items': top_selling_items,
        'current_month': today.strftime('%B %Y'),
    }
    return render(request, 'account/home.html', context)

@login_required
def add_account(request):
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('account:home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully!')
            return redirect('account:list_accounts')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'account/add_account.html', {'form': form})

@login_required
def list_accounts(request):
    if not request.user.is_superuser:
        try:
            if not request.user.customuser.role == 'admin':
                messages.error(request, 'You do not have permission to access this page.')
                return redirect('account:home')
        except CustomUser.DoesNotExist:
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('account:home')
    
    users = User.objects.prefetch_related('customuser').filter(is_active=True).order_by('username')
    accounts = []
    for user in users:
        try:
            custom_user = user.customuser
            accounts.append({
                'user': user,
                'custom_user': custom_user
            })
        except CustomUser.DoesNotExist:
            # Create CustomUser for existing users without one
            if user.is_superuser:
                custom_user = CustomUser.objects.create(user=user, role='admin')
                accounts.append({
                    'user': user,
                    'custom_user': custom_user
                })
    
    return render(request, 'account/list_accounts.html', {'accounts': accounts})

@login_required
def manage_permissions(request, user_id):
    if not request.user.is_superuser and not hasattr(request.user, 'customuser') or request.user.customuser.role != 'admin':
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('account:home')
    
    try:
        managed_user = User.objects.get(id=user_id)
        custom_user = CustomUser.objects.get(user=managed_user)
    except (User.DoesNotExist, CustomUser.DoesNotExist):
        messages.error(request, 'User not found.')
        return redirect('account:list_accounts')
    
    if request.method == 'POST':
        perm_form = PermissionsForm(request.POST)
        warehouse_form = WarehouseAssignmentForm(request.POST)
        
        if perm_form.is_valid() and warehouse_form.is_valid():
            # Update warehouse assignments only for non-admin users
            if custom_user.role != 'admin':
                custom_user.warehouses.set(warehouse_form.cleaned_data['warehouses'])
            
            # Get content types for our models
            content_types = {
                'inventory': ContentType.objects.get(app_label='inventory', model='inventoryitem'),
                'brand': ContentType.objects.get(app_label='inventory', model='brand'),
                'category': ContentType.objects.get(app_label='inventory', model='category'),
                'requisition': ContentType.objects.get(app_label='requisition', model='requisition'),
            }
            
            # Clear existing permissions for these content types
            managed_user.user_permissions.filter(content_type__in=content_types.values()).delete()
            
            # Create or update permissions based on form data
            for field_name, value in perm_form.cleaned_data.items():
                if not field_name.startswith('can_'):
                    continue
                    
                # Extract model and action from field name
                # e.g., 'can_add_inventory' -> action='add', model='inventory'
                _, action, model = field_name.split('_')
                
                if model not in content_types:
                    continue
                
                # Get or create the permission
                try:
                    perm, _ = Permission.objects.get_or_create(
                        codename=f"{action}_{model}",
                        content_type=content_types[model],
                        defaults={'name': f'Can {action} {model}'}
                    )
                    
                    # Add permission if checkbox was checked
                    if value:
                        managed_user.user_permissions.add(perm)
                except Exception as e:
                    messages.warning(request, f'Error with permission {action}_{model}: {str(e)}')
            
            # Force permission cache refresh
            managed_user = User.objects.get(id=user_id)
            
            messages.success(request, 'Permissions updated successfully!')
            return redirect('account:manage_permissions', user_id=user_id)
    else:
        # Initialize forms with current data
        initial_perms = {}
        
        # Get current permissions
        for perm in managed_user.user_permissions.all():
            initial_perms[f'can_{perm.codename}'] = True
        
        perm_form = PermissionsForm(initial=initial_perms)
        warehouse_form = WarehouseAssignmentForm(
            initial={'warehouses': custom_user.warehouses.all()}
        )
    
    context = {
        'managed_user': managed_user,
        'perm_form': perm_form,
        'warehouse_form': warehouse_form,
        'current_permissions': [p.codename for p in managed_user.user_permissions.all()],  # For debugging
    }
    
    return render(request, 'account/manage_permissions.html', context)

@login_required
def delete_account(request, user_id):
    if not request.user.is_superuser and not hasattr(request.user, 'customuser') or request.user.customuser.role != 'admin':
        messages.error(request, 'You do not have permission to delete accounts.')
        return redirect('account:list_accounts')
    
    try:
        user_to_delete = User.objects.get(id=user_id)
        if user_to_delete.is_superuser:
            messages.error(request, 'Cannot delete superuser accounts.')
            return redirect('account:list_accounts')
        
        # Delete the user and their associated custom user
        user_to_delete.delete()
        messages.success(request, 'Account deleted successfully.')
    except User.DoesNotExist:
        messages.error(request, 'User not found.')
    
    return redirect('account:list_accounts')

def error_404(request, exception):
    context = {
        'error_code': '404',
        'error_message': 'The page you\'re looking for doesn\'t exist.'
    }
    return render(request, 'error.html', context, status=404)

def error_500(request):
    context = {
        'error_code': '500',
        'error_message': 'Internal server error. Please try again later.'
    }
    return render(request, 'error.html', context, status=500)