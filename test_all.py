import json

import pytest

from backend import app


@pytest.fixture
def client():
    app.config['TESTING'] = True

    with app.test_client() as client:
        yield client


def test_config(client):
    response = client.get('/api/config')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert isinstance(data, dict)
    assert len(data) > 0
