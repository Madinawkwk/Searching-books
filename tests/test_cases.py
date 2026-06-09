def test_favorites_require_login(client):
    resp = client.post('/favorite/add/OL123M', follow_redirects=True)
    assert resp.status_code == 200
    assert b'login' in resp.data.lower()


def test_chat_page_require_login(client):
    resp = client.get('/chat', follow_redirects=True)
    assert resp.status_code == 200
    assert b'login' in resp.data.lower()

