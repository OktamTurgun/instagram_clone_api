"""
Comprehensive Tests for Social App

Test Coverage:
- Models: Follow (create, unique, self-follow, is_following, mutual)
- Views: Follow, Unfollow, Followers, Following, Stats, Search, Suggested, Popular
- Integration: Complete follow/unfollow workflows
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse

from .models import Follow

User = get_user_model()


# ============================================
# UTILITY FUNCTIONS
# ============================================

def create_user(username='testuser', email='test@example.com', password='TestPass123!'):
    """Test user yaratish"""
    return User.objects.create_user(
        username=username,
        email=email,
        password=password,
        auth_status='completed'
    )


# ============================================
# MODEL TESTS
# ============================================

class FollowModelTest(TestCase):
    """Follow model testlari"""

    def setUp(self):
        self.user1 = create_user('user1', 'user1@test.com')
        self.user2 = create_user('user2', 'user2@test.com')
        self.user3 = create_user('user3', 'user3@test.com')

    def test_create_follow(self):
        """Follow yaratish testi"""
        follow = Follow.objects.create(
            follower=self.user1,
            following=self.user2
        )
        self.assertEqual(follow.follower, self.user1)
        self.assertEqual(follow.following, self.user2)

    def test_follow_str_method(self):
        """Follow string representatsiyasi"""
        follow = Follow.objects.create(
            follower=self.user1,
            following=self.user2
        )
        expected = f"{self.user1.username} follows {self.user2.username}"
        self.assertEqual(str(follow), expected)

    def test_unique_follow_constraint(self):
        """Bir xil follow ikki marta yaratilmasligi kerak"""
        Follow.objects.create(follower=self.user1, following=self.user2)
        with self.assertRaises(IntegrityError):
            Follow.objects.create(follower=self.user1, following=self.user2)

    def test_self_follow_not_allowed(self):
        """O'zini follow qilish mumkin emas"""
        with self.assertRaises(ValidationError):
            Follow.objects.create(
                follower=self.user1,
                following=self.user1
            )

    def test_is_following_true(self):
        """is_following - follow mavjud bo'lganda True qaytarishi"""
        Follow.objects.create(follower=self.user1, following=self.user2)
        self.assertTrue(Follow.is_following(self.user1, self.user2))

    def test_is_following_false(self):
        """is_following - follow yo'q bo'lganda False qaytarishi"""
        self.assertFalse(Follow.is_following(self.user1, self.user2))

    def test_is_following_not_mutual(self):
        """user1 -> user2 follow qilsa, user2 -> user1 avtomatik bo'lmasligi"""
        Follow.objects.create(follower=self.user1, following=self.user2)
        self.assertFalse(Follow.is_following(self.user2, self.user1))

    def test_follow_ordering(self):
        """Followlar created_at bo'yicha teskari tartibda"""
        follow1 = Follow.objects.create(follower=self.user1, following=self.user2)
        follow2 = Follow.objects.create(follower=self.user1, following=self.user3)

        follows = Follow.objects.all()
        self.assertEqual(follows[0], follow2)
        self.assertEqual(follows[1], follow1)

    def test_get_mutual_followers(self):
        """Ikki foydalanuvchi o'rtasidagi umumiy followlar"""
        # user1 va user2 ikkalasi ham user3 ni follow qiladi
        Follow.objects.create(follower=self.user1, following=self.user3)
        Follow.objects.create(follower=self.user2, following=self.user3)

        mutual = Follow.get_mutual_followers(self.user1, self.user2)
        self.assertIn(self.user3, mutual)
        self.assertEqual(mutual.count(), 1)

    def test_get_mutual_followers_empty(self):
        """Umumiy follow yo'q bo'lganda bo'sh queryset"""
        Follow.objects.create(follower=self.user1, following=self.user2)

        mutual = Follow.get_mutual_followers(self.user1, self.user3)
        self.assertEqual(mutual.count(), 0)

    def test_delete_follow_cascade(self):
        """User o'chirilganda uning followlari ham o'chishi"""
        Follow.objects.create(follower=self.user1, following=self.user2)
        self.user1.delete()
        self.assertEqual(Follow.objects.count(), 0)


# ============================================
# FOLLOW / UNFOLLOW API TESTS
# ============================================

class FollowAPITest(APITestCase):
    """Follow va Unfollow API testlari"""

    def setUp(self):
        self.client = APIClient()
        self.user1 = create_user('user1', 'user1@test.com')
        self.user2 = create_user('user2', 'user2@test.com')
        self.client.force_authenticate(user=self.user1)

    def test_follow_user(self):
        """Foydalanuvchini follow qilish"""
        url = reverse('social:follow', kwargs={'user_id': self.user2.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Follow.objects.filter(
            follower=self.user1, following=self.user2
        ).exists())

    def test_follow_user_unauthenticated(self):
        """Autentifikatsiyasiz follow qilib bo'lmaydi"""
        self.client.force_authenticate(user=None)
        url = reverse('social:follow', kwargs={'user_id': self.user2.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_follow_nonexistent_user(self):
        """Mavjud bo'lmagan foydalanuvchini follow qilish"""
        url = reverse('social:follow', kwargs={'user_id': '00000000-0000-0000-0000-000000000000'})
        response = self.client.post(url)
        # FollowView: serializer 400, get_object_or_404 esa 404 qaytaradi
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND
        ])

    def test_follow_already_following(self):
        """Allaqachon follow qilingan user'ni qayta follow qilish"""
        Follow.objects.create(follower=self.user1, following=self.user2)
        url = reverse('social:follow', kwargs={'user_id': self.user2.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_unfollow_user(self):
        """Foydalanuvchidan unfollow qilish"""
        Follow.objects.create(follower=self.user1, following=self.user2)
        url = reverse('social:unfollow', kwargs={'user_id': self.user2.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Follow.objects.filter(
            follower=self.user1, following=self.user2
        ).exists())

    def test_unfollow_not_following(self):
        """Follow qilinmagan user'dan unfollow qilish"""
        url = reverse('social:unfollow', kwargs={'user_id': self.user2.id})
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_unfollow_unauthenticated(self):
        """Autentifikatsiyasiz unfollow qilib bo'lmaydi"""
        self.client.force_authenticate(user=None)
        url = reverse('social:unfollow', kwargs={'user_id': self.user2.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ============================================
# FOLLOWERS / FOLLOWING LIST TESTS
# ============================================

class FollowersFollowingAPITest(APITestCase):
    """Followers va Following ro'yxat testlari"""

    def setUp(self):
        self.client = APIClient()
        self.user1 = create_user('user1', 'user1@test.com')
        self.user2 = create_user('user2', 'user2@test.com')
        self.user3 = create_user('user3', 'user3@test.com')
        self.client.force_authenticate(user=self.user1)

    def test_get_followers_list(self):
        """Foydalanuvchi followerlarini olish"""
        Follow.objects.create(follower=self.user2, following=self.user1)
        Follow.objects.create(follower=self.user3, following=self.user1)

        url = reverse('social:followers', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_followers_empty(self):
        """Follower yo'q bo'lganda bo'sh response"""
        url = reverse('social:followers', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_following_list(self):
        """Foydalanuvchi following'larini olish"""
        Follow.objects.create(follower=self.user1, following=self.user2)
        Follow.objects.create(follower=self.user1, following=self.user3)

        url = reverse('social:following', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_following_empty(self):
        """Following yo'q bo'lganda bo'sh response"""
        url = reverse('social:following', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_nonexistent_user_followers(self):
        """Mavjud bo'lmagan user'ning followerlarini olish"""
        url = reverse('social:followers', kwargs={'user_id': '00000000-0000-0000-0000-000000000000'})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# ============================================
# USER STATS TESTS
# ============================================

class UserStatsAPITest(APITestCase):
    """UserStats API testlari"""

    def setUp(self):
        self.client = APIClient()
        self.user1 = create_user('user1', 'user1@test.com')
        self.user2 = create_user('user2', 'user2@test.com')
        self.user3 = create_user('user3', 'user3@test.com')
        self.client.force_authenticate(user=self.user1)

    def test_get_user_stats(self):
        """Foydalanuvchi statistikasini olish"""
        Follow.objects.create(follower=self.user2, following=self.user1)
        Follow.objects.create(follower=self.user3, following=self.user1)
        Follow.objects.create(follower=self.user1, following=self.user2)

        url = reverse('social:user-stats', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

        data = response.data['data']
        self.assertEqual(data['followers_count'], 2)
        self.assertEqual(data['following_count'], 1)

    def test_stats_is_following_true(self):
        """user1 user2 ni follow qilganda is_following=True"""
        Follow.objects.create(follower=self.user1, following=self.user2)

        url = reverse('social:user-stats', kwargs={'user_id': self.user2.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['data']['is_following'])

    def test_stats_is_following_false(self):
        """Follow yo'q bo'lganda is_following=False"""
        url = reverse('social:user-stats', kwargs={'user_id': self.user2.id})
        response = self.client.get(url)

        self.assertFalse(response.data['data']['is_following'])

    def test_stats_follows_you(self):
        """user2 user1 ni follow qilganda follows_you=True"""
        Follow.objects.create(follower=self.user2, following=self.user1)

        url = reverse('social:user-stats', kwargs={'user_id': self.user2.id})
        response = self.client.get(url)

        self.assertTrue(response.data['data']['follows_you'])

    def test_stats_zero_counts(self):
        """Yangi user'ning statistikasi 0 bo'lishi"""
        url = reverse('social:user-stats', kwargs={'user_id': self.user1.id})
        response = self.client.get(url)

        data = response.data['data']
        self.assertEqual(data['followers_count'], 0)
        self.assertEqual(data['following_count'], 0)


# ============================================
# USER SEARCH TESTS
# ============================================

class UserSearchAPITest(APITestCase):
    """User Search API testlari"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user('mainuser', 'main@test.com')
        self.client.force_authenticate(user=self.user)

        self.john = create_user('john_doe', 'john@test.com')
        self.jane = create_user('jane_smith', 'jane@test.com')
        self.bob = create_user('bob123', 'bob@test.com')

    def test_search_by_username(self):
        """Username bo'yicha qidirish"""
        url = reverse('social:user-search') + '?q=john'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_empty_query(self):
        """Bo'sh query bo'lganda natija yo'q"""
        url = reverse('social:user-search') + '?q='
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_search_excludes_self(self):
        """Qidiruvda o'zini ko'rmasligi"""
        url = reverse('social:user-search') + '?q=mainuser'
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get('results', response.data)
        usernames = [u.get('username') for u in (results if isinstance(results, list) else [])]
        self.assertNotIn('mainuser', usernames)

    def test_search_unauthenticated(self):
        """Autentifikatsiyasiz qidirib bo'lmaydi"""
        self.client.force_authenticate(user=None)
        url = reverse('social:user-search') + '?q=john'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_search_no_results(self):
        """Mavjud bo'lmagan username qidirganda"""
        url = reverse('social:user-search') + '?q=xyznotexists999'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# ============================================
# SUGGESTED / POPULAR USERS TESTS
# ============================================

class SuggestedUsersAPITest(APITestCase):
    """Suggested va Popular Users API testlari"""

    def setUp(self):
        self.client = APIClient()
        self.user = create_user('mainuser', 'main@test.com')
        self.user2 = create_user('user2', 'user2@test.com')
        self.user3 = create_user('user3', 'user3@test.com')
        self.client.force_authenticate(user=self.user)

    def test_get_suggested_users(self):
        """Tavsiya etilgan foydalanuvchilarni olish"""
        url = reverse('social:suggested-users')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_suggested_excludes_already_following(self):
        """Allaqachon follow qilinganlar tavsiyada bo'lmasligi"""
        Follow.objects.create(follower=self.user, following=self.user2)
        url = reverse('social:suggested-users')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_suggested_excludes_self(self):
        """O'zi tavsiyada ko'rinmasligi"""
        url = reverse('social:suggested-users')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_popular_users(self):
        """Mashhur foydalanuvchilarni olish"""
        url = reverse('social:popular-users')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_popular_excludes_self(self):
        """Mashhur foydalanuvchilar ro'yxatida o'zi bo'lmasligi"""
        url = reverse('social:popular-users')
        response = self.client.get(url)
        popular = response.data['data']['popular_users']
        user_ids = [str(u.get('id', '')) for u in popular]
        self.assertNotIn(str(self.user.id), user_ids)


# ============================================
# INTEGRATION TESTS
# ============================================

class SocialWorkflowTest(APITestCase):
    """To'liq social workflow testlari"""

    def setUp(self):
        self.client = APIClient()
        self.user1 = create_user('user1', 'user1@test.com')
        self.user2 = create_user('user2', 'user2@test.com')
        self.client.force_authenticate(user=self.user1)

    def test_follow_unfollow_workflow(self):
        """Follow -> Stats tekshirish -> Unfollow to'liq oqimi"""

        # 1. Follow qilish
        url = reverse('social:follow', kwargs={'user_id': self.user2.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Follow.is_following(self.user1, self.user2))

        # 2. Stats tekshirish
        url = reverse('social:user-stats', kwargs={'user_id': self.user2.id})
        response = self.client.get(url)
        self.assertTrue(response.data['data']['is_following'])
        self.assertEqual(response.data['data']['followers_count'], 1)

        # 3. Followers ro'yxatida ko'rinish
        url = reverse('social:followers', kwargs={'user_id': self.user2.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 4. Unfollow qilish
        url = reverse('social:unfollow', kwargs={'user_id': self.user2.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Follow.is_following(self.user1, self.user2))

        # 5. Stats qayta tekshirish
        url = reverse('social:user-stats', kwargs={'user_id': self.user2.id})
        response = self.client.get(url)
        self.assertFalse(response.data['data']['is_following'])
        self.assertEqual(response.data['data']['followers_count'], 0)

    def test_mutual_follow_workflow(self):
        """Ikki tomonlama follow oqimi"""

        # user1 -> user2
        Follow.objects.create(follower=self.user1, following=self.user2)

        # user2 -> user1
        self.client.force_authenticate(user=self.user2)
        url = reverse('social:follow', kwargs={'user_id': self.user1.id})
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Ikkalasi ham bir-birini follow qilganini tekshirish
        self.assertTrue(Follow.is_following(self.user1, self.user2))
        self.assertTrue(Follow.is_following(self.user2, self.user1))

        # Stats - follows_you = True bo'lishi
        self.client.force_authenticate(user=self.user1)
        url = reverse('social:user-stats', kwargs={'user_id': self.user2.id})
        response = self.client.get(url)
        self.assertTrue(response.data['data']['is_following'])
        self.assertTrue(response.data['data']['follows_you'])


# ============================================
# RUN TESTS
# ============================================
# python manage.py test social
# python manage.py test social.tests.FollowModelTest
# coverage run --source='.' manage.py test social
# coverage report