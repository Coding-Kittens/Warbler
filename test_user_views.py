"""User View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_user_views.py

import os
from unittest import TestCase
from models import db, connect_db, Message, User, Likes, Follows


os.environ["DATABASE_URL"] = "postgresql:///warbler_test"
from app import app, CURR_USER_KEY

db.create_all()

app.config["WTF_CSRF_ENABLED"] = False


class UserViewTestCase(TestCase):
    """Test views for users."""

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

    def test_follower_page(self):
        """Can you see the follower page if logged in?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 123

            res = c.get("/users/123/followers", follow_redirects=True)
            html = res.get_data(as_text=True)
            self.assertIn("testuser", html)

    def test_loggedOut_follower_page(self):
        """Are you disallowed from visiting a user’s follower page if not logged in?"""
        with self.client as c:
            res = c.get("/users/123/followers", follow_redirects=True)
            html = res.get_data(as_text=True)
            self.assertIn("Access unauthorized.", html)

    def test_following_page(self):
        """Can you see the following page if logged in?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 123

            res = c.get("/users/123/following", follow_redirects=True)
            html = res.get_data(as_text=True)
            self.assertIn("testuser", html)

    def test_loggedOut_following_page(self):
        """Are you disallowed from visiting a user’s following page if not logged in?"""
        with self.client as c:
            res = c.get("/users/123/following", follow_redirects=True)
            html = res.get_data(as_text=True)
            self.assertIn("Access unauthorized.", html)

    def test_add_follower(self):
        """Can you add a follower when logged in?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 123

            res = c.post("/users/follow/234")
            self.assertEqual(res.status_code, 302)
            follows = Follows.query.filter_by(
                user_being_followed_id=234, user_following_id=123
            ).one()
            self.assertEqual(follows.user_being_followed_id, 234)
            self.assertEqual(follows.user_following_id, 123)

    def test_loggedOut_add_follower(self):
        """Are you prohibited from adding a follower when logged out?"""
        with self.client as c:
            res = c.post("/users/follow/234")
            self.assertEqual(res.status_code, 302)
            follows = Follows.query.filter_by(
                user_being_followed_id=234, user_following_id=123
            ).all()
            self.assertEqual(follows, [])

    def test_follow_yourself(self):
        """Are you prohibited from following yourself?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 123

            res = c.post("/users/follow/123", follow_redirects=True)
            html = res.get_data(as_text=True)
            self.assertIn("You can not follow yourself!", html)

    def test_add_invalid_follower(self):
        """Are you prohibited from following someone that does not exist?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 123

            # should return 404 if the user you are trying to follow does not exist
            res = c.post("/users/follow/400", follow_redirects=True)
            self.assertEqual(res.status_code, 404)

    def test_delete_follow(self):
        """Can you unfollow when logged in?"""
        with self.client as c:

            test_follower = Follows(user_being_followed_id=234, user_following_id=123)
            db.session.add(test_follower)
            db.session.commit()

            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 123

            res = c.post("/users/stop-following/234")
            self.assertEqual(res.status_code, 302)
            follows = Follows.query.filter_by(
                user_being_followed_id=234, user_following_id=123
            ).all()
            self.assertEqual(follows, [])

    def test_delete_invalid_follow(self):
        """Are you prohibited from unfollowing a user that doesn't exist?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 123

            # should return 404 if the user you are trying to unfollow does not exist
            res = c.post("/users/stop-following/400", follow_redirects=True)
            self.assertEqual(res.status_code, 404)

    def test_loggedOut_delete_follow(self):
        """Are you prohibited from unfollowing when logged out?"""
        with self.client as c:

            test_follower = Follows(user_being_followed_id=123, user_following_id=234)
            db.session.add(test_follower)
            db.session.commit()

            res = c.post("/users/stop-following/234")
            self.assertEqual(res.status_code, 302)
            follows = Follows.query.filter_by(
                user_being_followed_id=123, user_following_id=234
            ).one()
            self.assertEqual(follows.user_being_followed_id, 123)
            self.assertEqual(follows.user_following_id, 234)
