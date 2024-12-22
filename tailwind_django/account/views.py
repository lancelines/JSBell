from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User, Permission
from .forms import UserRegistrationForm, UserLoginForm
from requisition.models import Requisition
from django.db.models import Q

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
            Q(created_by=user) | Q(approver=user)
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
            form.save()
            messages.success(request, 'Account created successfully!')
            return redirect('account:list_accounts')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'account/add_account.html', {'form': form})

@login_required
def list_accounts(request):
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('account:home')
    
    accounts = User.objects.all().order_by('username')
    return render(request, 'account/list_accounts.html', {'accounts': accounts})

@login_required
def manage_permissions(request, user_id):
    if not request.user.is_superuser:
        messages.error(request, 'You do not have permission to access this page.')
        return redirect('account:home')
    
    user = User.objects.get(id=user_id)
    all_permissions = Permission.objects.all()
    
    if request.method == 'POST':
        selected_permissions = request.POST.getlist('permissions')
        user.user_permissions.clear()
        for perm_id in selected_permissions:
            permission = Permission.objects.get(id=perm_id)
            user.user_permissions.add(permission)
        messages.success(request, f'Permissions updated for {user.username}')
        return redirect('account:list_accounts')
    
    context = {
        'user': user,
        'all_permissions': all_permissions,
    }
    return render(request, 'account/manage_permissions.html', context)