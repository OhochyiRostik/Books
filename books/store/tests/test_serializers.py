from django.contrib.auth.models import User
from django.db.models import Count, Case, When, Avg
from django.test import TestCase

from store.models import Book, UserBookRelation
from store.serializers import BookSerializer


class BookSerializerTestCase(TestCase):
    def test_serializer(self):
        user1 = User.objects.create(username='user1',
                                    first_name='First1',
                                    last_name='Last1')
        user2 = User.objects.create(username='user2',
                                    first_name='First2',
                                    last_name='Last2')
        user3 = User.objects.create(username='user3',
                                    first_name='First3',
                                    last_name='Last3')

        book_1 = Book.objects.create(name='book 1', prise=20,
                                     author_name='Author 1', owner=user1)
        book_2 = Book.objects.create(name='book 2', prise=40,
                                     author_name='Author 2')
        UserBookRelation.objects.create(user=user1, book=book_1, like=True,
                                        rate=4)
        UserBookRelation.objects.create(user=user2, book=book_1, like=True,
                                        rate=4)
        user_book_3 = UserBookRelation.objects.create(user=user3, book=book_1, like=True,
                                                      rate=4)

        # user_book_3.rate=4
        # user_book_3.save()
        # user_book_3.refresh_from_db()

        UserBookRelation.objects.create(user=user1, book=book_2, like=False,
                                        rate=2)
        UserBookRelation.objects.create(user=user2, book=book_2, like=True,
                                        rate=3)
        UserBookRelation.objects.create(user=user3, book=book_2, like=True,
                                        rate=4)

        books = Book.objects.all().annotate(
            annotated_likes=Count(Case(When(userbookrelation__like=True, then=1)))
        ).order_by('id')
        data = BookSerializer(books, many=True).data
        print(data)
        expected_data = [
            {
                'id': book_1.id,
                'name': 'book 1',
                'prise': '20.00',
                'author_name': 'Author 1',
                # 'likes_count': 3,
                'annotated_likes': 3,
                'rating': '4.00',
                'owner_name': 'user1',
                'readers': [
                    {
                        'first_name': 'First1',
                        'last_name': 'Last1'
                    },
                    {
                        'first_name': 'First2',
                        'last_name': 'Last2'
                    },
                    {
                        'first_name': 'First3',
                        'last_name': 'Last3'
                    }
                ]

            },
            {
                'id': book_2.id,
                'name': 'book 2',
                'prise': '40.00',
                'author_name': 'Author 2',
                # 'likes_count': 2,
                'annotated_likes': 2,
                'rating': '3.00',
                'owner_name': '',
                'readers': [
                    {
                        'first_name': 'First1',
                        'last_name': 'Last1'
                    },
                    {
                        'first_name': 'First2',
                        'last_name': 'Last2'
                    },
                    {
                        'first_name': 'First3',
                        'last_name': 'Last3'
                    }
                ]

            },
        ]
        self.assertEqual(expected_data, data)
