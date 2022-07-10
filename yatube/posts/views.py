from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page
from .forms import CommentForm, PostForm
from .models import Group, Follow, Post, User
from .utils import page_paginator


@cache_page(20)
def index(request):
    """"Выводит шаблон главной страницы"""
    post = Post.objects.select_related('group', 'author')
    context = {
        'post': post,
        'page_obj': page_paginator(post, request)
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Выводит шаблон с группами постов"""
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    context = {
        'group': group,
        'posts': posts,
        'page_obj': page_paginator(posts, request)
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Выводит шаблон профайла пользователя"""
    user = get_object_or_404(User, username=username)
    amount = user.posts.all().count()
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user, author=user
        ).exists()
    else:
        following = False
    context = {
        'author': user,
        'amount': amount,
        'page_obj': page_paginator(user.posts.all(), request),
        'following': following,
        'profile': user
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Выводит шаблон поста"""
    post = get_object_or_404(Post.objects.select_related(
        'author',
        'group',
    ), id=post_id)
    posts_count = post.author.posts.all().count()
    form = CommentForm(request.POST or None)
    context = {
        'post': post,
        'group': post.group,
        'posts_count': posts_count,
        'form': form,
        'comments': post.comments.all(),
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Выводит шаблон страницы создания поста"""
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect('posts:profile', request.user)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """Выводит шаблон страницы редактирования поста"""
    post = get_object_or_404(Post, pk=post_id)
    user = post.author
    if request.user != user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(
        request, 'posts/create_post.html', {'is_edit': True, 'form': form}
    )


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post.objects.select_related(
        'author',
        'group',
    ), id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    user = request.user
    post = Post.objects.filter(author__following__user=user)
    context = {'page_obj': page_paginator(post, request)}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Функция для подписки на автора"""
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    """Функция для отписки от автора"""
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=username)
