from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class AuthRateThrottle(AnonRateThrottle):
    rate = '10/hour'
    scope = 'auth'


class PaymentRateThrottle(UserRateThrottle):
    rate = '50/hour'
    scope = 'payment'