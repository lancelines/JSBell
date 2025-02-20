# Generated by Django 5.1.3 on 2024-11-26 01:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0007_globalsettings_inventoryitem_description_and_more'),
        ('requisition', '0011_requisition_delivery_image'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='requisition',
            name='actual_delivery_date',
        ),
        migrations.RemoveField(
            model_name='requisition',
            name='description',
        ),
        migrations.AddField(
            model_name='requisition',
            name='selected_item',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='selected_for_requisitions', to='inventory.inventoryitem'),
        ),
        migrations.AlterField(
            model_name='requisition',
            name='destination_warehouse',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='destination_requisitions', to='inventory.warehouse'),
        ),
        migrations.AlterField(
            model_name='requisition',
            name='item',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='inventory.inventoryitem'),
        ),
        migrations.AlterField(
            model_name='requisition',
            name='quantity',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AlterField(
            model_name='requisition',
            name='request_type',
            field=models.CharField(choices=[('item', 'Item Request'), ('service', 'Service Request')], max_length=10),
        ),
        migrations.AlterField(
            model_name='requisition',
            name='source_warehouse',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='source_requisitions', to='inventory.warehouse'),
        ),
        migrations.AlterField(
            model_name='requisition',
            name='status',
            field=models.CharField(choices=[('pending', 'Pending Manager Approval'), ('pending_admin_approval', 'Pending Admin Approval'), ('approved_by_admin', 'Approved by Admin'), ('rejected_by_manager', 'Rejected by Manager'), ('rejected_by_admin', 'Rejected by Admin'), ('in_delivery', 'In Delivery'), ('delivered', 'Delivered'), ('completed', 'Completed')], default='pending', max_length=25),
        ),
    ]
