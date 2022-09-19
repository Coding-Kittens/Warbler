"""Message model tests."""


# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows, Likes

os.environ["DATABASE_URL"] = "postgresql:///warbler_test"

from app import app


db.create_all()


class UserModelTestCase(TestCase):
    """Test message model"""

    def setUp(self):
        """Create test client, add sample data."""

        User.query.delete()
        Message.query.delete()
        Follows.query.delete()
        Likes.query.delete()

        self.client = app.test_client()

    def test_Messages(self):
        """Does basic model work?"""
        u = User(id=123, email="test@email.com", username="testUser", password="123456")
        db.session.add(u)
        db.session.commit()

        msg = Message(text="test msg", user_id=123)

        db.session.add(msg)
        db.session.commit()

        self.assertEqual(msg.text, "test msg")
        self.assertEqual(msg.user_id, 123)
        #  msg should be in u.messages
        self.assertIn(msg, u.messages)

    def test_likes(self):
        """Test if liked messages are in user.likes"""
        u = User(id=234, email="test@email.com", username="testUser", password="123456")
        u2 = User(
            id=123, email="test2@email2.com", username="testUser2", password="654321"
        )
        db.session.add(u2)
        meassages = [
            Message(text="test3", user_id=234),
            Message(text="test4", user_id=234),
        ]

        u.likes = meassages
        db.session.add(u)
        db.session.commit()

        self.assertIn(meassages[0], u.likes)
        self.assertIn(meassages[1], u.likes)
