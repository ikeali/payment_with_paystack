from django.core.cache import cache
from ..models import Order


def create_order(user, product, quantity):
    total_price = product.price * quantity
    order = Order.objects.create(
        user=user,
        product=product,
        quantity=quantity,
        total_price=total_price,
        status='pending'
    )
    # invalidate user orders cache when new order is created
    cache.delete(f'user_orders_{user.id}')
    return order


def get_user_orders(user):
    cache_key = f'user_orders_{user.id}'
    orders = cache.get(cache_key)

    if not orders:
        orders = list(
            Order.objects
            .filter(user=user)
            .select_related('user', 'product')
            .order_by('-created_at')
        )
        cache.set(cache_key, orders, timeout=60 * 10)  # cache for 10 minutes

    return orders


def get_order_by_id(order_id, user):
    cache_key = f'order_{order_id}_user_{user.id}'
    order = cache.get(cache_key)

    if not order:
        try:
            order = (
                Order.objects
                .select_related('user', 'product')
                .get(id=order_id, user=user)
            )
            cache.set(cache_key, order, timeout=60 * 10)  # cache for 10 minutes
        except Order.DoesNotExist:
            return None

    return order