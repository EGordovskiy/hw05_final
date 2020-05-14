from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, request
from .models import Group, Post, User, Comment, Follow
from .forms import PostForm, Group, CommentForm
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from posts.models import Comment
from django.views.decorators.cache import cache_page



def index(request):
    post_list = Post.objects.order_by("-pub_date").all()
    paginator = Paginator(post_list, 10) # показывать по 10 записей на странице.
    page_number = request.GET.get('page') # переменная в URL с номером запрошенной страницы
    page = paginator.get_page(page_number) # получить записи с нужным смещением
    return render(request, 'index.html', {'page': page, 'paginator': paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)

    post_list = Post.objects.filter(group=group).order_by("-pub_date").all()
    paginator = Paginator(post_list, 10)

    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "group.html", {"group": group, "page": page, "paginator": paginator})


@login_required
def new_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST or None, files=request.FILES or None)
        if form.is_valid():
            Post.objects.create(
                text=form.cleaned_data['text'],
                author=request.user,
                group=form.cleaned_data['group'],
                image=form.cleaned_data['image']
            )
            return redirect('/')
    form = PostForm(request.POST or None, files=request.FILES or None)
    return render(request, "new.html", {"form" : form})


def profile(request, username):
    author = get_object_or_404(User,username=username)
    post_list = Post.objects.filter(author=author).order_by("-pub_date").all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "profile.html", {"page" : page, "paginator": paginator, "author" : author, "post_list" : post_list, "username":username})


def post_view(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id)
    author = get_object_or_404(User, username=username)
    post_count = Post.objects.filter(author=author).count()
    comment_count = Comment.objects.filter(post=post).count()
    form = CommentForm()
    items = Comment.objects.filter(post=post)
    return render(request, "post.html", {
        "post" : post, "author" : author, "post_count": post_count, "form":form, "items":items, "comment_count":comment_count
        })


@login_required
def post_edit(request, username, post_id):
    profile = get_object_or_404(User, username=username)
    post = get_object_or_404(Post, pk=post_id, author=profile)
    if request.user != profile:
        return redirect("post", username=request.user.username, post_id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)

    if request.method == "POST":
        if form.is_valid():
            form.save()
            return redirect("post", username=request.user.username, post_id=post_id)
    return render(request, "post_edit.html", {"form": form, "post":post})


def page_not_found(request, exception):
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, id=post_id)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect("post", username=request.user, post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.select_related("author") \
        .filter(author__following__in=Follow.objects.filter(user=request.user)).order_by('-pub_date').all()
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)
    return render(request, "follow.html", {"page": page, "paginator": paginator})


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if Follow.objects.filter(user=request.user, author=author).exists():
        return redirect("profile", username=username)
    else:
        if request.user.id != author.id:
            Follow.objects.create(user=request.user, author=author)
    return redirect("profile", username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    one = Follow.objects.filter(user=request.user, author=author).first()
    if one:
        one.delete()
    return redirect("profile/", username=username)
