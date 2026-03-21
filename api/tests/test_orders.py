import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from api.models import User, Product, Order


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


# CREATE ORDER TESTS
@pytest.mark.django_db
def test_create_order_success(authenticated_client, sample_product):
    url = reverse('order-list-create')
    payload = {
        'product_id': sample_product.id,
        'quantity': 2
    }
    response = authenticated_client.post(url, payload, format='json')
    assert response.status_code == 201
    assert response.data['quantity'] == 2
    assert response.data['total_price'] == '10000.00'
    assert response.data['status'] == 'pending'


@pytest.mark.django_db
def test_create_order_total_price_calculated(authenticated_client, sample_product):
    url = reverse('order-list-create')
    payload = {
        'product_id': sample_product.id,
        'quantity': 3
    }
    response = authenticated_client.post(url, payload, format='json')
    assert response.status_code == 201
    # 5000 x 3 = 15000
    assert response.data['total_price'] == '15000.00'


@pytest.mark.django_db
def test_create_order_invalid_product(authenticated_client):
    url = reverse('order-list-create')
    payload = {
        'product_id': 999,  # non-existent product
        'quantity': 2
    }
    response = authenticated_client.post(url, payload, format='json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_order_missing_fields(authenticated_client, sample_product):
    url = reverse('order-list-create')
    payload = {
        'product_id': sample_product.id,
        # missing quantity
    }
    response = authenticated_client.post(url, payload, format='json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_order_unauthenticated(client, sample_product):
    url = reverse('order-list-create')
    payload = {
        'product_id': sample_product.id,
        'quantity': 2
    }
    response = client.post(url, payload, format='json')
    assert response.status_code == 401


# LIST ORDERS TESTS
@pytest.mark.django_db
def test_list_orders_success(authenticated_client, sample_order):
    url = reverse('order-list-create')
    response = authenticated_client.get(url)
    assert response.status_code == 200
    assert len(response.data) == 1


@pytest.mark.django_db
def test_list_orders_only_own_orders(client, sample_product):
    # create first user and order
    user1 = User.objects.create_user(
        username='user1',
        email='user1@gmail.com',
        password='testpassword123'
    )
    Order.objects.create(
        user=user1,
        product=sample_product,
        quantity=1,
        total_price=5000.00,
        status='pending'
    )

    # create second user and login
    User.objects.create_user(
        username='user2',
        email='user2@gmail.com',
        password='testpassword123'
    )
    response = client.post(reverse('login'), {
        'email': 'user2@gmail.com',
        'password': 'testpassword123'
    }, format='json')
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {response.data["access"]}')

    # user2 should not see user1's orders
    url = reverse('order-list-create')
    response = client.get(url)
    assert response.status_code == 200
    assert len(response.data) == 0


@pytest.mark.django_db
def test_list_orders_unauthenticated(client):
    url = reverse('order-list-create')
    response = client.get(url)
    assert response.status_code == 401


# RETRIEVE ORDER TESTS
@pytest.mark.django_db
def test_retrieve_order_success(authenticated_client, sample_order):
    url = reverse('order-detail', kwargs={'pk': sample_order['id']})
    response = authenticated_client.get(url)
    assert response.status_code == 200
    assert response.data['id'] == sample_order['id']


@pytest.mark.django_db
def test_retrieve_order_not_found(authenticated_client):
    url = reverse('order-detail', kwargs={'pk': 999})
    response = authenticated_client.get(url)
    assert response.status_code == 404