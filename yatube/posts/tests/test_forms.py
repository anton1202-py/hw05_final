from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings, TestCase
from django.urls import reverse

import shutil
import tempfile
from http import HTTPStatus

from posts.forms import PostForm
from posts.models import Comment, Group, Post


User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def body_test(self, first_object, form_data):
        """Проверка полей поста."""
        self.assertEqual(first_object.text, form_data['text'])
        self.assertEqual(
            first_object.author.username, self.post.author.username)
        self.assertEqual(first_object.group.id, form_data['group'])
        self.assertEqual(
            first_object.image.name, f"posts/{form_data['image'].name}"
        )

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый текст поста',
            'image': uploaded,
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse((
            'posts:profile'), args={self.user.username}))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        # Проверяем, что все поля создаются правильно
        first_object = response.context['page_obj'].object_list[0]
        self.body_test(first_object, form_data)

    def test_cant_create_post_without_text(self):
        """Проверим, что пост не создастся, если не вводить текст"""
        posts_count = Post.objects.count()
        form_data = {'text': ''}
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_edit_post(self):
        """Валидная форма редактирует запись в Post."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded_2 = SimpleUploadedFile(
            name='new.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Тестовый отредактированный текст',
            'group': self.group.id,
            'image': uploaded_2
        }
        response = self.authorized_client.post(
            reverse((
                'posts:post_edit'), args={self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse((
            'posts:post_detail'), args={self.post.id}))
        self.assertEqual(Post.objects.count(), posts_count)
        # Проверим, что все поля редактируются правильно
        first_object = response.context['post']
        self.body_test(first_object, form_data)

    def test_cant_edit_post_without_text(self):
        """Проверим, что нельзя сохранить пост без текста"""
        posts_count = Post.objects.count()
        form_data = {
            'text': ''
        }
        response = self.authorized_client.post(
            reverse((
                'posts:post_edit'), args={self.post.id}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_comment_show_up_with_authorized_user(self):
        """Комментировать посты может только авторизованный пользователь.
        После успешной отправки, комментарий появляется на странице поста."""
        # Подсчитаем количество комметариев
        comments_count = Comment.objects.count()
        form_data = {
            'text': 'Новый комментарий для поста',
        }
        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse((
                'posts:add_comment'), kwargs={'post_id': f'{self.post.id}'}),
            data=form_data,
            follow=True
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse((
            'posts:post_detail'), args=[f'{self.post.id}']))
        # Проверяем, увеличилось ли число комментариев
        self.assertEqual(Comment.objects.count(), comments_count + 1)
