from django.contrib.auth import get_user_model
from django.test import TestCase

from .qr import decode_token, is_sunday_token, make_sunday_token


class SundayQRPageTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_superuser(
            username='qr_staff', email='staff@example.com', password='secret123'
        )

    def test_permanent_qr_page_renders(self):
        self.client.force_login(self.user)
        response = self.client.get('/attendance/qr/sunday/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Permanent Sunday Attendance QR')
        self.assertContains(response, 'fbmi://attend/')
        self.assertTrue(is_sunday_token(decode_token(make_sunday_token())))

    def test_permanent_qr_page_requires_login(self):
        response = self.client.get('/attendance/qr/sunday/')
        self.assertEqual(response.status_code, 302)
