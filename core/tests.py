import json
from django.test import TestCase, Client
from django.urls import reverse
from accounts.models import User
from members.models import Family, Member


class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'testpass123', role='super_admin')
        self.member_user = User.objects.create_user('member1', 'member@test.com', 'testpass123', role='member')

    def test_login_page_loads(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)

    def test_login_success(self):
        response = self.client.post(reverse('accounts:login'), {'username': 'admin', 'password': 'testpass123'})
        self.assertEqual(response.status_code, 302)

    def test_login_invalid(self):
        response = self.client.post(reverse('accounts:login'), {'username': 'admin', 'password': 'wrong'})
        self.assertEqual(response.status_code, 200)

    def test_logout(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('accounts:logout'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 302)

    def test_dashboard_accessible_when_logged_in(self):
        self.client.login(username='admin', password='testpass123')
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)


class MemberModelTests(TestCase):
    def test_member_number_auto_generated(self):
        member = Member.objects.create(
            first_name='John', last_name='Doe', gender='male'
        )
        self.assertTrue(member.member_number.startswith('FBMI-'))

    def test_member_str(self):
        member = Member.objects.create(
            first_name='John', last_name='Doe', gender='male'
        )
        self.assertIn('John Doe', str(member))


class MemberViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'testpass123', role='super_admin')
        self.client.login(username='admin', password='testpass123')

    def test_member_list_view(self):
        response = self.client.get(reverse('members:member-list'))
        self.assertEqual(response.status_code, 200)

    def test_member_create_view(self):
        response = self.client.get(reverse('members:member-create'))
        self.assertEqual(response.status_code, 200)

    def test_member_create_post(self):
        data = {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'gender': 'female',
            'phone': '0712345678',
            'email': 'jane@test.com',
            'membership_status': 'active',
            'marital_status': 'single',
            'membership_type': 'full',
        }
        response = self.client.post(reverse('members:member-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Member.objects.filter(email='jane@test.com').exists())

    def test_member_detail_view(self):
        member = Member.objects.create(first_name='Test', last_name='User', gender='male')
        response = self.client.get(reverse('members:member-detail', kwargs={'pk': member.pk}))
        self.assertEqual(response.status_code, 200)

    def test_member_edit_view(self):
        member = Member.objects.create(first_name='Test', last_name='User', gender='male')
        response = self.client.get(reverse('members:member-update', kwargs={'pk': member.pk}))
        self.assertEqual(response.status_code, 200)

    def test_member_delete_view(self):
        member = Member.objects.create(first_name='Test', last_name='Delete', gender='male')
        response = self.client.post(reverse('members:member-delete', kwargs={'pk': member.pk}))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Member.objects.filter(pk=member.pk).exists())


class FamilyViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = User.objects.create_superuser('admin', 'admin@test.com', 'testpass123', role='super_admin')
        self.client.login(username='admin', password='testpass123')

    def test_family_list_view(self):
        response = self.client.get(reverse('members:family-list'))
        self.assertEqual(response.status_code, 200)

    def test_family_create(self):
        data = {'name': 'Test Family', 'address': '123 Test St', 'phone': '0712345678'}
        response = self.client.post(reverse('members:family-create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Family.objects.filter(name='Test Family').exists())


class SeedDataLinkingTests(TestCase):
    """The member portal is driven by Member.user. Seed data must link them."""

    def test_every_seeded_member_gets_a_login(self):
        from django.core.management import call_command
        from io import StringIO

        call_command('seed_data', stdout=StringIO())

        unlinked = Member.objects.filter(user__isnull=True)
        self.assertEqual(
            unlinked.count(), 0,
            f'Seeded members without a login account: {list(unlinked)}',
        )

    def test_seeded_member_login_reaches_portal(self):
        from django.core.management import call_command
        from io import StringIO
        import json

        call_command('seed_data', stdout=StringIO())

        response = self.client.post(
            '/api/login/',
            data=json.dumps({'username': 'member1', 'password': 'test123'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        token = response.json()['token']
        self.assertIsNotNone(response.json().get('member'), 'Login returned no member profile')

        portal = self.client.get(
            '/api/portal/', headers={'authorization': f'Token {token}'}
        )
        self.assertEqual(portal.status_code, 200)
        self.assertIsNotNone(portal.json().get('member'))


class MemberPortalApiTests(TestCase):
    def setUp(self):
        from services.models import Service
        from events.models import Event
        from django.utils import timezone

        self.user = User.objects.create_user('member1', 'member@test.com', 'testpass123', role='member')
        self.member = Member.objects.create(
            first_name='John', last_name='Doe', gender='male', user=self.user
        )
        self.service = Service.objects.create(
            name='Sunday Service', date=timezone.now().date(),
            start_time='09:00', end_time='12:00', location='Main Hall',
        )
        self.event = Event.objects.create(
            name='Test Event', date=timezone.now().date(), location='Main Hall', capacity=10
        )
        response = self.client.post(
            '/api/login/',
            data=json.dumps({'username': 'member1', 'password': 'testpass123'}),
            content_type='application/json',
        )
        self.token = response.json()['token']
        self.headers = {'authorization': f'Token {self.token}'}

    def test_service_check_in(self):
        response = self.client.post(f'/api/services/{self.service.pk}/attend/', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get('checked_in'))

    def test_event_registration(self):
        response = self.client.post(f'/api/events/{self.event.pk}/register/', headers=self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get('registered'))

    def test_endpoints_require_token(self):
        self.assertEqual(self.client.get('/api/portal/').status_code, 401)


class PermissionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.member_user = User.objects.create_user('member1', 'member@test.com', 'testpass123', role='member')

    def test_member_cannot_access_admin(self):
        self.client.login(username='member1', password='testpass123')
        response = self.client.get(reverse('members:member-create'))
        self.assertIn(response.status_code, [302, 403])

    def test_public_pages_accessible(self):
        response = self.client.get(reverse('public:home'))
        self.assertEqual(response.status_code, 200)

    def test_contact_page_accessible(self):
        response = self.client.get(reverse('public:contact'))
        self.assertEqual(response.status_code, 200)
