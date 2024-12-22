from django.db import models
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from requisition.models import Requisition
from inventory.models import Warehouse

class CustomUser(models.Model):
    ROLE_CHOICES = [
        ('manager', 'Manager'),
        ('attendance', 'Attendance'),
        ('admin', 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    warehouses = models.ManyToManyField(Warehouse, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new or self.role in ['manager', 'admin']:
            self.update_permissions()

    def update_permissions(self):
        # Remove all existing permissions
        self.user.user_permissions.clear()

        # Add permissions based on role
        if self.role in ['manager', 'admin']:
            self.add_requisition_permission()

        if self.role == 'admin':
            self.add_admin_permissions()

    def add_requisition_permission(self):
        content_type = ContentType.objects.get_for_model(Requisition)
        permission, created = Permission.objects.get_or_create(
            codename='can_approve_requisition',
            name='Can approve requisition',
            content_type=content_type,
        )
        self.user.user_permissions.add(permission)

    def add_admin_permissions(self):
        # Add all permissions for admin role
        all_permissions = Permission.objects.all()
        self.user.user_permissions.add(*all_permissions)

    @property
    def is_manager(self):
        return self.role == 'manager'

    @property
    def is_admin(self):
        return self.role == 'admin'