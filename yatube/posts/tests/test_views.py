from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import caches
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Comment, Group, Post, Follow

User = get_user_model()
cache = caches['default']


class TestPosts(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='Test group',
            description='test description',
            slug='test-group'
        )
        cls.group2 = Group.objects.create(
            title='Test group2',
            description='test description',
            slug='test-group2'
        )
        cls.user = User.objects.create_user(username='test user')
        cls.post = Post.objects.create(
            text='test post',
            author=cls.user,
            group=cls.group
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.user,
            text='test comment'
        )
        cls.index_url = reverse('posts:index')
        cls.follow_url = reverse('posts:follow_index')
        cls.group_url = reverse(
            'posts:group_list',
            kwargs={'slug': cls.group.slug}
        )
        cls.profile_url = reverse(
            'posts:profile',
            kwargs={'username': cls.user.username}
        )
        cls.post_detail_url = reverse(
            'posts:post_detail',
            kwargs={'post_id': cls.post.pk}
        )
        cls.post_edit_url = reverse(
            'posts:post_edit',
            kwargs={'post_id': cls.post.pk}
        )
        cls.post_create_url = reverse('posts:post_create')

        cls.all_urls = (
            (cls.index_url, 'posts/index.html'),
            (cls.group_url, 'posts/group_list.html'),
            (cls.profile_url, 'posts/profile.html'),
            (cls.post_detail_url, 'posts/post_detail.html'),
            (cls.post_create_url, 'posts/post_create.html'),
            (cls.post_edit_url, 'posts/post_create.html'),
            (cls.follow_url, 'posts/follow.html')
        )

    def setUp(self):
        cache.clear()
        self.unauthorized_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(TestPosts.user)

    def assert_content(self, context):
        post = context['page_obj'][0]

        self.assertEqual(post.author, TestPosts.user)
        self.assertEqual(post.pub_date, TestPosts.post.pub_date)
        self.assertEqual(post.text, TestPosts.post.text)
        self.assertEqual(post.group, TestPosts.post.group)

    def test_index_page_context_is_correct(self):
        """Тест, проверяющий контекст, передаваемый в шаблон."""
        response = self.unauthorized_client.get(reverse('posts:index'))
        self.assert_content(response.context)

    def test_used_templates_are_correct(self):
        """View-функции используют ожидаемые HTML-шаблоны"""
        for address, template in TestPosts.all_urls:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_group_list_page_context_is_correct(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = (
            self.authorized_client.get(
                reverse('posts:group_list', kwargs={'slug': 'test-group'})
            )
        )
        group = response.context['group']

        self.assertEqual(group.slug, 'test-group')
        self.assertEqual(group.description, 'test description')
        self.assertEqual(group.title, 'Test group')
        self.assert_content(response.context)

    def test_post_shows_up_in_its_group(self):
        """Пост появляется только в своей группе."""
        response = (
            self.authorized_client.get(
                reverse('posts:group_list', kwargs={'slug': 'test-group2'})
            )
        )
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_post_shows_up_in_its_author_profile(self):
        """Пост появляется на странице профайла автора."""
        response = (
            self.authorized_client.get(TestPosts.profile_url)
        )
        post = response.context['page_obj'][0]

        self.assertEqual(post.author, TestPosts.user)

    def test_profile_page_context_is_correct(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = (
            self.authorized_client.get(
                reverse(
                    'posts:profile',
                    kwargs={'username': TestPosts.user.username})
            )
        )
        author = response.context['author']
        following = response.context['following']

        self.assertIn(following, response.context)
        self.assertEqual(author, TestPosts.user)
        self.assert_content(response.context)

    def test_post_detail_page_context_is_correct(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (
            self.authorized_client.get(
                reverse(
                    'posts:post_detail',
                    kwargs={'post_id': TestPosts.post.pk})
            )
        )

        post = response.context['post']
        comment = response.context['comments'][0]
        form_field = {
            'text': forms.fields.CharField,
        }

        self.assertEqual(comment.text, TestPosts.comment.text)
        self.assertEqual(comment.post, post)
        self.assertEqual(comment.author, TestPosts.user)
        self.assertEqual(post.author, TestPosts.user)
        self.assertEqual(post.pub_date, TestPosts.post.pub_date)
        self.assertEqual(post.text, TestPosts.post.text)
        self.assertEqual(post.group, TestPosts.post.group)

        for value, expected in form_field.items():
            with self.subTest(value=value):
                field = response.context.get('form').fields.get(value)
                self.assertIsInstance(field, expected)

    def test_post_create_page_context_is_correct(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_context_is_correct(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit', kwargs={'post_id': TestPosts.post.pk}))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
            'image': forms.ImageField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_paginator_in_pages_with_posts(self):
        """Тестирует работу пагинатора."""
        paginator_amount = settings.POST_PER_PAGE
        all_posts_count = 14

        posts = [
            Post(
                text=f'test text {num}', author=TestPosts.user,
                group=TestPosts.group
            ) for num in range(1, all_posts_count)
        ]
        Post.objects.bulk_create(posts)
        urls_with_pagination = (
            TestPosts.index_url,
            TestPosts.group_url,
            TestPosts.profile_url
        )
        pages = (
            (1, paginator_amount),
            (2, all_posts_count - paginator_amount)
        )
        for url in urls_with_pagination:
            for page, count in pages:
                with self.subTest(url=url):
                    response = self.authorized_client.get(
                        url,
                        {'page': page}
                    )

                    self.assertEqual(
                        len(response.context.get('page_obj').object_list),
                        count
                    )

    def test_comment_shows_up_in_post_page(self):
        """Комментарий появляется на странице поста."""
        post = TestPosts.post
        comment = TestPosts.comment
        response = (
            self.authorized_client.get(
                reverse(
                    'posts:post_detail',
                    kwargs={'post_id': post.pk})
            )
        )
        post_comment = response.context['comments'][0]

        self.assertEqual(post_comment.text, comment.text)

    def test_cache_index(self):
        """Проверка хранения и очищения кэша для index."""
        response_old = self.authorized_client.get(reverse('posts:index'))
        old_posts = response_old.content
        Post.objects.create(
            text='test_new_post',
            author=TestPosts.user,
        )
        response = self.authorized_client.get(reverse('posts:index'))
        posts = response.content
        self.assertEqual(old_posts, posts)
        cache.clear()
        response_new = self.authorized_client.get(reverse('posts:index'))
        new_posts = response_new.content
        self.assertNotEqual(old_posts, new_posts)


class FollowTests(TestCase):
    def setUp(self):
        self.auth_client_follower = Client()
        self.auth_client_following = Client()
        self.user_follower = User.objects.create_user(username='follower')
        self.user_following = User.objects.create_user(username='following')
        self.post = Post.objects.create(
            author=self.user_following,
            text='test text'
        )
        self.auth_client_follower.force_login(self.user_follower)
        self.auth_client_following.force_login(self.user_following)

    def test_follow(self):
        """Авторизованный юзер может подписываться на других юзеров."""
        self.auth_client_follower.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_following.username})
        )
        self.assertEqual(Follow.objects.all().count(), 1)

    def test_unfollow(self):
        """Авторизованный юзер может удалять других юзеров из подписок."""
        self.auth_client_follower.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.user_following.username})
        )
        self.auth_client_follower.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.user_following.username})
        )
        self.assertEqual(Follow.objects.all().count(), 0)

    def test_subscription_feed(self):
        """Запись не появляется в ленте тех, кто не подписан."""
        Follow.objects.create(user=self.user_follower,
                              author=self.user_following)
        response = self.auth_client_follower.get(
            reverse('posts:follow_index')
        )
        post = response.context['page_obj'][0]
        self.assertEqual(post.text, 'test text')

        response = self.auth_client_following.get(
            reverse('posts:follow_index')
        )
        self.assertNotContains(response, 'test text')
