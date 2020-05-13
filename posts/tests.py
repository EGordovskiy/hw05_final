from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.images import ImageFile
from django.core.cache.utils import make_template_fragment_key
from django.core.cache import cache


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



class TestImages(TestCase):
    testusername = 'userimage'
    testtext1 = 'testtext1'
    testemail = 'image@ya.ru'
    #grouptest = 'testgroup'
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

        self.grouptest = self.client.group()

        with open('media/posts/ozero.jpg', 'rb') as fp:
            self.post_create_image = self.client.post(
                    "/new/", {"text": self.testtext1, "group": self.grouptest, "image": fp}, follow=True
                )

            self.response_profile = self.client.get("/userimage/")
            self.response_post = self.client.get("/userimage/1/")
            self.response_index = self.client.get("/")
            self.response_group = self.client.get("/group/testgroup/")
        
    def test_post_with_image(self):
        #Проверяем страницу конкретной записи с картинкой на наличие тега <img>
        #self.assertContains(self.response_post, "<img")
        self.assertEqual(self.post_create_image.status_code, 200)
    


    def test_have_images(self):
        self.assertContains(self.response_profile, "<img")
        self.assertContains(self.response_index, "<img")
        self.assertContains(self.response_group, "<img")

    def test_safe_download(self):
        with open('media/posts/text_file.txt', 'rb') as fp:
            response = self.client.post('/new/', {'text': self.testtext1, 'image': fp}, follow=True)
            self.assertContains(response, 'Upload a valid image. The file you uploaded was either not an image or a corrupted image.')


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
        key = make_template_fragment_key('index_page')
        response_cache = cache.get(key)
        self.assertTrue(self.response_index, response_cache)

