from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth_user')
        cls.group = Group.objects.create(
            title='test title',
            description='test description',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            text='test text',
            author=cls.user,
            group=cls.group
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
        cls.unexisting_page_url = '/unexisting_page/'

        cls.public_urls = (
            (cls.index_url, 'posts/index.html'),
            (cls.group_url, 'posts/group_list.html'),
            (cls.profile_url, 'posts/profile.html'),
            (cls.post_detail_url, 'posts/post_detail.html')
        )
        cls.private_urls = (
            (cls.post_create_url, 'posts/post_create.html'),
            (cls.post_edit_url, 'posts/post_create.html'),
            (cls.follow_url, 'posts/follow.html')
        )

    def setUp(self):
        self.unauthorized_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostsURLTests.user)

    def test_public_urls_work(self):
        """Публичные URLs работают."""
        for url in PostsURLTests.public_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unauthorized_user_cannot_access_private_urls(self):
        """Неавторизированный юзер не может создавать, редактировать посты."""
        for url, _ in PostsURLTests.private_urls:
            with self.subTest(url=url):
                response = self.unauthorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_post_edit_url_redirect_auth_notauthor_user_on_post_detail(self):
        """Юзер не может редактировать пост, если он не его автор."""
        user = User.objects.create_user(username='second')
        authorized_client2 = Client()
        authorized_client2.force_login(user)
        response = (
            authorized_client2.get(
                reverse(
                    'posts:post_edit',
                    kwargs={'post_id': PostsURLTests.post.pk}), follow=True
            )
        )
        self.assertRedirects(response, PostsURLTests.post_detail_url)

    def test_authorized_user_can_access_private_urls(self):
        """Авторизированный юзер может создать и редактировать пост."""
        for url, _ in PostsURLTests.private_urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_unexisting_page(self):
        """При запросе несуществующего URL используется правильный шаблон."""
        response = self.unauthorized_client.get('/unexisting_page/')
        template = 'core/404.html'
        self.assertTemplateUsed(response, template)

    def test_public_urls_uses_correct_template(self):
        """Публичные URLs используют правильные шаблоны."""
        for address, template in PostsURLTests.public_urls:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_private_urls_uses_correct_template(self):
        """Приватные URLs используют правильные шаблоны."""
        for address, template in PostsURLTests.private_urls:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
