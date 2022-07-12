from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

import shutil
import tempfile

from posts.models import Group, Follow, Post


User = get_user_model()


TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class TaskPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug-test',
            description='Тестовое название'
        )
        cls.post = Post.objects.create(
            text='Тестовый пост',
            author=cls.user,
            group=cls.group,
            image=cls.uploaded
        )
        cls.INDEX = ('posts:index', 'posts/index.html', None)
        cls.GROUP = (
            'posts:group_list',
            'posts/group_list.html',
            (cls.post.group.slug,)
        )
        cls.PROFILE = (
            'posts:profile',
            'posts/profile.html',
            (cls.post.author.username,)
        )
        cls.DETAIL = (
            'posts:post_detail',
            'posts/post_detail.html',
            (cls.post.id,)
        )
        cls.EDIT = (
            'posts:post_edit',
            'posts/create_post.html',
            (cls.post.id,)
        )
        cls.CREATE = (
            'posts:post_create',
            'posts/create_post.html',
            None
        )
        cls.templates_tuple_view = [
            cls.INDEX, cls.GROUP, cls.PROFILE,
            cls.DETAIL, cls.EDIT, cls.CREATE,
        ]
        cls.pages_for_post = [cls.INDEX, cls.GROUP, cls.PROFILE]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.user_author = User.objects.get(username='auth')
        self.post_author = Client()
        self.post_author.force_login(self.user_author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответсвующий шаблон"""
        for reverse_name, templates, argument in self.templates_tuple_view:
            with self.subTest(reverse_name=reverse_name):
                response = self.post_author.get(reverse(
                    reverse_name,
                    args=argument
                ))
                self.assertTemplateUsed(response, templates)

    def body_test(self, first_object):
        """Проверка полей поста."""
        self.assertEqual(first_object.text, self.post.text)
        self.assertEqual(
            first_object.author.username, self.post.author.username)
        self.assertEqual(first_object.group.title, self.post.group.title)
        self.assertEqual(first_object.image.name, self.post.image.name)

    def group_fields_test(self, first_object):
        """Проверка полей группы."""
        self.assertEqual(first_object.group.title, self.post.group.title)
        self.assertEqual(
            first_object.group.slug, self.post.group.slug)
        self.assertEqual(
            first_object.group.description,
            self.post.group.description
        )

    def test_index_page_show_correct_context(self):
        """
        Шаблон index сформирован с правильным контекстом.
        Проверяем список постов и вывод картинки
        """
        response = self.post_author.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.body_test(first_object)

    def test_group_list_page_show_correct_context(self):
        """
        Шаблон /group/test-slug/ сформирован с правильным контекстом.
        Проверяем список постов с картинками, отфильтрованных по группе
        """
        response = self.post_author.get(reverse(
            'posts:group_list', args={self.group.slug}))
        first_object = response.context['page_obj'][0]
        self.body_test(first_object)
        self.group_fields_test(first_object)

    def test_profile_page_show_correct_context(self):
        """
        Шаблон posts/profile.html сформирован с правильным контекстом.
        Проверяем список постов с картинками, отфильтрованных по автору
        """
        response = self.post_author.get(
            reverse('posts:profile', args={self.post.author.username}))
        first_object = response.context['page_obj'][0]
        self.body_test(first_object)

    def test_post_detail_page_show_correct_context(self):
        """
        Шаблон posts/post_detail.html сформирован с правильным контекстом.
        Проверяем один пост и картинку, отфильтрованный по id
        """
        response = self.post_author.get(reverse(
            'posts:post_detail', args={self.post.id}))
        first_object = response.context.get('post')
        self.body_test(first_object)
        self.group_fields_test(first_object)

    def test_post_create_edit_page_show_correct_context(self):
        """
        Шаблон posts/post_create.html сформирован с правильным контекстом.
        Проверяем форму редактирования поста, отфильтрованного по id
        """
        response = self.post_author.get(
            reverse('posts:post_edit', args={self.post.id}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_create_page_show_correct_context(self):
        """
        Шаблон posts/post_detail.html сформирован с правильным контекстом.
        Проверяем форму создания поста
        """
        response = self.post_author.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_check_post_on_create(self):
        """
        Проверяем, что при создании поста с группой этот пост появляется
        на главной странице, на странице группы, на странице профайла.
        """
        Post.objects.create(
            text='Новый тестовый пост',
            author=self.user,
            group=self.group,
        )
        for reverse_name, _, argument in self.pages_for_post:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse(
                    reverse_name,
                    args=argument
                ))
                count_posts = len(response.context['page_obj'])
                self.assertEqual(count_posts, 2)

    def test_group_post(self):
        """ Проверка на ошибочное попадание поста не в ту группу. """
        error_group = Group.objects.create(
            title='Новая группа',
            slug='error-slug',
            description='Новое описание',
        )
        response = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': error_group.slug}
            )
        )
        context = response.context['page_obj'].object_list
        self.assertNotIn(self.post, context)

    def test_cache(self):
        """Тестируем работу кеша"""
        test_post = Post.objects.create(
            text='Тестируем кэш',
            group=self.group,
            author=self.user,
        )
        var_test_cache = reverse('posts:index')
        post_content = self.post_author.get(var_test_cache).content
        test_post.delete()
        delete_post_but_in_cache = self.post_author.get(var_test_cache).content
        cache.clear()
        content_after_cache_clear = self.post_author.get(
            var_test_cache).content
        self.assertEqual(
            post_content, delete_post_but_in_cache
        )
        self.assertNotEqual(
            post_content, content_after_cache_clear
        )


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_user = User.objects.create_user(username='user')
        cls.user_author = User.objects.create_user(username='author')
        cls.FOLLOW_INDEX = reverse('posts:follow_index')
        cls.PROFILE_FOLLOW_AUTHOR = reverse(
            'posts:profile_follow',
            args={cls.user_author.username}
        )
        cls.PROFILE_UNFOLLOW_AUTHOR = reverse(
            'posts:profile_unfollow',
            args={cls.user_author.username}
        )
        cls.PROFILE_FOLLOW_USER = reverse(
            'posts:profile_follow',
            args={cls.user_user.username}
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        self.user = Client()
        self.author = Client()
        self.user.force_login(self.user_user)
        self.author.force_login(self.user_author)

    def test_authenticated_user_can_follow(self):
        """Залогиненный пользователь может подписаться на авторов,
        при этом нельзя подписаться, если он уже подписан"""
        follow_count = Follow.objects.count()
        self.user.get(self.PROFILE_FOLLOW_AUTHOR)
        self.user.get(self.PROFILE_FOLLOW_AUTHOR)
        self.assertEqual(Follow.objects.count(), follow_count + 1)

    def test_authenticated_user_can_unfollow(self):
        """Залогиненный пользователь может отписаться от авторов,
        при этом нельзя отписаться, если он уже отписан"""
        follow_count = Follow.objects.count()
        self.user.get(self.PROFILE_FOLLOW_AUTHOR)
        self.user.get(self.PROFILE_UNFOLLOW_AUTHOR)
        self.user.get(self.PROFILE_UNFOLLOW_AUTHOR)
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_authenticated_user_canе_follow_himself(self):
        """Залогиненный пользователь не может подписаться на самого себя"""
        follow_count = Follow.objects.count()
        self.user.get(self.PROFILE_FOLLOW_USER)
        self.assertEqual(Follow.objects.count(), follow_count)

    def test_profile_follow(self):
        """Проверяем, что пост возникает на странице подписки."""
        Post.objects.create(
            text='Тестовый пост подписки',
            author=self.user_author
        )
        Follow.objects.create(user=self.user_user, author=self.user_author)
        self.user.get(self.PROFILE_FOLLOW_USER)
        response = self.user.get(self.FOLLOW_INDEX)
        self.assertEqual(
            response.context['page_obj'].object_list[0],
            Post.objects.latest('id')
        )


class PaginatorViewsTest(TestCase):
    """Тест паджинатора"""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='slug-test',
            description='Тестовое название'
        )
        for i in range(13):
            Post.objects.create(
                author=cls.user,
                text=f'{i+1}й тестовый длинююююющий пост',
                group=cls.group
            )

    def setUp(self):
        cache.clear()
        self.user_author = User.objects.get(username='auth')
        self.post_author = Client()
        self.post_author.force_login(self.user_author)

    def test_first_page_contains_ten_record(self):
        response = self.post_author.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        response = self.post_author.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 3)
