# test.py
import pytest
from app import app, db, Todo
from flask import url_for

@pytest.fixture
def client():
    # Configure the app for testing: enable the testing mode and use an in-memory SQLite DB.
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False  # if you are using forms with CSRF tokens
    
    # Create the test client and set up the database.
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        # Clean up / drop the test database after tests.
        with app.app_context():
            db.drop_all()


# ---------- Tests for the Home Route ("/") ----------

def test_home_get(client):
    """Test that GET request to home page loads correctly."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Todo' in response.data or b'Add' in response.data


def test_home_post_missing_fields(client):
    """Test POST request with missing title or description."""
    # Missing title
    response = client.post('/', data={'title': ' ', 'desc': 'Some description'}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Please fill in both the title and description." in response.data

    # Missing description
    response = client.post('/', data={'title': 'Task 1', 'desc': '   '}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Please fill in both the title and description." in response.data


def test_home_post_valid(client):
    """Test a valid POST request to add a new Todo."""
    response = client.post('/', data={'title': 'Task 1', 'desc': 'Description 1'}, follow_redirects=True)
    # Expect a redirect to home with success flash message.
    assert response.status_code == 200
    assert b"Todo added successfully!" in response.data

    # Verify that the Todo is in the database.
    with app.app_context():
        todo = Todo.query.filter_by(title='Task 1').first()
        assert todo is not None
        assert todo.desc == 'Description 1'


def test_home_post_duplicate_title(client):
    """Test that posting a Todo with an existing title returns an error."""
    # First, add a Todo with a unique title.
    with app.app_context():
        todo = Todo(title='Unique Task', desc='Some description')
        db.session.add(todo)
        db.session.commit()

    # Now try adding another Todo with the same title.
    response = client.post('/', data={'title': 'Unique Task', 'desc': 'Another description'}, follow_redirects=True)
    assert response.status_code == 200
    assert b"A Todo with that title already exists" in response.data

    # Verify that the duplicate was not added.
    with app.app_context():
        todos = Todo.query.filter_by(title='Unique Task').all()
        assert len(todos) == 1


# ---------- Tests for the Update Route  ----------

def test_update_get(client):
    """Test that GET request to update page loads the Todo."""
    # First, create a Todo to update.
    with app.app_context():
        todo = Todo(title='Update Task', desc='Initial description')
        db.session.add(todo)
        db.session.commit()
        sno = todo.sno

    response = client.get(f'/update/{sno}')
    assert response.status_code == 200
    # Check that the page contains the Todo's current title.
    assert b'Update Task' in response.data


def test_update_post_missing_fields(client):
    """Test update with missing title or description."""
    # Create a Todo to update.
    with app.app_context():
        todo = Todo(title='Task to Update', desc='Original description')
        db.session.add(todo)
        db.session.commit()
        sno = todo.sno

    # Missing title
    response = client.post(f'/update/{sno}', data={'title': '   ', 'desc': 'New description'}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Please fill in both the title and description." in response.data

    # Missing description
    response = client.post(f'/update/{sno}', data={'title': 'New Title', 'desc': '   '}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Please fill in both the title and description." in response.data


def test_update_post_valid(client):
    """Test updating a Todo with valid new data."""
    # Create a Todo to update.
    with app.app_context():
        todo = Todo(title='Old Title', desc='Old description')
        db.session.add(todo)
        db.session.commit()
        sno = todo.sno

    # Update with new valid data.
    response = client.post(f'/update/{sno}', data={'title': 'New Title', 'desc': 'New description'}, follow_redirects=True)
    assert response.status_code == 200
    assert b"Todo updated successfully!" in response.data

    # Verify that the database is updated.
    with app.app_context():
        updated_todo = Todo.query.get(sno)
        assert updated_todo.title == 'New Title'
        assert updated_todo.desc == 'New description'


def test_update_post_duplicate_title(client):
    """Test updating a Todo with a title that already exists in another Todo."""
    with app.app_context():
        # Create two Todos.
        todo1 = Todo(title='Task One', desc='Description One')
        todo2 = Todo(title='Task Two', desc='Description Two')
        db.session.add_all([todo1, todo2])
        db.session.commit()
        sno = todo2.sno

    # Try to update todo2 with the title of todo1.
    response = client.post(f'/update/{sno}', data={'title': 'Task One', 'desc': 'New Description'}, follow_redirects=True)
    assert response.status_code == 200
    assert b"A Todo with that title already exists" in response.data

    # Verify that todo2 was not updated.
    with app.app_context():
        todo2_after = Todo.query.get(sno)
        assert todo2_after.title == 'Task Two'


# ---------- Tests for the Delete Route ----------

def test_delete(client):
    """Test that a Todo can be deleted."""
    # Create a Todo to delete.
    with app.app_context():
        todo = Todo(title='Task to Delete', desc='Delete me')
        db.session.add(todo)
        db.session.commit()
        sno = todo.sno

    response = client.get(f'/delete/{sno}', follow_redirects=True)
    assert response.status_code == 200
    assert b"Todo deleted successfully!" in response.data

    # Verify that the Todo has been removed from the database.
    with app.app_context():
        deleted_todo = Todo.query.get(sno)
        assert deleted_todo is None
