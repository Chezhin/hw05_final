import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user')
        cls.user2 = User.objects.create_user(username='test_user2')
        cls.group = Group.objects.create(
            title='Test group',
            description='test description',
            slug='test-group'
        )
        cls.group_2 = Group.objects.create(
            title='Test group2',
            description='test description2',
            slug='test-group2'
        )

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.unauthorized_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostFormTests.user)

    def test_user_can_edit_post(self):
        """Тест, проверяющий редактирование поста."""
        post = Post.objects.create(
            text='new post',
            author=PostFormTests.user,
            group=PostFormTests.group
        )
        edit_post_data = {
            'text': 'edit new post',
            'group': PostFormTests.group_2.id,
            'author': PostFormTests.user
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post.pk}),
            data=edit_post_data,
        )
        post_edit = Post.objects.first()
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(post_edit.text, edit_post_data['text'])
        self.assertEqual(
            post_edit.author,
            edit_post_data['author']
        )
        self.assertEqual(
            post_edit.group.id,
            edit_post_data['group']
        )
        self.assertEqual(
            post_edit.group.slug,
            'test-group2'
        )
        self.assertEqual(
            post_edit.group.title,
            'Test group2'
        )

    def test_create_post_with_image(self):
        """При отправке поста с картинкой создается запись в базе данных."""
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        posto_data = {
            'text': 'new posto',
            'group': PostFormTests.group.id,
            'image': uploaded
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'), data=posto_data, follow=True)
        self.assertEqual(response.status_code, HTTPStatus.OK)

        self.assertTrue(
            Post.objects.filter(
                text='new posto',
                image='posts/small.gif',
                group=PostFormTests.group,
                author=PostFormTests.user
            ).exists()
        ) 
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_authorized_user_can_create_comment(self):
        """Тест, проверяющий создание комментария авторизованным юзером."""
        comments_count = Comment.objects.count()
        post = Post.objects.create(
            text='new post',
            author=PostFormTests.user,
            group=PostFormTests.group
        )
        comment_data = {
            'text': 'my comment'
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.pk}),
            data=comment_data,
        )
        comment = Comment.objects.first()

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Comment.objects.count(), comments_count + 1)
        self.assertEqual(comment.author, PostFormTests.user)
        self.assertEqual(comment.post, post)

    def test_unauthorized_user_cant_create_comment(self):
        """Неавторизованный юзер не может создать комментарий."""
        comments_count = Comment.objects.count()
        post = Post.objects.create(
            text='new post',
            author=PostFormTests.user,
            group=PostFormTests.group
        )
        comment_data = {
            'text': 'my comment'
        }
        response = self.unauthorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.pk}),
            data=comment_data,
        )
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(Comment.objects.count(), comments_count)
