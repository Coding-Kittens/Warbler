"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows
from sqlalchemy import exc

os.environ["DATABASE_URL"] = "postgresql:///warbler_test"
from app import app

db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        Message.query.delete()
        Follows.query.delete()
        User.query.delete()
        self.client = app.test_client()

    def tearDown(self):
        db.session.rollback()

    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url="",
        )

        db.session.add(u)
        db.session.commit()

        # User should have no messages & no followers
        self.assertEqual(len(u.messages), 0)
        self.assertEqual(len(u.followers), 0)

    def test_repr(self):
        """Tests if repr works as expected"""

        u = User(
            email="test@test.com",
            username="testuser",
            password="HASHED_PASSWORD",
            image_url="",
        )

        db.session.add(u)
        db.session.commit()

        self.assertEqual(u.__repr__(), f"<User #{u.id}: {u.username}, {u.email}>")

    def test_is_following(self):
        """Tests is_following successfully detect when user1 is and is not following user2"""

        u = User(email="test@email.com", username="testUser", password="123456")
        u2 = User(email="test2@email2.com", username="testUser2", password="654321")

        db.session.add(u)
        db.session.add(u2)
        db.session.commit()

        self.assertEqual(u.is_following(u2), False)

        u.following.append(u2)
        db.session.add(u)
        db.session.commit()

        self.assertEqual(u.is_following(u2), True)

    def test_is_followed_by(self):
        """Tests is_followed_by successfully detect when user1 is and is not followed by user2"""

        u = User(email="test@email.com", username="testUser", password="123456")
        u2 = User(email="test2@email2.com", username="testUser2", password="654321")

        db.session.add(u)
        db.session.add(u2)
        db.session.commit()

        self.assertEqual(u.is_followed_by(u2), False)

        u.followers.append(u2)
        db.session.add(u)
        db.session.commit()

        self.assertEqual(u.is_followed_by(u2), True)

    def test_User_create(self):
        """Tests if signup works as expected"""
        u = User.signup(
            email="test@email.com", username="testUser", password="123456", image_url=""
        )
        db.session.commit()

        self.assertEqual(u.email, "test@email.com")
        self.assertEqual(u.username, "testUser")

    def test_User_invalid_username_create(self):
        """Tests if signup fails if no username"""
        u = User.signup(
            email="test@email.com", username=None, password="123234", image_url=""
        )
        db.session.add(u)
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_User_invalid_email_create(self):
        """Tests if signup fails if no email"""

        u = User.signup(
            email=None, username="testUser", password="123234", image_url=""
        )
        db.session.add(u)
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_User_invalid_password_create(self):
        """Tests if signup fails if no password"""
        with self.assertRaises(ValueError) as context:
            User.signup(
                email="test1@email.com",
                username="testUser1",
                password=None,
                image_url="",
            )

    def test_User_authenticate(self):
        """Tests if authenticate works as expected"""
        u = User.signup(
            email="test@email.com", username="testUser", password="123456", image_url=""
        )
        db.session.add(u)
        db.session.commit()

        self.assertEqual(User.authenticate(username="testUser", password="123456"), u)
        self.assertEqual(User.authenticate(username="testUser", password="1236"), False)
        self.assertEqual(User.authenticate(username="tUser", password="123456"), False)
