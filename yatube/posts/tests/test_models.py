from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
        )

    def test_models_have_correct_odject_names(self):
        """Проверяем, что у моделей корректно работает __str__."""
        model_str = {
            self.post: self.post.text[:15],
            self.group: self.group.title
        }
        for model, expected_values in model_str.items():
            with self.subTest(model=model):
                self.assertEqual(model.__str__(), expected_values, (
                    f'Ошибка метода __str__ в модели {type(model).__name__}'))
