# Функция reverse_lazy позволяет получить URL по параметрам функции path()
# Берём, тоже пригодится
from django.urls import reverse_lazy
# Импортируем CreateView, чтобы создать ему наследника
from django.views.generic import CreateView

# Импортируем класс формы, чтобы сослаться на неё во view-классе
from .forms import CreationForm


class SignUp(CreateView):
    # form_class — из какого класса взять форму
    form_class = CreationForm
    # success_url — куда перенаправить пользователя
    # после успешной отправки формы
    # После успешной регистрации перенаправляем пользователя на главную.
    success_url = reverse_lazy('posts:index')
    # template_name — имя шаблона, куда будет передана переменная
    # form с объектом HTML-формы. Всё это чем-то похоже на вызов
    # функции render() во view-функции.
    template_name = 'users/signup.html'
