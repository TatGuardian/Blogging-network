from django import forms
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from yatube.settings import PER_PAGE

from ..models import Comment, Follow, Group, Post

User = get_user_model()


class PostViewTests(TestCase):
    "Создаем тестовые посты и группы."
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        cls.user = User.objects.create_user(username='leo')
        cls.group = Group.objects.create(
            title='Группа поклонников графа',
            slug='tolstoi',
            description='Что-то о группе'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Война и мир переоценен',
            group=cls.group,
            image=uploaded,
        )
        cls.comment_post = Comment.objects.create(
            author=cls.user,
            text='Полностью согласен.',
            post=cls.post
        )

    @classmethod
    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(PostViewTests.user)
        cache.clear()

    def exists_on_page(self, page_context):
        """Метод, чтобы проверить, существует ли пост на странице."""
        if 'page_obj' in page_context:
            post = page_context['page_obj'][0]
        else:
            post = page_context['post']
        to_check = {
            PostViewTests.post.author: post.author,
            PostViewTests.post.text: post.text,
            PostViewTests.post.group: post.group,
            PostViewTests.post.pk: post.pk,
            PostViewTests.post.image: post.image,
            PostViewTests.comment_post: post.comments.last()
        }
        for key, val in to_check.items():
            with self.subTest():
                self.assertEqual(key, val)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = {
            reverse('posts:posts_index'): 'posts/index.html',
            reverse('posts:group_list',
                    kwargs={'slug':
                            PostViewTests.group.slug}):
                                'posts/group_list.html',
            reverse(
                'posts:profile',
                kwargs={'username':
                        PostViewTests.user.username}): 'posts/profile.html',
            reverse(
                'posts:post_detail',
                kwargs={'post_id':
                        PostViewTests.post.pk}): 'posts/post_detail.html',
            reverse(
                'posts:post_edit',
                kwargs={'post_id':
                        PostViewTests.post.pk}): 'posts/post_create.html',
            reverse('posts:post_create'): 'posts/post_create.html',
        }

        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_paginator_correct_context(self):
        """Шаблон index, group_list и profile
        сформированы с корректным Paginator."""
        paginator_objects = []
        for i in range(1, 18):  # we create 18 objects to test
            new_post = Post(
                author=PostViewTests.user,
                text='Тестовый пост ' + str(i),
                group=PostViewTests.group
            )
            paginator_objects.append(new_post)
        Post.objects.bulk_create(paginator_objects)
        paginator_data = {
            'index': reverse('posts:posts_index'),
            'group': reverse(
                'posts:group_list',
                kwargs={'slug': PostViewTests.group.slug}
            ),
            'profile': reverse(
                'posts:profile',
                kwargs={'username': PostViewTests.user.username}
            )
        }
        for place, page in paginator_data.items():
            with self.subTest(paginator_place=place):
                response_page_1 = self.authorized_client.get(page)
                response_page_2 = self.authorized_client.get(
                    page + '?page=2')
                self.assertEqual(len(
                    response_page_1.context['page_obj']), PER_PAGE)
                self.assertEqual(len(
                    response_page_2.context['page_obj']), 18 - PER_PAGE)

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response_post_detail = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostViewTests.post.pk}
            )
        )
        page_post_detail_context = response_post_detail.context
        self.exists_on_page(page_post_detail_context)

    def test_group_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response_group = self.authorized_client.get(
            reverse(
                'posts:group_list',
                kwargs={'slug': PostViewTests.group.slug}
            )
        )
        page_group_context = response_group.context
        self.exists_on_page(page_group_context)  # if post exists on group page
        self.assertEqual(response_group.context['group'], PostViewTests.group)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response_index = self.authorized_client.get(
            reverse('posts:posts_index'))
        page_index_context = response_index.context
        # if post exists on the main page
        self.exists_on_page(page_index_context)

    def test_profile_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response_profile = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': PostViewTests.user.username}
            )
        )
        page_profile_context = response_profile.context
        # if post exists on profile page
        self.exists_on_page(page_profile_context)
        self.assertEqual(
            response_profile.context['author'], PostViewTests.user)

    def test_create_post_page_show_correct_context(self):
        """Шаблон create_post сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон create_post(edit) сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse('posts:post_edit',
                    kwargs={'post_id': PostViewTests.post.pk})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_index_caches(self):
        """Тестирование кэша главной страницы."""
        new_post = Post.objects.create(
            author=PostViewTests.user,
            text='Этот пост создан быть удаленным',
            group=PostViewTests.group
        )
        response_1 = self.authorized_client.get(
            reverse('posts:posts_index')
        )
        response_content_1 = response_1.content
        new_post.delete()
        response_2 = self.authorized_client.get(
            reverse('posts:posts_index')
        )
        response_content_2 = response_2.content
        self.assertEqual(response_content_1, response_content_2)
        cache.clear()
        response_3 = self.authorized_client.get(
            reverse('posts:posts_index')
        )
        response_content_3 = response_3.content
        self.assertNotEqual(response_content_2, response_content_3)

    def test_follow(self):
        """Тестирование подписки на автора."""
        count_follow = Follow.objects.count()
        new_author = User.objects.create(username='Leonid')
        Follow.objects.create(
            user=self.user,
            author=new_author
        )
        follow = Follow.objects.last()
        to_check = {
            Follow.objects.count(): count_follow + 1,
            follow.author: new_author,
            follow.user: PostViewTests.user,
        }
        for val, expected in to_check.items():
            with self.subTest(value=val):
                self.assertEqual(val, expected)

    def test_unfollow(self):
        """Тестирование отписки от автора."""
        count_follow = Follow.objects.count()
        new_author = User.objects.create(username='Leonid')
        Follow.objects.create(
            user=self.user,
            author=new_author
        )
        self.assertEqual(Follow.objects.count(), count_follow + 1)
        self.authorized_client.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': new_author.username}
            )
        )
        self.assertEqual(Follow.objects.count(), count_follow)
        self.assertFalse(Follow.objects.filter(
            user=self.user, author=new_author).exists())

    def test_following_posts(self):
        """Тестирование появления поста автора в ленте подписчика."""
        new_user = User.objects.create(username='Leonid')
        authorized_client1 = Client()
        authorized_client1.force_login(new_user)
        authorized_client1.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': PostViewTests.user.username}
            )
        )
        response_follow = authorized_client1.get(
            reverse('posts:follow_index')
        )
        context_follow = response_follow.context
        self.exists_on_page(context_follow)

    def test_unfollowing_posts(self):
        """Тестирование отсутствия поста автора у нового пользователя."""
        new_user = User.objects.create(username='Leonid')
        authorized_client2 = Client()
        authorized_client2.force_login(new_user)
        response_unfollow = authorized_client2.get(
            reverse('posts:follow_index')
        )
        context_unfollow = response_unfollow.context
        self.assertEqual(len(context_unfollow['page_obj']), 0)
