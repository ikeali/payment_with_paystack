from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from .models import User, Product, Order, Payment

from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import EmailTokenObtainPairSerializer


from .models import Product
from .serializers import (
    RegisterSerializer, UserSerializer,
    ProductSerializer, OrderSerializer, PaymentSerializer
)
from .services.auth_service import register_user
from .services.order_service import create_order, get_user_orders, get_order_by_id
from .services.payment_service import initiate_payment, verify_payment, handle_webhook_event, verify_paystack_webhook
import json
from .throttles import AuthRateThrottle, PaymentRateThrottle




# AUTH
class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]  # ← 10 requests per hour


    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = register_user(serializer.validated_data)
        return Response({
            'message': 'Registration successful',
            'user': UserSerializer(user).data,
        }, status=status.HTTP_201_CREATED)



class EmailTokenObtainPairView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [AuthRateThrottle]  # ← 10 requests per hour


    def post(self, request):
        serializer = EmailTokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)

# PRODUCTS
class ProductListView(generics.ListCreateAPIView):
    queryset = Product.objects.all().order_by('-created_at')
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]


# ORDERS
class OrderListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        orders = get_user_orders(request.user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = OrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        product = data.get('product')
        quantity = data.get('quantity')

        if not product:
            return Response({'error': 'Product is required.'}, status=status.HTTP_400_BAD_REQUEST)
        if not quantity:
            return Response({'error': 'Quantity is required.'}, status=status.HTTP_400_BAD_REQUEST)

        order = create_order(request.user, product, quantity)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

class OrderDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        order = get_order_by_id(pk, request.user)
        if not order:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(OrderSerializer(order).data)


# PAYMENTS 
class InitiatePaymentView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [PaymentRateThrottle]  # ← 50 requests per hour


    def post(self, request, order_id):
        order = get_order_by_id(order_id, request.user)
        if not order:
            return Response({'error': 'Order not found.'}, status=status.HTTP_404_NOT_FOUND)
        if order.status == 'paid':
            return Response({'error': 'Order is already paid.'}, status=status.HTTP_400_BAD_REQUEST)

        payment, result = initiate_payment(order, request.user.email)
        if not payment:
            return Response({'error': result}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'message': 'Payment initialized successfully.',
            'authorization_url': result,
            'reference': payment.reference,
        }, status=status.HTTP_200_OK)


class VerifyPaymentView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [PaymentRateThrottle]  # ← 50 requests per hour


    def get(self, request, reference):
        payment, error = verify_payment(reference)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            'message': f"Payment {payment.status}.",
            'payment': PaymentSerializer(payment).data,
        }, status=status.HTTP_200_OK)
    



class PaystackCallbackView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        reference = request.query_params.get('reference')
        if not reference:
            return Response({'error': 'Reference not provided.'}, status=status.HTTP_400_BAD_REQUEST)

        payment, error = verify_payment(reference)
        if error:
            return Response({'error': error}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'message': f"Payment {payment.status}.",
            'payment': PaymentSerializer(payment).data,
        }, status=status.HTTP_200_OK)


class PaystackWebhookView(APIView):
    permission_classes = [AllowAny]  # Paystack doesn't send JWT

    def post(self, request):
        paystack_signature = request.headers.get('x-paystack-signature')
        if not paystack_signature:
            return Response({'error': 'No signature provided.'}, status=status.HTTP_400_BAD_REQUEST)

        # verify the webhook is actually from Paystack
        is_valid = verify_paystack_webhook(request.body, paystack_signature)
        if not is_valid:
            return Response({'error': 'Invalid signature.'}, status=status.HTTP_400_BAD_REQUEST)

        payload = json.loads(request.body)
        event = payload.get('event')
        data = payload.get('data', {})

        handle_webhook_event(event, data)

        return Response({'message': 'Webhook received.'}, status=status.HTTP_200_OK)


