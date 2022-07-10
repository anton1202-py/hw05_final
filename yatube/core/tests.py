from django.test import TestCase


class ViewTestClass(TestCase):
    def test_error_page(self):
        """Проверяет, что статус ответа сервера - 404"""
        response = self.client.get('/nonexist-page/')
        self.assertEqual(response.status_code, 404)

    def test_use_error_template(self):
        """Проверяет, что используется шаблон core/404.html"""
        response = self.client.get('/nonexist-page/')
        self.assertTemplateUsed(response, 'core/404.html')