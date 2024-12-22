from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User, Permission
from .forms import UserRegistrationForm, UserLoginForm, PermissionsForm, WarehouseAssignmentForm
from requisition.models import Requisition
from django.db.models import Q
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
    
    if user.is_superuser:
        requisitions = Requisition.objects.all().order_by('-created_at')[:5]
    else:
        requisitions = Requisition.objects.filter(
            Q(requester=user)
        ).order_by('-created_at')[:5]
    
    context = {
        'requisitions': requisitions,
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
            # Create CustomUser with admin role
            CustomUser.objects.create(user=user, role='admin')
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
            # Update warehouse assignments
            custom_user.warehouses.set(warehouse_form.cleaned_data['warehouses'])
            
            # Clear existing permissions
            managed_user.user_permissions.clear()
            
            # Update permissions based on form data
            content_types = {
                'inventory': ContentType.objects.get(app_label='inventory', model='inventoryitem'),
                'brand': ContentType.objects.get(app_label='inventory', model='brand'),
                'category': ContentType.objects.get(app_label='inventory', model='category'),
                'requisition': ContentType.objects.get(app_label='requisition', model='requisition'),
            }
            
            for field, value in perm_form.cleaned_data.items():
                if value:  # If permission is checked
                    model, action = field.split('_')[1:]  # e.g., 'can_add_inventory' -> ['can', 'add', 'inventory']
                    if model in content_types:
                        perm = Permission.objects.get(
                            codename=f"{action}_{model}",
                            content_type=content_types[model]
                        )
                        managed_user.user_permissions.add(perm)
            
            messages.success(request, 'Permissions updated successfully!')
            return redirect('account:list_accounts')
    else:
        # Initialize forms with current data
        initial_perms = {
            f'can_{perm.codename}': True 
            for perm in managed_user.user_permissions.all()
        }
        perm_form = PermissionsForm(initial=initial_perms)
        warehouse_form = WarehouseAssignmentForm(
            initial={'warehouses': custom_user.warehouses.all()}
        )
    
    return render(request, 'account/manage_permissions.html', {
        'managed_user': managed_user,
        'perm_form': perm_form,
        'warehouse_form': warehouse_form,
    })