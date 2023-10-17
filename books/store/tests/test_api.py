from django.contrib.auth.models import User
from django.db import connection
from django.db.models import Count, Case, When, Avg
from django.urls import reverse
from rest_framework import status
from rest_framework.exceptions import ErrorDetail
from rest_framework.test import APITestCase
# from rest_framework.utils import json
import json
from store.models import Book, UserBookRelation
from store.serializers import BookSerializer
from django.test.utils import CaptureQueriesContext


class BooksApiTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create(username='test_username')
        self.book_1 = Book.objects.create(name='book 1', prise=60,
                                          author_name='Author 1',
                                          owner=self.user)
        self.book_2 = Book.objects.create(name='book 2', prise=40,
                                          author_name='Author 3',
                                          owner=self.user)
        self.book_3 = Book.objects.create(name='book Author 1', prise=60,
                                          author_name='Author 2',
                                          owner=self.user)
        UserBookRelation.objects.create(user=self.user, book=self.book_1, like=True,
                                        rate=4)

    def test_get(self):
        url = reverse('book-list')
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(url)
            self.assertEqual(2, len(queries))
        # response = self.client.get(url)
        books = Book.objects.all().annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1)))
        ).order_by('id')
        setializer_data = BookSerializer(books,
                                         many=True).data
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertEquals(setializer_data, response.data)
        self.assertEquals(setializer_data[0]['rating'], '4.00')
        # self.assertEquals(setializer_data[0]['likes_count'], 1)
        self.assertEquals(setializer_data[0]['annotated_likes'], 1)

    def test_get_filter(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'prise': 60})
        books = Book.objects.filter(id__in=[self.book_1.id, self.book_3.id]).annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1)))
        ).order_by('id')
        setializer_data = BookSerializer(books,
                                         many=True).data
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertEquals(setializer_data, response.data)

    def test_get_search(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'search': 'Author 1'})
        books = Book.objects.filter(id__in=[self.book_1.id, self.book_3.id]).annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1)))
        ).order_by('id')
        setializer_data = BookSerializer(books,
                                         many=True).data
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertEquals(setializer_data, response.data)


    def test_get_ordering(self):
        url = reverse('book-list')
        response = self.client.get(url, data={'ordering': 'author_name'})
        books = Book.objects.all().annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1)))
        ).order_by('author_name')
        setializer_data = BookSerializer(books,
                                         many=True).data
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        self.assertEquals(setializer_data, response.data)

    def test_create(self):
        self.assertEquals(3, Book.objects.all().count())
        url = reverse('book-list')
        data = {
            "name": "Book create",
            "prise": 100,
            "author_name": "Author Create"
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.post(url, data=json_data,
                                    content_type='application/json')

        self.assertEquals(status.HTTP_201_CREATED, response.status_code)
        self.assertEquals(4, Book.objects.all().count())
        self.assertEquals(self.user, Book.objects.last().owner)

    def test_update(self):
        url = reverse('book-detail', args=(self.book_1.id,))
        data = {
            "name": self.book_1.name,
            "prise": 100,
            "author_name": self.book_1.author_name
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)
        response = self.client.put(url, data=json_data,
                                   content_type='application/json')

        self.assertEquals(status.HTTP_200_OK, response.status_code)
        # self.book_1 = Book.objects.get(id=self.book_1.id)
        self.book_1.refresh_from_db()

        self.assertEquals(100, self.book_1.prise)

    def test_delete(self):
        self.assertEquals(3, Book.objects.all().count())
        url = reverse('book-detail', args=(self.book_1.id,))

        self.client.force_login(self.user)
        response = self.client.delete(url)

        self.assertEquals(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertEquals(2, Book.objects.all().count())

    def test_update_not_owner(self):
        self.user2 = User.objects.create(username='test_username 2')

        url = reverse('book-detail', args=(self.book_1.id,))
        data = {
            "name": self.book_1.name,
            "prise": 100,
            "author_name": self.book_1.author_name
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user2)
        response = self.client.put(url, data=json_data,
                                   content_type='application/json')

        self.assertEquals(status.HTTP_403_FORBIDDEN, response.status_code)
        # self.book_1 = Book.objects.get(id=self.book_1.id)

        self.assertEquals({'detail': ErrorDetail(
            string='You do not have permission to perform this action.',
            code='permission_denied')}, response.data)

        self.book_1.refresh_from_db()

        self.assertEquals(60, self.book_1.prise)

    def test_update_not_owner_but_staff(self):
        self.user2 = User.objects.create(username='test_username 2',
                                         is_staff=True)

        url = reverse('book-detail', args=(self.book_1.id,))
        data = {
            "name": self.book_1.name,
            "prise": 100,
            "author_name": self.book_1.author_name
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user2)
        response = self.client.put(url, data=json_data,
                                   content_type='application/json')

        self.assertEquals(status.HTTP_200_OK, response.status_code)
        # self.book_1 = Book.objects.get(id=self.book_1.id)

        self.book_1.refresh_from_db()

        self.assertEquals(100, self.book_1.prise)

    def test_delete_not_owner(self):
        self.user2 = User.objects.create(username='test_username 2')

        self.assertEquals(3, Book.objects.all().count())
        url = reverse('book-detail', args=(self.book_1.id,))

        self.client.force_login(self.user2)
        response = self.client.delete(url)
        self.assertEquals({'detail': ErrorDetail(
            string='You do not have permission to perform this action.',
            code='permission_denied')}, response.data)
        self.assertEquals(status.HTTP_403_FORBIDDEN, response.status_code)
        self.assertEquals(3, Book.objects.all().count())

    def test_delete_not_owner_but_staff(self):
        self.user2 = User.objects.create(username='test_username 2',
                                         is_staff=True)
        self.assertEquals(3, Book.objects.all().count())
        url = reverse('book-detail', args=(self.book_1.id,))

        self.client.force_login(self.user2)
        response = self.client.delete(url)

        self.assertEquals(status.HTTP_204_NO_CONTENT, response.status_code)
        self.assertEquals(2, Book.objects.all().count())


class BooksRelationTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create(username='test_username')
        self.user2 = User.objects.create(username='test_username 2')

        self.book_1 = Book.objects.create(name='book 1', prise=60,
                                          author_name='Author 1',
                                          owner=self.user)
        self.book_2 = Book.objects.create(name='book 2', prise=40,
                                          author_name='Author 3',
                                          owner=self.user)

    def test_like(self):
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))
        data = {
            "like": True,
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)

        response = self.client.patch(url, data=json_data,
                                     content_type='application/json')
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user,
                                                book=self.book_1)
        self.assertTrue(relation.like)

    def test_in_bookmarks(self):
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))
        data = {
            "in_bookmarks": True,
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)

        response = self.client.patch(url, data=json_data,
                                     content_type='application/json')
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user,
                                                book=self.book_1)
        self.assertTrue(relation.in_bookmarks)

    def test_rate(self):
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))
        data = {
            "rate": 1,
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)

        response = self.client.patch(url, data=json_data,
                                     content_type='application/json')
        self.assertEquals(status.HTTP_200_OK, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user,
                                                book=self.book_1)
        self.assertEquals(1, relation.rate)


    def test_rate_wrong(self):
        url = reverse('userbookrelation-detail', args=(self.book_1.id,))
        data = {
            "rate": 6,
        }
        json_data = json.dumps(data)
        self.client.force_login(self.user)

        response = self.client.patch(url, data=json_data,
                                     content_type='application/json')
        self.assertEquals(status.HTTP_400_BAD_REQUEST, response.status_code)
        relation = UserBookRelation.objects.get(user=self.user,
                                                book=self.book_1)
        self.assertEquals(None, relation.rate)