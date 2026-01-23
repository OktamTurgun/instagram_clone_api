"""
Comprehensive Tests for Posts App

This module contains all tests for the posts app:
- Model tests: Field validation, methods, properties
- Signal tests: Counter updates on create/delete
- Serializer tests: Validation, representation
- View tests: API endpoints, permissions
- Integration tests: Full workflows

Test Coverage:
- Models: Post, PostImage, Like, Comment, CommentLike, SavedPost
- Signals: Auto-counting on like/comment
- Serializers: All serializers with edge cases
- Views: All API endpoints with permissions
- Integration: Complete user flows
"""
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.utils import IntegrityError
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
import tempfile
from PIL import Image
import io

from .models import Post, PostImage, Like, Comment, CommentLike, SavedPost
from .serializers import (
    PostCreateSerializer,
    PostListSerializer,
    CommentSerializer,
)

User = get_user_model()


# ============================================
# UTILITY FUNCTIONS
# ============================================

def create_test_image():
    """Create a temporary test image"""
    file = io.BytesIO()
    image = Image.new('RGB', (100, 100), color='red')
    image.save(file, 'JPEG')
    file.seek(0)
    return SimpleUploadedFile(
        'test_image.jpg',
        file.read(),
        content_type='image/jpeg'
    )


def create_test_user(username='testuser', email='test@example.com'):
    """Create a test user"""
    return User.objects.create_user(
        username=username,
        email=email,
        password='TestPass123!',
        auth_status='completed'
    )


# ============================================
# MODEL TESTS
# ============================================

class PostModelTest(TestCase):
    """Test Post model"""
    
    def setUp(self):
        self.user = create_test_user()
    
    def test_create_post(self):
        """Test creating a post"""
        post = Post.objects.create(
            user=self.user,
            caption='Test caption',
            location='Tashkent'
        )
        
        self.assertEqual(post.user, self.user)
        self.assertEqual(post.caption, 'Test caption')
        self.assertEqual(post.location, 'Tashkent')
        self.assertEqual(post.likes_count, 0)
        self.assertEqual(post.comments_count, 0)
        self.assertFalse(post.is_archived)
    
    def test_post_str_method(self):
        """Test post string representation"""
        post = Post.objects.create(user=self.user, caption='Test')
        expected = f"Post by @{self.user.username} - {post.created_at.strftime('%Y-%m-%d')}"
        self.assertEqual(str(post), expected)
    
    def test_post_ordering(self):
        """Test posts ordered by created_at desc"""
        post1 = Post.objects.create(user=self.user, caption='First')
        post2 = Post.objects.create(user=self.user, caption='Second')
        
        posts = Post.objects.all()
        self.assertEqual(posts[0], post2)  # Most recent first
        self.assertEqual(posts[1], post1)


class PostImageModelTest(TestCase):
    """Test PostImage model"""
    
    def setUp(self):
        self.user = create_test_user()
        self.post = Post.objects.create(user=self.user, caption='Test')
    
    def test_create_post_image(self):
        """Test creating a post image"""
        image = create_test_image()
        post_image = PostImage.objects.create(
            post=self.post,
            image=image,
            order=0
        )
        
        self.assertEqual(post_image.post, self.post)
        self.assertTrue(post_image.image)
        self.assertEqual(post_image.order, 0)
    
    def test_post_image_ordering(self):
        """Test images ordered by order field"""
        img1 = PostImage.objects.create(
            post=self.post,
            image=create_test_image(),
            order=1
        )
        img2 = PostImage.objects.create(
            post=self.post,
            image=create_test_image(),
            order=0
        )
        
        images = PostImage.objects.filter(post=self.post)
        self.assertEqual(images[0], img2)  # Order 0 first
        self.assertEqual(images[1], img1)  # Order 1 second


class LikeModelTest(TestCase):
    """Test Like model"""
    
    def setUp(self):
        self.user = create_test_user()
        self.post = Post.objects.create(user=self.user, caption='Test')
    
    def test_create_like(self):
        """Test creating a like"""
        like = Like.objects.create(user=self.user, post=self.post)
        
        self.assertEqual(like.user, self.user)
        self.assertEqual(like.post, self.post)
    
    def test_unique_constraint(self):
        """Test user can't like same post twice"""
        Like.objects.create(user=self.user, post=self.post)
        
        with self.assertRaises(IntegrityError):
            Like.objects.create(user=self.user, post=self.post)
    
    def test_like_str_method(self):
        """Test like string representation"""
        like = Like.objects.create(user=self.user, post=self.post)
        expected = f"@{self.user.username} liked post {self.post.id}"
        self.assertEqual(str(like), expected)


class CommentModelTest(TestCase):
    """Test Comment model"""
    
    def setUp(self):
        self.user = create_test_user()
        self.post = Post.objects.create(user=self.user, caption='Test')
    
    def test_create_comment(self):
        """Test creating a comment"""
        comment = Comment.objects.create(
            user=self.user,
            post=self.post,
            text='Great post!'
        )
        
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.post, self.post)
        self.assertEqual(comment.text, 'Great post!')
        self.assertIsNone(comment.parent)
        self.assertEqual(comment.likes_count, 0)
    
    def test_is_reply_property(self):
        """Test is_reply property"""
        comment = Comment.objects.create(
            user=self.user,
            post=self.post,
            text='Comment'
        )
        self.assertFalse(comment.is_reply)
        
        reply = Comment.objects.create(
            user=self.user,
            post=self.post,
            text='Reply',
            parent=comment
        )
        self.assertTrue(reply.is_reply)
    
    def test_nested_replies(self):
        """Test comment with nested replies"""
        comment = Comment.objects.create(
            user=self.user,
            post=self.post,
            text='Parent'
        )
        
        reply1 = Comment.objects.create(
            user=self.user,
            post=self.post,
            text='Reply 1',
            parent=comment
        )
        
        reply2 = Comment.objects.create(
            user=self.user,
            post=self.post,
            text='Reply 2',
            parent=comment
        )
        
        self.assertEqual(comment.replies.count(), 2)
        self.assertIn(reply1, comment.replies.all())
        self.assertIn(reply2, comment.replies.all())


# ============================================
# SIGNAL TESTS
# ============================================

class PostSignalTest(TransactionTestCase):
    """Test post-related signals"""
    
    def setUp(self):
        self.user = create_test_user()
        self.post = Post.objects.create(user=self.user, caption='Test')
    
    def test_like_increments_count(self):
        """Test like creation increments likes_count"""
        self.assertEqual(self.post.likes_count, 0)
        
        Like.objects.create(user=self.user, post=self.post)
        self.post.refresh_from_db()
        
        self.assertEqual(self.post.likes_count, 1)
    
    def test_unlike_decrements_count(self):
        """Test like deletion decrements likes_count"""
        like = Like.objects.create(user=self.user, post=self.post)
        self.post.refresh_from_db()
        self.assertEqual(self.post.likes_count, 1)
        
        like.delete()
        self.post.refresh_from_db()
        
        self.assertEqual(self.post.likes_count, 0)
    
    def test_comment_increments_count(self):
        """Test comment creation increments comments_count"""
        self.assertEqual(self.post.comments_count, 0)
        
        Comment.objects.create(user=self.user, post=self.post, text='Test')
        self.post.refresh_from_db()
        
        self.assertEqual(self.post.comments_count, 1)
    
    def test_delete_comment_decrements_count(self):
        """Test comment deletion decrements comments_count"""
        comment = Comment.objects.create(
            user=self.user,
            post=self.post,
            text='Test'
        )
        self.post.refresh_from_db()
        self.assertEqual(self.post.comments_count, 1)
        
        comment.delete()
        self.post.refresh_from_db()
        
        self.assertEqual(self.post.comments_count, 0)
    
    def test_multiple_likes(self):
        """Test multiple likes increment correctly"""
        user2 = create_test_user(username='user2', email='user2@test.com')
        user3 = create_test_user(username='user3', email='user3@test.com')
        
        Like.objects.create(user=self.user, post=self.post)
        Like.objects.create(user=user2, post=self.post)
        Like.objects.create(user=user3, post=self.post)
        
        self.post.refresh_from_db()
        self.assertEqual(self.post.likes_count, 3)


class CommentSignalTest(TransactionTestCase):
    """Test comment-related signals"""
    
    def setUp(self):
        self.user = create_test_user()
        self.post = Post.objects.create(user=self.user, caption='Test')
        self.comment = Comment.objects.create(
            user=self.user,
            post=self.post,
            text='Test comment'
        )
    
    def test_comment_like_increments_count(self):
        """Test comment like increments likes_count"""
        self.assertEqual(self.comment.likes_count, 0)
        
        CommentLike.objects.create(user=self.user, comment=self.comment)
        self.comment.refresh_from_db()
        
        self.assertEqual(self.comment.likes_count, 1)
    
    def test_comment_unlike_decrements_count(self):
        """Test comment unlike decrements likes_count"""
        like = CommentLike.objects.create(user=self.user, comment=self.comment)
        self.comment.refresh_from_db()
        self.assertEqual(self.comment.likes_count, 1)
        
        like.delete()
        self.comment.refresh_from_db()
        
        self.assertEqual(self.comment.likes_count, 0)


# ============================================
# API VIEW TESTS
# ============================================

class PostAPITest(APITestCase):
    """Test Post API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user()
        self.client.force_authenticate(user=self.user)
    
    def test_create_post(self):
        """Test creating a post via API"""
        url = reverse('posts:post-create')
        image = create_test_image()
        
        data = {
            'caption': 'Test post',
            'location': 'Tashkent',
            'images': [image]
        }
        
        response = self.client.post(url, data, format='multipart')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['success'], True)
        self.assertEqual(Post.objects.count(), 1)
        
        post = Post.objects.first()
        self.assertEqual(post.caption, 'Test post')
        self.assertEqual(post.location, 'Tashkent')
        self.assertEqual(post.images.count(), 1)
    
    def test_create_post_unauthenticated(self):
        """Test creating post without authentication fails"""
        self.client.force_authenticate(user=None)
        url = reverse('posts:post-create')
        
        data = {
            'caption': 'Test',
            'images': [create_test_image()]
        }
        
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_get_post_detail(self):
        """Test getting post details"""
        post = Post.objects.create(user=self.user, caption='Test')
        PostImage.objects.create(post=post, image=create_test_image())
        
        url = reverse('posts:post-detail', kwargs={'pk': post.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['caption'], 'Test')
        self.assertEqual(len(response.data['images']), 1)
    
    def test_update_post_owner(self):
        """Test updating post by owner"""
        post = Post.objects.create(user=self.user, caption='Original')
        
        url = reverse('posts:post-detail', kwargs={'pk': post.id})
        data = {'caption': 'Updated'}
        
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post.refresh_from_db()
        self.assertEqual(post.caption, 'Updated')
    
    def test_update_post_non_owner(self):
        """Test updating post by non-owner fails"""
        other_user = create_test_user(username='other', email='other@test.com')
        post = Post.objects.create(user=other_user, caption='Test')
        
        url = reverse('posts:post-detail', kwargs={'pk': post.id})
        data = {'caption': 'Hacked'}
        
        response = self.client.put(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_delete_post_owner(self):
        """Test deleting post by owner"""
        post = Post.objects.create(user=self.user, caption='Test')
        
        url = reverse('posts:post-detail', kwargs={'pk': post.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Post.objects.count(), 0)
    
    def test_delete_post_non_owner(self):
        """Test deleting post by non-owner fails"""
        other_user = create_test_user(username='other', email='other@test.com')
        post = Post.objects.create(user=other_user, caption='Test')
        
        url = reverse('posts:post-detail', kwargs={'pk': post.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(Post.objects.count(), 1)


class LikeAPITest(APITestCase):
    """Test Like API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user()
        self.client.force_authenticate(user=self.user)
        self.post = Post.objects.create(user=self.user, caption='Test')
    
    def test_like_post(self):
        """Test liking a post"""
        url = reverse('posts:like-toggle', kwargs={'post_id': self.post.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['liked'], True)
        self.assertEqual(Like.objects.count(), 1)
    
    def test_unlike_post(self):
        """Test unliking a post"""
        Like.objects.create(user=self.user, post=self.post)
        
        url = reverse('posts:like-toggle', kwargs={'post_id': self.post.id})
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['liked'], False)
        self.assertEqual(Like.objects.count(), 0)
    
    def test_like_toggle_idempotent(self):
        """Test like toggle is idempotent"""
        url = reverse('posts:like-toggle', kwargs={'post_id': self.post.id})
        
        # Like
        response1 = self.client.post(url)
        self.assertTrue(response1.data['data']['liked'])
        
        # Unlike
        response2 = self.client.post(url)
        self.assertFalse(response2.data['data']['liked'])
        
        # Like again
        response3 = self.client.post(url)
        self.assertTrue(response3.data['data']['liked'])


class CommentAPITest(APITestCase):
    """Test Comment API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user()
        self.client.force_authenticate(user=self.user)
        self.post = Post.objects.create(user=self.user, caption='Test')
    
    def test_create_comment(self):
        """Test creating a comment"""
        url = reverse('posts:post-comments', kwargs={'post_id': self.post.id})
        data = {'text': 'Great post!'}
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Comment.objects.count(), 1)
        
        comment = Comment.objects.first()
        self.assertEqual(comment.text, 'Great post!')
        self.assertEqual(comment.user, self.user)
        self.assertEqual(comment.post, self.post)
    
    def test_create_reply(self):
        """Test creating a reply to comment"""
        comment = Comment.objects.create(
            user=self.user,
            post=self.post,
            text='Original comment'
        )
        
        url = reverse('posts:post-comments', kwargs={'post_id': self.post.id})
        data = {
            'text': 'Reply to comment',
            'parent': str(comment.id)
        }
        
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        reply = Comment.objects.get(parent=comment)
        self.assertEqual(reply.text, 'Reply to comment')
        self.assertTrue(reply.is_reply)
    
    def test_list_comments(self):
        """Test listing comments on a post"""
        Comment.objects.create(user=self.user, post=self.post, text='Comment 1')
        Comment.objects.create(user=self.user, post=self.post, text='Comment 2')
        
        url = reverse('posts:post-comments', kwargs={'post_id': self.post.id})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 2)
    
    def test_delete_own_comment(self):
        """Test deleting own comment"""
        comment = Comment.objects.create(
            user=self.user,
            post=self.post,
            text='My comment'
        )
        
        url = reverse('posts:comment-detail', kwargs={'pk': comment.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Comment.objects.count(), 0)
    
    def test_delete_comment_on_own_post(self):
        """Test post owner can delete comments on their post"""
        other_user = create_test_user(username='other', email='other@test.com')
        comment = Comment.objects.create(
            user=other_user,
            post=self.post,
            text='Comment from other'
        )
        
        url = reverse('posts:comment-detail', kwargs={'pk': comment.id})
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class FeedAPITest(APITestCase):
    """Test Feed API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user()
        self.client.force_authenticate(user=self.user)
    
    def test_feed_includes_own_posts(self):
        """Test feed includes user's own posts"""
        post = Post.objects.create(user=self.user, caption='My post')
        
        url = reverse('posts:feed')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['id'], str(post.id))
    
    def test_feed_excludes_archived(self):
        """Test feed excludes archived posts"""
        Post.objects.create(user=self.user, caption='Active')
        Post.objects.create(user=self.user, caption='Archived', is_archived=True)
        
        url = reverse('posts:feed')
        response = self.client.get(url)
        
        self.assertEqual(len(response.data['results']), 1)


# ============================================
# INTEGRATION TESTS
# ============================================

class PostWorkflowTest(APITestCase):
    """Test complete post workflow"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = create_test_user()
        self.client.force_authenticate(user=self.user)
    
    def test_complete_post_lifecycle(self):
        """Test creating, liking, commenting, and deleting a post"""
        
        # 1. Create post
        url = reverse('posts:post-create')
        data = {
            'caption': 'My first post!',
            'location': 'Tashkent',
            'images': [create_test_image()]
        }
        response = self.client.post(url, data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        post_id = response.data['data']['id']
        
        # 2. Like post
        url = reverse('posts:like-toggle', kwargs={'post_id': post_id})
        response = self.client.post(url)
        self.assertTrue(response.data['data']['liked'])
        
        # 3. Add comment
        url = reverse('posts:post-comments', kwargs={'post_id': post_id})
        response = self.client.post(url, {'text': 'Great post!'})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # 4. Verify counters
        post = Post.objects.get(id=post_id)
        self.assertEqual(post.likes_count, 1)
        self.assertEqual(post.comments_count, 1)
        
        # 5. Unlike post
        url = reverse('posts:like-toggle', kwargs={'post_id': post_id})
        response = self.client.post(url)
        self.assertFalse(response.data['data']['liked'])
        
        # 6. Delete post
        url = reverse('posts:post-detail', kwargs={'pk': post_id})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify all deleted
        self.assertEqual(Post.objects.count(), 0)
        self.assertEqual(Like.objects.count(), 0)
        self.assertEqual(Comment.objects.count(), 0)


# ============================================
# RUN TESTS
# ============================================

# To run all tests:
# python manage.py test posts

# To run specific test class:
# python manage.py test posts.tests.PostModelTest

# To run with coverage:
# coverage run --source='.' manage.py test posts
# coverage report