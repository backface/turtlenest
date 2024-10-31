import json
import base64
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.projects.models import Project
from apps.classrooms.models import Group, SelectedProject
from allauth.account.models import EmailAddress


User = get_user_model()

class APITestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='snap$testpass')
        self.user_email = EmailAddress.objects.create(user=self.user, email='test@example.com', primary=True, verified=True)
        self.user2 = User.objects.create_user(username='testuse2r', email='test@example.com', password='snap$testpass')
        self.project = Project.objects.create(user=self.user, name='testproject', is_public=True)

    def test_init(self):
        response = self.client.post('/api/v1/init')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {})

    def test_current_user(self):
        self.client.login(username='testuser', password='snap$testpass')
        response = self.client.get('/api/v1/users/c')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['username'], 'testuser')

    def test_login_user(self):
        response = self.client.post('/api/v1/users/testuser/login', data='testpass', content_type='text/plain')
        self.assertEqual(response.status_code, 200)
        self.assertIn('logged in', response.json()['message'])

    def test_signup_user(self):
        response = self.client.post('/api/v1/users/newuser?email=newuser@example.com&password=newpass&password_repeat=newpass', 
            content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Account created', response.json()['title'])

        response = self.client.post('/api/v1/users/newuser/login', data='newpass', content_type='text/plain')
        self.assertEqual(response.status_code, 200)
        self.assertIn('logged in', response.json()['message'])


    def test_resend_verification(self):
        response = self.client.get('/api/v1/users/testuser/resendverification')
        self.assertEqual(response.status_code, 200)

    def test_request_password_change(self):
        response = self.client.post('/api/v1/users/testuser/password_reset')
        self.assertEqual(response.status_code, 200)
        self.assertIn('password reset link', response.json()['message'])

    def test_change_password(self):
        self.client.login(username='testuser', password='snap$testpass')
        response = self.client.post('/api/v1/users/testuser/newpassword?oldpassword=testpass&newpassword=newpass&password_repeat=newpass', content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('Password changed', response.json()['title'])

    def test_logout_user(self):
        self.client.login(username='testuser', password='snap$testpass')
        response = self.client.post('/api/v1/logout')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['redirect'], '/')

    def test_save_load_delete_project(self):
        self.client.login(username='testuser', password='snap$testpass')
        data = {
            'xml': '<project name="testfile" app="Snap! 9.0, https://snap.berkeley.edu" version="2"><notes>a test note</notes><thumbnail>data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAKAAAAB4CAYAAAB1ovlvAAACqElEQVR4Xu3XMY7aUABF0e99QA/LAYkN0bAgEKuBjUBBRqSYYmaSKIWvZB3Xlp58/xHG0+vjGi4FogITgFF5s+8CAIKQFgAwzW8cQAbSAgCm+Y0DyEBaAMA0v3EAGUgLAJjmNw4gA2kBANP8xgFkIC0AYJrfOIAMpAUATPMbB5CBtACAaX7jADKQFgAwzW8cQAbSAgCm+Y0DyEBaAMA0v3EAGUgLAJjmNw4gA2kBANP8xgFkIC0AYJrfOIAMpAUATPMbB5CBtACAaX7jADKQFgAwzW8cQAbSAgCm+Y0DyEBaAMA0v3EAGUgLAJjmNw4gA2kBANP8xgFkIC0…7"></list></sounds><variables></variables><blocks></blocks><scripts></scripts><sprites select="1"><sprite name="Sprite" idx="1" x="0" y="0" heading="90" scale="1" volume="100" pan="0" rotation="1" draggable="true" costume="0" color="80,80,80,1" pen="tip" id="12"><costumes><list struct="atomic" id="13"></list></costumes><sounds><list struct="atomic" id="14"></list></sounds><blocks></blocks><variables></variables><scripts></scripts></sprite></sprites></stage><variables></variables></scene></scenes></project>',
            'notes': 'a test notes',
            'thumbnail': 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAKAAAAB4CAYAAAB1ovlvAAACqElEQVR4Xu3XMY7aUABF0e99QA/LAYkN0bAgEKuBjUBBRqSYYmaSKIWvZB3Xlp58/xHG0+vjGi4FogITgFF5s+8CAIKQFgAwzW8cQAbSAgCm+Y0DyEBaAMA0v3EAGUgLAJjmNw4gA2kBANP8xgFkIC0AYJrfOIAMpAUATPMbB5CBtACAaX7jADKQFgAwzW8cQAbSAgCm+Y0DyEBaAMA0v3EAGUgLAJjmNw4gA2kBANP8xgFkIC0AYJrfOIAMpAUATPMbB5CBtACAaX7jADKQFgAwzW8cQAbSAgCm+Y0DyEBaAMA0v3EAGUgLAJjmNw4gA2kBANP8xgFkIC0AYJrfOIAMpAUATPMbB5CBtACAaX7jADKQFgAwzW8cQAbSAgCm+Y0DyEBaAMA0v3EAGUgLAPhD/u12O47H4zgcDukBLX0cwD+c8H6/H6/X633H7XYb1+t1rNfrpZuY9fkA/Evu3W735Y5pmsbz+Rzn83nWw1riGID/CfDxeIzL5bJEE7M+E4D/+Aq+3+/vV/BqtZr1gJY+BuAPJ7zZbMbpdBrfvYKXjmLO5wNwztq2vv6f/vjK+/2Z51IgKOAXMIhu8rMAgDSkBQBM8xsHkIG0AIBpfuMAMpAWADDNbxxABtICAKb5jQPIQFoAwDS/cQAZSAsAmOY3DiADaQEA0/zGAWQgLQBgmt84gAykBQBM8xsHkIG0AIBpfuMAMpAWADDNbxxABtICAKb5jQPIQFoAwDS/cQAZSAsAmOY3DiADaQEA0/zGAWQgLQBgmt84gAykBQBM8xsHkIG0AIBpfuMAMpAWADDNbxxABtICAKb5jQPIQFoAwDS/cQAZSAsAmOY3DiADaQEA0/zGAWQgLQBgmt84gAykBQBM8xsHkIG0AIBpfuMAMpAWADDNb/wXK14Ct+2fpIIAAAAASUVORK5CYII='
        }
        response = self.client.post('/api/v1/projects/testuser/newproject', data=json.dumps(data), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        self.assertIn('project newproject saved', response.json()['message'])

        response = self.client.get('/api/v1/projects/testuser')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['projects']), 2)

        response = self.client.get('/api/v1/projects/testuser/newproject/thumbnail')
        self.assertEqual(response.status_code, 200)
        self.assertIn('data:image/png;base64,', response.content.decode())

        response = self.client.delete('/api/v1/projects/testuser/newproject')
        self.assertEqual(response.status_code, 200)
        self.assertIn('project newproject has been deleted', response.json()['message'])        

    def test_get_users_projects(self):
        self.client.login(username='testuser', password='snap$testpass')
        response = self.client.get('/api/v1/projects/testuser')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['projects']), 1)

    # def test_get_project_thumbnail(self):
    #     response = self.client.get('/api/v1/projects/testuser/newproject/thumbnail')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertIn('data:image/png;base64,', response.content.decode())

    # def test_get_project(self):
    #     response = self.client.get('/api/v1/projects/testuser/newproject')
    #     self.assertEqual(response.status_code, 200)
    #     self.assertIn('<snapdata>', response.content.decode())

    def test_get_project_versions(self):
        response = self.client.get('/api/v1/projects/testuser/testproject/versions')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_set_project_visibility(self):
        self.client.login(username='testuser', password='snap$testpass')
        response = self.client.post('/api/v1/projects/testuser/testproject/metadata?ispublic=false&ispublished=false')
        self.assertEqual(response.status_code, 200)
        self.assertIn('project testproject updated', response.json()['message'])

        response = self.client.post('/api/v1/logout')
        self.assertEqual(response.status_code, 200)

        self.client.login(username='testuser2', password='snap$testpass')
        response = self.client.get('/api/v1/projects/testuser')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json()['projects']), 0)        

    def test_delete_project(self):
        self.client.login(username='testuser', password='snap$testpass')
        response = self.client.delete('/api/v1/projects/testuser/testproject')
        self.assertEqual(response.status_code, 200)
        self.assertIn('project testproject has been deleted', response.json()['message'])

