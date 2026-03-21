import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from api.models import User, Product


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def authenticated_client(client):
    # register user
    user = User.objects.create_user(
        username='testuser',
        email='testuser@gmail.com',
        password='testpassword123'
    )
    # login and get token
    url = reverse('login')
    response = client.post(url, {
        'email': 'testuser@gmail.com',
        'password': 'testpassword123'
    }, format='json')
    token = response.data['access']
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
    return client


@pytest.fixture
def sample_product(authenticated_client):
    url = reverse('product-list')
    payload = {
        'name': 'Test Product',
        'description': 'This is a test product',
        'price': '5000.00'
    }
    response = authenticated_client.post(url, payload, format='json')
    return response.data


# CREATE PRODUCT TESTS
@pytest.mark.django_db
def test_create_product_success(authenticated_client):
    url = reverse('product-list')
    payload = {
        'name': 'Test Product',
        'description': 'This is a test product',
        'price': '5000.00'
    }
    response = authenticated_client.post(url, payload, format='json')
    assert response.status_code == 201
    assert response.data['name'] == 'Test Product'
    assert response.data['price'] == '5000.00'
    assert Product.objects.filter(name='Test Product').exists()


@pytest.mark.django_db
def test_create_product_missing_fields(authenticated_client):
    url = reverse('product-list')
    payload = {
        'name': 'Test Product',
        # missing description and price
    }
    response = authenticated_client.post(url, payload, format='json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_create_product_unauthenticated(client):
    url = reverse('product-list')
    payload = {
        'name': 'Test Product',
        'description': 'This is a test product',
        'price': '5000.00'
    }
    response = client.post(url, payload, format='json')
    assert response.status_code == 401


# LIST PRODUCTS TESTS
@pytest.mark.django_db
def test_list_products_success(authenticated_client, sample_product):
    url = reverse('product-list')
    response = authenticated_client.get(url)
    assert response.status_code == 200
    assert len(response.data) == 1


@pytest.mark.django_db
def test_list_products_unauthenticated(client):
    url = reverse('product-list')
    response = client.get(url)
    assert response.status_code == 401


# RETRIEVE PRODUCT TESTS
@pytest.mark.django_db
def test_retrieve_product_success(authenticated_client, sample_product):
    url = reverse('product-detail', kwargs={'pk': sample_product['id']})
    response = authenticated_client.get(url)
    assert response.status_code == 200
    assert response.data['name'] == 'Test Product'


@pytest.mark.django_db
def test_retrieve_product_not_found(authenticated_client):
    url = reverse('product-detail', kwargs={'pk': 999})
    response = authenticated_client.get(url)
    assert response.status_code == 404


# UPDATE PRODUCT TESTS
@pytest.mark.django_db
def test_update_product_success(authenticated_client, sample_product):
    url = reverse('product-detail', kwargs={'pk': sample_product['id']})
    payload = {
        'name': 'Updated Product',
        'description': 'Updated description',
        'price': '8000.00'
    }
    response = authenticated_client.put(url, payload, format='json')
    assert response.status_code == 200
    assert response.data['name'] == 'Updated Product'
    assert response.data['price'] == '8000.00'


# DELETE PRODUCT TESTS
@pytest.mark.django_db
def test_delete_product_success(authenticated_client, sample_product):
    url = reverse('product-detail', kwargs={'pk': sample_product['id']})
    response = authenticated_client.delete(url)
    assert response.status_code == 204
    assert not Product.objects.filter(id=sample_product['id']).exists()