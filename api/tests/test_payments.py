import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from unittest.mock import patch, MagicMock
from api.models import User, Product, Order, Payment


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def authenticated_client(client):
    user = User.objects.create_user(
        username='testuser',
        email='testuser@gmail.com',
        password='testpassword123'
    )
    url = reverse('login')
    response = client.post(url, {
        'email': 'testuser@gmail.com',
        'password': 'testpassword123'
    }, format='json')
    token = response.data['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client


@pytest.fixture
def sample_product():
    return Product.objects.create(
        name='Test Product',
        description='This is a test product',
        price='5000.00'
    )


@pytest.fixture
def sample_order(authenticated_client, sample_product):
    url = reverse('order-list-create')
    payload = {
        'product_id': sample_product.id,
        'quantity': 2
    }
    response = authenticated_client.post(url, payload, format='json')
    return response.data


@pytest.fixture
def mock_paystack_initiate():
    with patch('api.services.payment_service.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': True,
            'data': {
                'authorization_url': 'https://checkout.paystack.com/test123',
                'access_code': 'test_access_code',
                'reference': 'PAY-TEST123'
            }
        }
        mock_post.return_value = mock_response
        yield mock_post


@pytest.fixture
def mock_paystack_verify_success():
    with patch('api.services.payment_service.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': True,
            'data': {
                'status': 'success',
                'reference': 'PAY-TEST123'
            }
        }
        mock_get.return_value = mock_response
        yield mock_get


@pytest.fixture
def mock_paystack_verify_failed():
    with patch('api.services.payment_service.requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            'status': True,
            'data': {
                'status': 'failed',
                'reference': 'PAY-TEST123'
            }
        }
        mock_get.return_value = mock_response
        yield mock_get


# INITIATE PAYMENT TESTS
@pytest.mark.django_db
def test_initiate_payment_success(authenticated_client, sample_order, mock_paystack_initiate):
    url = reverse('initiate-payment', kwargs={'order_id': sample_order['id']})
    response = authenticated_client.post(url)
    assert response.status_code == 200
    assert 'authorization_url' in response.data
    assert 'reference' in response.data
    assert response.data['authorization_url'] == 'https://checkout.paystack.com/test123'


@pytest.mark.django_db
def test_initiate_payment_order_not_found(authenticated_client, mock_paystack_initiate):
    url = reverse('initiate-payment', kwargs={'order_id': 999})
    response = authenticated_client.post(url)
    assert response.status_code == 404


@pytest.mark.django_db
def test_initiate_payment_already_paid(authenticated_client, sample_order, mock_paystack_initiate):
    # first mark the order as paid
    Order.objects.filter(id=sample_order['id']).update(status='paid')
    url = reverse('initiate-payment', kwargs={'order_id': sample_order['id']})
    response = authenticated_client.post(url)
    assert response.status_code == 400
    assert response.data['error'] == 'Order is already paid.'


@pytest.mark.django_db
def test_initiate_payment_unauthenticated(client): 
    url = reverse('initiate-payment', kwargs={'order_id': 1})
    response = client.post(url)
    assert response.status_code == 401

# VERIFY PAYMENT TESTS
@pytest.mark.django_db
def test_verify_payment_success(authenticated_client, sample_order, mock_paystack_initiate, mock_paystack_verify_success):
    # first initiate payment
    initiate_url = reverse('initiate-payment', kwargs={'order_id': sample_order['id']})
    initiate_response = authenticated_client.post(initiate_url)
    reference = initiate_response.data['reference']

    # then verify
    verify_url = reverse('verify-payment', kwargs={'reference': reference})
    response = authenticated_client.get(verify_url)
    assert response.status_code == 200
    assert response.data['payment']['status'] == 'success'
    assert response.data['payment']['order']['status'] == 'paid'


@pytest.mark.django_db
def test_verify_payment_failed(authenticated_client, sample_order, mock_paystack_initiate, mock_paystack_verify_failed):
    # first initiate payment
    initiate_url = reverse('initiate-payment', kwargs={'order_id': sample_order['id']})
    initiate_response = authenticated_client.post(initiate_url)
    reference = initiate_response.data['reference']

    # then verify
    verify_url = reverse('verify-payment', kwargs={'reference': reference})
    response = authenticated_client.get(verify_url)
    assert response.status_code == 200
    assert response.data['payment']['status'] == 'failed'
    assert response.data['payment']['order']['status'] == 'failed'


@pytest.mark.django_db
def test_verify_payment_not_found(authenticated_client):
    url = reverse('verify-payment', kwargs={'reference': 'PAY-INVALID123'})
    response = authenticated_client.get(url)
    assert response.status_code == 400
    assert response.data['error'] == 'Payment not found.'


@pytest.mark.django_db
def test_verify_payment_unauthenticated(client):
    url = reverse('verify-payment', kwargs={'reference': 'PAY-TEST123'})
    response = client.get(url)
    assert response.status_code == 401