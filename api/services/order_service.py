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
    return order


def get_user_orders(user):
    return Order.objects.filter(user=user).order_by('-created_at')


def get_order_by_id(order_id, user):
    try:
        return Order.objects.get(id=order_id, user=user)
    except Order.DoesNotExist:
        return None