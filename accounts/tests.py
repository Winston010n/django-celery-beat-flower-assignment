from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import User
from .tasks import clean_inactive_users_task, send_daily_admin_report_task


class RegistrationTests(TestCase):
    @patch("accounts.views.send_welcome_email_task.delay")
    def test_registration_dispatches_welcome_task(self, send_task):
        response = APIClient().post(
            "/api/register/",
            {"username": "new-user", "email": "new@example.com", "password": "StrongPass123!"},
            format="json",
        )

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(username="new-user")
        send_task.assert_called_once_with(user.pk)


class UserTaskTests(TestCase):
    def test_cleanup_deletes_only_old_inactive_users(self):
        old_user = User.objects.create_user(username="old-inactive", password="x", is_active=False)
        old_user.date_joined = timezone.now() - timedelta(days=31)
        old_user.save(update_fields=["date_joined"])
        recent_user = User.objects.create_user(username="recent-inactive", password="x", is_active=False)
        active_user = User.objects.create_user(username="active", password="x", is_active=True)

        result = clean_inactive_users_task()

        self.assertEqual(result, "Удалено неактивных пользователей: 1")
        self.assertFalse(User.objects.filter(pk=old_user.pk).exists())
        self.assertTrue(User.objects.filter(pk=recent_user.pk).exists())
        self.assertTrue(User.objects.filter(pk=active_user.pk).exists())

    def test_admin_report_counts_each_role(self):
        User.objects.create_user(username="admin-user", password="x", role=User.Role.ADMIN)
        User.objects.create_user(username="moderator-user", password="x", role=User.Role.MODERATOR)
        User.objects.create_user(username="regular-user", password="x")

        with patch("builtins.print") as print_report:
            result = send_daily_admin_report_task()

        self.assertIn("ADMIN=1", result)
        self.assertIn("MODERATOR=1", result)
        self.assertIn("USER=1", result)
        print_report.assert_called_once_with(result)
