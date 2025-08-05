from django.urls import path
from . import views

app_name = 'book'

urlpatterns = [
    path('', views.ListBookView.as_view(), name='list-book'),  # 一覧ページ
    path('<int:pk>/detail/', views.DetailBookView.as_view(), name='detail-book'),
    path('create/', views.CreateBookView.as_view(), name='create-book'),
    path('<int:pk>/delete/', views.DeleteBookView.as_view(), name='delete-book'),
    path('<int:pk>/update/', views.UpdateBookView.as_view(), name='update-book'),
    
    # ✅ レビュー投稿用URL（これだけ残す）
    path('<int:book_id>/review/', views.CreateReviewView.as_view(), name='create-review'),
    path('review/<int:pk>/update/', views.UpdateReviewView.as_view(), name='update-review'),
    path('review/<int:pk>/delete/', views.DeleteReviewView.as_view(), name='delete-review'),

    # 👍 参考になったボタン
    path('toggle_like/', views.toggle_like, name='toggle_like'),
]
