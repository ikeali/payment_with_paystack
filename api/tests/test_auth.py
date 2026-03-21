import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from api.models import User


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def registered_user(client):
    url = reverse('register')
    payload = {
        'username': 'testuser',
        'email': 'testuser@gmail.com',
        'password': 'testpassword123'
    }
    client.post(url, payload, format='json')
    return payload


# REGISTER TESTS

@pytest.mark.django_db
def test_register_success(client):
    url = reverse('register')
    payload = {
        'username': 'testuser',
        'email': 'testuser@gmail.com',
        'password': 'testpassword123'
    }
    response = client.post(url, payload, format='json')
    assert response.status_code == 201
    assert response.data['message'] == 'Registration successful'
    assert response.data['user']['email'] == 'testuser@gmail.com'
    assert User.objects.filter(email='testuser@gmail.com').exists()


@pytest.mark.django_db
def test_register_duplicate_email(client, registered_user):
    url = reverse('register')
    payload = {
        'username': 'testuser2',
        'email': 'testuser@gmail.com',  # same email
        'password': 'testpassword123'
    }
    response = client.post(url, payload, format='json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_register_missing_fields(client):
    url = reverse('register')
    payload = {
        'email': 'testuser@gmail.com',
        # missing username and password
    }
    response = client.post(url, payload, format='json')
    assert response.status_code == 400


@pytest.mark.django_db
def test_register_short_password(client):
    url = reverse('register')
    payload = {
        'username': 'testuser',
        'email': 'testuser@gmail.com',
        'password': '123'  # less than 8 characters
    }
    response = client.post(url, payload, format='json')
    assert response.status_code == 400


# LOGIN TESTS

@pytest.mark.django_db
def test_login_success(client, registered_user):
    url = reverse('login')
    payload = {
        'email': registered_user['email'],
        'password': registered_user['password']
    }
    response = client.post(url, payload, format='json')
    assert response.status_code == 200
    assert 'access' in response.data
    assert 'refresh' in response.data

@pytest.mark.django_db
def test_login_wrong_password(client, registered_user):
    url = reverse('login')
    payload = {
        'email': registered_user['email'],
        'password': 'wrongpassword'
    }
    response = client.post(url, payload, format='json')
    assert response.status_code == 401  # updated 400 -> 401


@pytest.mark.django_db
def test_login_wrong_email(client):
    url = reverse('login')
    payload = {
        'email': 'nonexistent@gmail.com',
        'password': 'testpassword123'
    }
    response = client.post(url, payload, format='json')
    assert response.status_code == 401  # updated 400 -> 401

@pytest.mark.django_db
def test_login_missing_fields(client):
    url = reverse('login')
    payload = {
        'email': 'testuser@gmail.com',
        # missing password
    }
    response = client.post(url, payload, format='json')
    assert response.status_code == 400