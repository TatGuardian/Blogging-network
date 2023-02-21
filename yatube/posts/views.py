from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from yatube.settings import PER_PAGE
from .forms import CommentForm, PostForm
from .models import Group, Post, User, Follow
from .utils import page
from django.views.decorators.cache import cache_page


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    page_obj = page(request, post_list, PER_PAGE)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = Post.objects.all().filter(
        group=group)
    page_obj = page(request, posts, PER_PAGE)
    context = {
        'page_obj': page_obj,
        'group': group,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):

    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()
    page_obj = page(request, post_list, PER_PAGE)
    context = {
        'author': author,
        'page_obj': page_obj,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    context = {
        'post': post,
        'comments': post.comments.all(),
        'form': CommentForm
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        temp_form = form.save(commit=False)
        temp_form.author = request.user
        temp_form.save()
        return redirect('posts:profile', temp_form.author)
    data = {
        'form': form,
    }
    return render(request, 'posts/post_create.html', data)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect(
            'posts:post_detail', post_id
        )
    data = {
        'form': form,
        'is_edit': True,
        'post': post
    }
    return render(request, 'posts/post_create.html', data)


@login_required
def add_comment(request, post_id):
    # Получите пост и сохраните его в переменную post.
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, pk=post_id)
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    title = 'Публикации избранных авторов'
    posts = Post.objects.filter(author__following__user=request.user)
    page_obj = page(request, posts, PER_PAGE)
    context = {
        'title': title,
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    follow_author = get_object_or_404(User, username=username)
    if follow_author != request.user and (
        not request.user.follower.filter(author=follow_author).exists()
    ):
        Follow.objects.create(
            user=request.user,
            author=follow_author
        )
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    follow_author = get_object_or_404(User, username=username)
    data_follow = request.user.follower.filter(author=follow_author)
    if data_follow.exists():
        data_follow.delete()
    return redirect('posts:profile', username)
