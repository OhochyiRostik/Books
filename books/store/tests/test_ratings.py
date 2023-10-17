from django.contrib.auth.models import User
from django.test import TestCase

from store.models import Book, UserBookRelation
from store.ratings import set_rating


class SetRatingTestCase(TestCase):
    def setUp(self):
        user1 = User.objects.create(username='user1',
                                    first_name='First1',
                                    last_name='Last1')
        user2 = User.objects.create(username='user2',
                                    first_name='First2',
                                    last_name='Last2')
        user3 = User.objects.create(username='user3',
                                    first_name='First3',
                                    last_name='Last3')

        self.book_1 = Book.objects.create(name='book 1', prise=20,
                                     author_name='Author 1', owner=user1)
        UserBookRelation.objects.create(user=user1, book=self.book_1, like=True,
                                        rate=4)
        UserBookRelation.objects.create(user=user2, book=self.book_1, like=True,
                                        rate=5)
        UserBookRelation.objects.create(user=user3, book=self.book_1, like=True,
                                        rate=5)

    def test_rating(self):
        set_rating(self.book_1)
        self.book_1.refresh_from_db()
        self.assertEqual('4.67', str(self.book_1.rating))


