# レビュー削除ビュー

from django.shortcuts import render, redirect
from django.views import generic
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q, Avg
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import Shelf, Review, CATEGORY, Like, Task 
from .forms import ReviewForm  # ← 追加する！

class DeleteReviewView(LoginRequiredMixin, generic.DeleteView):
    model = Review
    template_name = 'book/review_confirm_delete.html'
    
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user != self.request.user:
            raise PermissionDenied('削除権限がありません。')
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('book:detail-book', kwargs={'pk': self.object.book.id})
class ListBookView(LoginRequiredMixin, generic.ListView):
    template_name = 'book/book_list.html'
    model = Shelf
    context_object_name = 'Shelf'
    paginate_by = 10

    def get_queryset(self):
        queryset = Shelf.objects.all().order_by('-id')
        keyword = self.request.GET.get('keyword')
        category = self.request.GET.get('category')

        if keyword:
            queryset = queryset.filter(
                Q(title__icontains=keyword) | Q(text__icontains=keyword)
            )
        if category:
            queryset = queryset.filter(category=category)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = CATEGORY
        context['keyword'] = self.request.GET.get('keyword', '')
        context['selected_category'] = self.request.GET.get('category', '')

        ranking_list = (
            Shelf.objects.annotate(avg_rating=Avg('review__rate'))
            .order_by('-avg_rating')[:3]
        )
        context['ranking_list'] = ranking_list
        return context


class DetailBookView(LoginRequiredMixin, generic.DetailView):
    template_name = 'book/book_detail.html'
    model = Shelf
    context_object_name = 'Shelf'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        sort = self.request.GET.get('sort', 'new')

        if sort == 'rate':
            ordering = '-rate'
        else:
            ordering = '-id'

        reviews = Review.objects.filter(book=self.object).order_by(ordering)

        user_likes = Like.objects.filter(user=self.request.user, review__in=reviews)
        liked_review_ids = set(user_likes.values_list('review_id', flat=True))

        for review in reviews:
            review.is_liked = review.id in liked_review_ids
            review.like_count = review.likes.count()

        paginator = Paginator(reviews, 3)
        page_number = self.request.GET.get('page')
        context['reviews'] = paginator.get_page(page_number)
        context['review_count'] = reviews.count()
        context['current_sort'] = sort

        return context


class CreateBookView(LoginRequiredMixin, generic.CreateView):
    template_name = 'book/book_create.html'
    model = Shelf
    context_object_name = 'Shelf'
    fields = ('title', 'text', 'category', 'thumbnail')
    success_url = reverse_lazy('book:list-book')  # ← 名前空間付きに修正

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)


class DeleteBookView(LoginRequiredMixin, generic.DeleteView):
    template_name = 'book/book_confirm_delete.html'
    model = Shelf
    context_object_name = 'Shelf'
    success_url = reverse_lazy('book:list-book')  # ← 名前空間付きに修正

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user != self.request.user:
            raise PermissionDenied('削除権限がありません。')
        return super().dispatch(request, *args, **kwargs)


class UpdateBookView(LoginRequiredMixin, generic.UpdateView):
    template_name = 'book/book_update.html'
    model = Shelf
    context_object_name = 'Shelf'
    fields = ('title', 'text', 'category', 'thumbnail')
    success_url = reverse_lazy('book:list-book')  # ← 名前空間付きに修正

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user != self.request.user:
            raise PermissionDenied('編集権限がありません。')
        return super().dispatch(request, *args, **kwargs)


class CreateReviewView(LoginRequiredMixin, generic.CreateView):
    model = Review
    form_class = ReviewForm  # ← これを追加！
    template_name = 'book/review_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['book'] = Shelf.objects.get(pk=self.kwargs['book_id'])
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.book = Shelf.objects.get(pk=self.kwargs['book_id'])
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('book:detail-book', kwargs={'pk': self.object.book.id})  # ← 名前空間付きに修正


class UpdateReviewView(LoginRequiredMixin, generic.UpdateView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['book'] = self.object.book
        return context
    model = Review
    form_class = ReviewForm
    template_name = 'book/review_form.html'  # 投稿と同じフォームを使う

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.user != self.request.user:
            raise PermissionDenied('編集権限がありません。')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse('book:detail-book', kwargs={'pk': self.object.book.id})  # ← 名前空間付きに修正


class TaskListView(generic.ListView):
    model = Task
    template_name = 'book/task_list.html'  # Task用テンプレート
    context_object_name = 'tasks'


# 👍 参考になったボタン：いいねのトグル用API
@require_POST
@login_required
def toggle_like(request):
    review_id = request.POST.get('review_id')
    review = Review.objects.get(id=review_id)
    user = request.user

    like, created = Like.objects.get_or_create(user=user, review=review)

    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    like_count = review.likes.count()
    return JsonResponse({'liked': liked, 'like_count': like_count})
