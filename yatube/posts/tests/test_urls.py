from django.core.cache import cache
from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from http import HTTPStatus

from posts.models import Group, Post

User = get_user_model()


class TaskURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
        )
        cls.INDEX = ('/', 'posts/index.html')
        cls.GROUP = (f'/group/{cls.post.group.slug}/', 'posts/group_list.html')
        cls.PROFILE = (
            f'/profile/{cls.post.author.username}/',
            'posts/profile.html',
        )
        cls.DETAIL = (f'/posts/{cls.post.id}/', 'posts/post_detail.html')
        cls.EDIT = (f'/posts/{cls.post.id}/edit/', 'posts/create_post.html')
        cls.CREATE = ('/create/', 'posts/create_post.html')
        cls.NOTFOUND = ('/unexistint_page/', None)
        cls.check_status_and_template_author = [
            cls.INDEX, cls.GROUP, cls.PROFILE, cls.DETAIL, cls.EDIT, cls.CREATE
        ]
        cls.check_status_and_template_authorized = [
            cls.INDEX, cls.GROUP, cls.PROFILE, cls.DETAIL, cls.CREATE
        ]
        cls.check_status_code_all_users = [
            cls.INDEX, cls.GROUP, cls.PROFILE, cls.DETAIL,
        ]
        cls.check_create_edit_page_guest_user = [cls.EDIT, cls.CREATE]

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user = User.objects.create_user(username='Noname')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author = User.objects.get(username='auth')
        self.post_author = Client()
        self.post_author.force_login(self.post.author)

    def test_urls_address_is_available_all_users(self):
        """Проверка доступности URL-адресов всем пользователям"""
        for address_tuple, *_ in self.check_status_code_all_users:
            with self.subTest(address=address_tuple):
                response = self.guest_client.get(address_tuple).status_code
                self.assertEqual(response, HTTPStatus.OK)

    def test_urls_address_is_available_authorized_users(self):
        """
        Проверка: не авторизованный пользователь
        не может создать и редактировать пост.
        """
        for address_tuple, *_ in self.check_create_edit_page_guest_user:
            with self.subTest(address=address_tuple):
                response = self.guest_client.get(address_tuple).status_code
                self.assertEqual(response, HTTPStatus.FOUND)

    def test_redirect_edit_for_guest_user(self):
        """
        Проверка: не авторизованный пользователь при попытке создать
        и отредактировать пост перенаправляется на страницу логина
        """
        for url, _ in self.check_create_edit_page_guest_user:
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(response, f'/auth/login/?next={url}')

    def test_urls_address_is_available_author_users(self):
        """Проверка доступности URL-адресов автору постов"""
        for address_tuple, *_ in self.check_status_and_template_author:
            with self.subTest(address=address_tuple):
                response = self.post_author.get(address_tuple).status_code
                self.assertEqual(response, HTTPStatus.OK)

    def test_urls_address_is_available_authorized_user(self):
        """Проверка доступности URL-адресов авторизованному пользователю"""
        for address_tuple, *_ in self.check_status_and_template_authorized:
            with self.subTest(address=address_tuple):
                response = self.post_author.get(address_tuple).status_code
                self.assertEqual(response, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответсвующий шаблон."""
        for address, template in self.check_status_and_template_author:
            with self.subTest(address=address):
                response = self.post_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_check_not_found_page(self):
        """
        ПРоверяем, страница /unexistint_page/
        недоступна для всех пользователей
        """
        users_list = [
            self.guest_client,
            self.authorized_client,
            self.post_author
        ]
        for user in users_list:
            with self.subTest(address=user):
                response = user.get(self.NOTFOUND[0]).status_code
                self.assertEqual(response, HTTPStatus.NOT_FOUND)
