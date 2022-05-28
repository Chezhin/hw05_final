from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page

from .forms import CommentForm, PostForm
from .get_page_context import get_page_context
from .models import Follow, Group, Post

User = get_user_model()


@cache_page(20, key_prefix='index_page')
def index(request) -> HttpResponse:
    """Передать в шаблон index.html объекты модели Post."""
    posts = Post.objects.all()
    context = {
        'page_obj': get_page_context(request, posts)
    }
    return render(request, 'posts/index.html', context)


def group_list(request, slug) -> HttpResponse:
    """Передать в шаблон group_list.html объекты модели Post."""
    group = get_object_or_404(Group, slug=slug)
    posts = group.group_posts.all()
    context = {
        'group': group,
        'page_obj': get_page_context(request, posts),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username) -> HttpResponse:
    author = get_object_or_404(User, username=username)
    posts = author.posts.select_related('author', 'group')
    user = request.user
    following = user.is_authenticated and author.following.exists()
    context = {
        'following': following,
        'author': author,
        'page_obj': get_page_context(request, posts)
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id) -> HttpResponse:
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(files=request.FILES or None)
    comments = post.comments.all()
    context = {
        'post': post,
        'form': form,
        'comments': comments
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request) -> HttpResponse:
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', username=request.user)
        return render(request, 'posts/post_create.html', {'form': form})
    form = PostForm()
    return render(request, 'posts/post_create.html', {'form': form})


@login_required
def post_edit(request, post_id) -> HttpResponse:
    post = get_object_or_404(Post, id=post_id)
    if post.author != request.user:
        return redirect('posts:post_detail', post_id)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    context = {
        'form': form,
        'post_id': post_id,
        'is_edit': True
    }
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    return render(request, 'posts/post_create.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    context = {'page_obj': get_page_context(request, posts)}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    if author != user:
        Follow.objects.get_or_create(user=user, author=author)
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    Follow.objects.get(user=user, author__username=username).delete()
    return redirect('posts:profile', username=username)
