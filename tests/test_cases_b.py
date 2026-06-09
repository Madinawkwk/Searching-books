import pytest
import requests
from flask import session, json


def test_search_post_with_mock(client, mock_openlibrary_api):
    resp = client.post('/', data={'query': 'test'}, follow_redirects=True)
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    assert 'lala' in html
    assert 'bebe' in html

def test_book_detail_page(client, mock_openlibrary_api):
    resp = client.get('/book/OL123M')
    assert resp.status_code == 200
    html = resp.data.decode('utf-8')
    assert 'lala' in html
    assert 'bebe' in html
    assert 'hahah' in html


def test_api_book_detail(client, mock_openlibrary_api):
    resp = client.get('/api/book/OL123M')
    assert resp.status_code == 404
    data = resp.get_json()
    assert isinstance(data, dict)
    assert data['title'] == 'lala'
    assert data['description'] == 'hahah'


