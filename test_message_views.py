"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes


os.environ["DATABASE_URL"] = "postgresql:///warbler_test"

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
db.create_all()


# Don't have WTForms use CSRF at all, since it's a pain to test

app.config["WTF_CSRF_ENABLED"] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(
            username="testuser",
            email="test@test.com",
            password="testuser",
            image_url=None,
        )

        self.testuser2 = User.signup(
            username="testuser2",
            email="test@test2.com",
            password="testuser2",
            image_url=None,
        )

        self.testuser.id = 123
        self.testuser2.id = 234
        db.session.add(self.testuser)
        db.session.add(self.testuser2)
        db.session.commit()

    def test_add_message(self):
        """
        Can use add a message when looged in?
        """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 123

            res = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(res.status_code, 302)

            msg = Message.query.one()
            self.assertEqual(msg.text, "Hello")

    def test_loggedOut_add_message(self):
        """
        Are you prohibited from adding messages when logged out?
        """

        with self.client as c:
            res = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            html = res.get_data(as_text=True)
            self.assertIn("Access unauthorized.", html)

    def test_add_message_invalid_user(self):
        """
        Can use add a message when looged in?
        """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 2341341

            res = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True)
            self.assertEqual(res.status_code, 404)

    def test_show_message(self):
        """
        Can use add a message when looged in?
        """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 123

            msg = Message(id=234, text="test msg 1", user_id=123)
            db.session.add(msg)
            db.session.commit()

            res = c.get("/messages/234")
            self.assertEqual(res.status_code, 200)
            html = res.get_data(as_text=True)
            self.assertIn("test msg 1", html)

    def test_show_invalid_message(self):
        """
        Can use add a message when looged in?
        """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 123

            res = c.get("/messages/23423232")
            self.assertEqual(res.status_code, 404)

    def test_delete_message(self):
        """
        Can use delete a message when looged in?
        Are you prohibited from deleting messages when logged out?
        """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 123

            msg = Message(id=234, text="test msg 1", user_id=123)
            db.session.add(msg)
            db.session.commit()

            res = c.post("/messages/400/delete", follow_redirects=True)
            self.assertEqual(res.status_code, 404)

            res = c.post(f"/messages/{234}/delete")

            self.assertEqual(res.status_code, 302)
            msgs = Message.query.filter_by(id=234).all()
            self.assertEqual(msgs, [])

    def test_loggedOut_delete_message(self):
        """
        Are you prohibited from deleting messages when logged out?
        """
        with self.client as c:

            msg = Message(id=234, text="test msg 1", user_id=123)

            db.session.add(msg)
            db.session.commit()

            res = c.post(f"/messages/{234}/delete")
            self.assertEqual(res.status_code, 302)
            # the message should not be deleted
            msg1 = Message.query.one()
            self.assertEqual(msg1.text, "test msg 1")

    def test_delete_message_as_other_user(self):
        """
        Are you prohibited from deleting a message as another user when logged in?
        """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 123

            msg = Message(id=456, text="test msg 1", user_id=234)

            db.session.add(msg)
            db.session.commit()

            res = c.post(f"/messages/{456}/delete")

            self.assertEqual(res.status_code, 302)
            # the message should not be deleted since the logged in user.id is not the same as the message.user_id
            msg1 = Message.query.one()
            self.assertEqual(msg1.text, "test msg 1")

    def test_toggle_like(self):
        """
        Test if message not liked, like it.
        Test if message liked, unlike it.
        """
        ## make a message to like/unlike
        msg = Message(id=123, text="test msg 1", user_id=234)
        db.session.add(msg)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 123

            ##like the message since the message is not liked by that user yet
            res = c.post(f"/users/like/123", follow_redirects=True)
            self.assertEqual(res.status_code, 200)
            likes = Likes.query.filter_by(user_id=123, message_id=123).one()

            self.assertEqual(likes.user_id, 123)
            self.assertEqual(likes.message_id, 123)

            ##unlikes the message since the user has like that message before
            res = c.post(f"/users/like/123")
            self.assertEqual(res.status_code, 302)

            likes = Likes.query.filter_by(user_id=123, message_id=123).all()
            self.assertEqual(likes, [])

    def test_loggedOut_like(self):
        """
        Are you prohibited from likeing/unlikeing a message when logged out?

        """
        with self.client as c:
            msg = Message(id=123, text="test msg 1", user_id=234)

            db.session.add(msg)
            db.session.commit()

            res = c.post(f"/users/like/{123}")
            self.assertEqual(res.status_code, 302)
            likes = Likes.query.filter_by(user_id=123, message_id=123).all()
            self.assertEqual(likes, [])

            res = c.post(f"/users/like/{123}", follow_redirects=True)
            html = res.get_data(as_text=True)
            self.assertIn("Access unauthorized.", html)

    def test_like_own_msg(self):
        """
        Are you prohibited from likeing your own message?
        """
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 123

            msg = Message(id=234, text="test msg 1", user_id=123)

            db.session.add(msg)
            db.session.commit()

            res = c.post(f"/users/like/{234}")
            self.assertEqual(res.status_code, 302)
            likes = Likes.query.filter_by(user_id=123, message_id=234).all()
            self.assertEqual(likes, [])

            res = c.post(f"/users/like/{234}", follow_redirects=True)
            html = res.get_data(as_text=True)
            self.assertIn("You can&#39;t like your own message", html)
