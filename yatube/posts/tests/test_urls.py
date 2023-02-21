from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    """Создаем тестовый пост и группу."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='leo')
        cls.group = Group.objects.create(
            title='Группа поклонников графа',
            slug='tolstoi',
            description='Что-то о группе'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Новый пост без группы'
        )

    def setUp(self):
        self.guest_client = self.client
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_urls_available_unauth(self):
        """URL-адрес использует соответствующий шаблон (unauthorized)."""

        templates_url_names_unauth = {
            '/': HTTPStatus.OK,
            f'/group/{StaticURLTests.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user.username}/': HTTPStatus.OK,
            f'/posts/{StaticURLTests.post.pk}/': HTTPStatus.OK,
            f'/posts/{StaticURLTests.post.pk}/edit/': HTTPStatus.FOUND,
            '/create/': HTTPStatus.FOUND,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }

        # checking availability for unauthorized client
        for address, code in templates_url_names_unauth.items():
            with self.subTest():
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, code, msg=f'{address}')

    def test_urls_available_auth(self):
        """URL-адрес использует соответствующий шаблон (authorized)."""

        # checking availability for authorized client
        templates_url_names_auth = {
            '/': HTTPStatus.OK,
            f'/group/{StaticURLTests.group.slug}/': HTTPStatus.OK,
            f'/profile/{self.user.username}/': HTTPStatus.OK,
            f'/posts/{StaticURLTests.post.pk}/': HTTPStatus.OK,
            f'/posts/{StaticURLTests.post.pk}/edit/': HTTPStatus.FOUND,
            '/create/': HTTPStatus.OK,
            '/unexisting_page/': HTTPStatus.NOT_FOUND,
        }
        for address, code in templates_url_names_auth.items():
            with self.subTest():
                response = self.authorized_client.get(address)
                self.assertEqual(response.status_code, code, msg=f'{address}')
