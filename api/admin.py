
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, Product, Order, Payment




@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ['id', 'email', 'username', 'is_staff', 'created_at']
    ordering = ['email']
    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2'),
        }),
    )

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'price', 'created_at']
    search_fields = ['name']
    ordering = ['-created_at']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'product', 'quantity', 'total_price', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['user__username', 'product__name']
    ordering = ['-created_at']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'reference', 'amount', 'status', 'paid_at']
    list_filter = ['status']
    search_fields = ['reference', 'order__user__username']
    ordering = ['-created_at']