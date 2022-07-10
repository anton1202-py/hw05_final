from django.core.paginator import Paginator

POST_LIMIT = 10


def page_paginator(queryset, request):
    """"Функция для паджинации страниц"""
    paginator = Paginator(queryset, POST_LIMIT)
    page_number = request.GET.get('page')

    return paginator.get_page(page_number)
