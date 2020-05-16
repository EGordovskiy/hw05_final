from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.images import ImageFile
from django.core.cache.utils import make_template_fragment_key
from django.core.cache import cache
from .models import Follow, Comment


class TestAutorizedUser(TestCase):
    testusername = 'testuser'
    testtext1 = 'testtext1'
    testtext2 = 'testtext2'
    testemail = 'testemail@ya.ru'
    password = 'yac@q765490'
    client = Client()

    def setUp(self):
        #Регистрируем пользователя, логиним и создаем пост
        self.response_signup = self.client.post(
                "/auth/signup/", {"username": self.testusername, "email": self.testemail, 
                "password1": self.password, "password2": self.password}, follow=True
            )
        self.response_login = self.client.post(
                "/auth/login/", {"username": self.testusername, "password": self.password}, follow=True
            )
        self.response_post_create = self.client.post("/new/", {"text" : self.testtext1}, follow=True)
        self.response_profile = self.client.get("/testuser/")
        self.response_post = self.client.get("/testuser/1/")
        self.response_index = self.client.get("/")
 

    def test_create_profile(self):
        #После регистрации пользователя проверяем наличие страницы пользователя
        self.assertEqual(self.response_profile.status_code, 200)


    def test_create_new_post(self):
        #Авторизованный пользователь может опубликовать пост
        self.assertEqual(self.response_post_create.status_code, 200)
        #Проверяем количество созданных постов на странице profile пользователя
        #(значение должно равняться единице)
        self.assertEqual(len(self.response_profile.context["post_list"]), 1)


    def test_have_new_post(self):
        #После публикации поста новая запись доступна на страницах index, profile и post
        self.assertContains(self.response_index, self.testtext1, status_code=200)
        self.assertContains(self.response_profile, self.testtext1, status_code=200)
        self.assertContains(self.response_post, self.testtext1, status_code=200)


    def test_edit_post(self):
        #После редактирования поста запись доступна на страницах index, profile и post
        self.client.post(
                reverse("post_edit", kwargs={"username":self.testusername, "post_id":1}),
                {"text": self.testtext2},
            )
        urls = ["/", "/testuser/", "/testuser/1/"]
        for url in urls:
            response = self.client.get(url)
            self.assertContains(response, self.testtext2, status_code=200)
        

    def test_error_404(self):
        #Проверка возвращения ошибки 404 при обращении на несуществующую страницу
        response_404 = self.client.get("/not_user/1100/")
        self.assertEqual(response_404.status_code, 404)

        
class TestNonAutorizedUser(TestCase):
    def test_no_create_new_post(self):
        #Неавторизованный пользователь не может опубликовать пост
        #его редиректит на страницу входа
        self.client = Client()
        response = self.client.get("/new/")
        self.assertRedirects(response, "/auth/login/?next=/new/", status_code=302)



class TestCache(TestCase):
    testusername = 'testuser'
    testtext1 = 'testtext1'
    testemail = 'testemail@ya.ru'
    password = 'yac@q765490'
    client = Client()

    def setUp(self):
        #Регистрируем пользователя, логиним
        self.response_signup = self.client.post(
                "/auth/signup/", {"username": self.testusername, "email": self.testemail, 
                "password1": self.password, "password2": self.password}, follow=True
            )
        self.response_login = self.client.post(
                "/auth/login/", {"username": self.testusername, "password": self.password}, follow=True
            )
        self.response_index = self.client.get("/")

    def test_cache_index(self):
        #Создаем пост
        response_post_create = self.client.post("/new/", {"text" : self.testtext1}, follow=True)
        #Проверяем создание поста
        self.assertEqual(response_post_create.status_code, 200)
        #Проверяем работу кэша
        key = make_template_fragment_key('index_page')
        response_cache = cache.get(key)
        self.assertTrue(self.response_index, response_cache)


        
class TestImages(TestCase):
    testusername = 'userimage'
    testtext1 = 'testtext1'
    testtext2 = 'testtext2'
    testemail = 'image@ya.ru'
    password = 'yac@q765490'
    client = Client()
    def setUp(self):
        #Создаем пользователя и загружаем картинку
        self.response_signup = self.client.post(
                "/auth/signup/", {"username": self.testusername, "email": self.testemail, 
                "password1": self.password, "password2": self.password}, follow=True
            )
        self.response_login = self.client.post(
                "/auth/login/", {"username": self.testusername, "password": self.password}, follow=True
            )
        #Создают новый пост
        self.response_create_post = self.client.post("/new/", {"text": self.testtext1}, follow=True)

        with open('media/posts/ozero.jpg', 'rb') as fp:
            self.post_edit = self.client.post(
                "/userimage/1/edit/", {"text": self.testtext2, "image": fp}
            )
        self.response_profile = self.client.get("/userimage/")
        self.response_post = self.client.get("/userimage/1/")
        self.response_index = self.client.get("/")
        
    def test_post_with_image(self):
        # Редактирую пост и вставляю в него картинку
        self.assertEqual(self.response_create_post.status_code, 200)
        # На всякий случай проверяю, отредактировался ли пост
        self.assertEqual(self.post_edit.status_code, 302)
        # Проверяю наличие тега "<img" на странице отредактированного поста с кодом ответа 200
        self.assertContains(self.response_post, "<img", status_code=200)
    
    def test_have_images(self):
        # Проверяю наличие тега "<img" на страницах index & profile с кодом ответа 200
        self.assertContains(self.response_profile, "<img", status_code=200)
        self.assertContains(self.response_index, "<img", status_code=200)

    def test_safe_download(self):
        # Создаю пост, но вместо картинки пробую приложить текстовый документ, получаю ошибку об этом
        with open('media/posts/text_file.txt', 'rb') as file:
            response = self.client.post('/new/', {'text': self.testtext1, 'image': file})
            self.assertFormError(response, 'form', 'image', 'Upload a valid image. The file you uploaded was either not an image or a corrupted image.')



class TestFollow(TestCase):
    testusername1 = 'username1'
    testusername2 = 'username2'
    testtext1 = 'testtext1'
    testtext2 = 'testtext2'
    testemail1 = 'test1@ya.ru'
    testemail2 = 'test2@ya.ru'
    password = 'yac@q765490'
    client = Client()

    def setUp(self):
        #Создаем пользователя 1
        self.response_signup = self.client.post(
                "/auth/signup/", {"username": self.testusername1, "email": self.testemail1, 
                "password1": self.password, "password2": self.password}, follow=True
            )
        self.response_login = self.client.post(
                "/auth/login/", {"username": self.testusername1, "password": self.password}, follow=True
            )
        # Создаем пост
        self.response_create_post = self.client.post("/new/", {"text": self.testtext1}, follow=True)
        #Создаем пользователя 2
        self.response_signup = self.client.post(
                "/auth/signup/", {"username": self.testusername2, "email": self.testemail2, 
                "password1": self.password, "password2": self.password}, follow=True
            )
        self.response_login = self.client.post(
                "/auth/login/", {"username": self.testusername2, "password": self.password}, follow=True
            )
        

    def test_follow_unfollow(self):
        self.client.get("/username1/follow/", follow=True)
        follow_count = Follow.objects.count()
        self.assertEqual(follow_count, 1)
        self.client.get("/username1/unfollow/", follow=True)
        unfollow_count = Follow.objects.count()
        self.assertEqual(unfollow_count, 0)


    def test_new_post_in_follow_index(self):
        self.client.get('/username1/follow/', follow=True)
        response_follow_index = self.client.get('/follow/')
        self.assertContains(response_follow_index, self.testtext1, status_code=200)
        self.client.get('/username1/unfollow/', follow=True)
        response_unfollow_index = self.client.get('/follow/')
        self.assertNotContains(response_unfollow_index, self.testtext1, status_code=200)


    def test_create_comment_for_post(self):
        self.client.post("/username1/1/comment/", {"text": self.testtext2}, follow=True)
        response = self.client.get("/username1/1/")
        comment_count = Comment.objects.filter(post=1).count()
        self.assertEqual(comment_count, 1)
        self.assertContains(response, self.testtext2, status_code=200)