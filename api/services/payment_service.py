import uuid
import requests
from decouple import config
from django.utils import timezone
from ..models import Payment
from decouple import config


def initiate_payment(order, user_email):

    existing_payment = Payment.objects.filter(order=order).first()
    if existing_payment:
        if existing_payment.status == 'success':
            return None, 'Payment already completed for this order.'
        else:
            # delete the failed/pending payment and try again
            existing_payment.delete()
    reference = f"PAY-{uuid.uuid4().hex[:12].upper()}"

    paystack_url = f"{config('PAYSTACK_API_URL')}/initialize"
    headers = {
        "Authorization": f"Bearer {config('PAYSTACK_SECRET_KEY')}",
        "Content-Type": "application/json",
    }
    payload = {
        "email": user_email,
        "amount": int(order.total_price * 100),  # convert to kobo
        
        "reference": reference,
        "callback_url": config('PAYSTACK_CALLBACK_URL'),
    }

    response = requests.post(paystack_url, json=payload, headers=headers)
    res_data = response.json()

    if not res_data.get('status'):
        return None, res_data.get('message', 'Payment initialization failed.')

    payment = Payment.objects.create(
        order=order,
        reference=reference,
        access_code=res_data['data']['access_code'],
        amount=order.total_price,
        status='pending',
    )

    return payment, res_data['data']['authorization_url']


def verify_payment(reference):
    try:
        payment = Payment.objects.get(reference=reference)
    except Payment.DoesNotExist:
        return None, 'Payment not found.'

    paystack_url = f"{config('PAYSTACK_API_URL')}/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {config('PAYSTACK_SECRET_KEY')}",
    }

    response = requests.get(paystack_url, headers=headers)
    res_data = response.json()

    if not res_data.get('status'):
        return None, 'Verification failed.'

    paystack_status = res_data['data']['status']

    if paystack_status == 'success':
        payment.status = 'success'
        payment.paid_at = timezone.now()
        payment.order.status = 'paid'
    else:
        payment.status = 'failed'
        payment.order.status = 'failed'

    payment.save()
    payment.order.save()

    return payment, None


import hmac
import hashlib


def verify_paystack_webhook(payload, paystack_signature):
    secret = config('PAYSTACK_SECRET_KEY')
    computed_signature = hmac.new(
        secret.encode('utf-8'),
        payload,
        digestmod=hashlib.sha512
    ).hexdigest()
    return hmac.compare_digest(computed_signature, paystack_signature)


def handle_webhook_event(event, data):
    reference = data.get('reference')

    try:
        payment = Payment.objects.get(paystack_reference=reference)
    except Payment.DoesNotExist:
        return False

    if event == 'charge.success':
        payment.status = 'success'
        payment.paid_at = timezone.now()
        payment.order.status = 'paid'
    elif event == 'charge.failed':
        payment.status = 'failed'
        payment.order.status = 'failed'

    payment.save()
    payment.order.save()
    return True