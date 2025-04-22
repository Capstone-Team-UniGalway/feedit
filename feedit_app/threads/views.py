from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.db import models

from .models import Thread, Mention
from .forms import ThreadForm, ThreadReplyForm


class ThreadListView(LoginRequiredMixin, ListView):
    """View for listing threads."""
    model = Thread
    template_name = 'threads/thread_list.html'
    context_object_name = 'threads'
    paginate_by = 10

    def get_queryset(self):
        # Get threads that the user has access to
        queryset = super().get_queryset()

        # Filter by company if the user is associated with one
        if hasattr(self.request.user, 'workplace') and self.request.user.workplace:
            queryset = queryset.filter(company=self.request.user.workplace)

        # Filter out replies (only show parent threads)
        queryset = queryset.filter(parent__isnull=True)

        # Filter out deleted threads
        queryset = queryset.filter(is_deleted=False)

        # Apply search filter if provided
        search_query = self.request.GET.get('search')
        if search_query:
            queryset = queryset.filter(
                models.Q(title__icontains=search_query) |
                models.Q(content__icontains=search_query)
            )

        # Apply type filter if provided
        thread_type = self.request.GET.get('type')
        if thread_type:
            queryset = queryset.filter(type=thread_type)

        # Apply visibility filter if provided
        visibility = self.request.GET.get('visibility')
        if visibility:
            queryset = queryset.filter(visibility=visibility)

        # Apply sorting
        sort_by = self.request.GET.get('sort', '-created_at')
        valid_sort_fields = ['created_at', '-created_at', 'updated_at', '-updated_at', 'title', '-title']
        if sort_by in valid_sort_fields:
            queryset = queryset.order_by(sort_by)
        else:
            queryset = queryset.order_by('-created_at')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Threads'

        # Add filter parameters to context for form persistence
        context['search_query'] = self.request.GET.get('search', '')
        context['thread_type'] = self.request.GET.get('type', '')
        context['visibility'] = self.request.GET.get('visibility', '')
        context['sort_by'] = self.request.GET.get('sort', '-created_at')

        # Add thread type and visibility choices for the filter form
        context['thread_types'] = Thread.ThreadType.choices
        context['visibility_types'] = Thread.ThreadVisibility.choices

        return context


class ThreadDetailView(LoginRequiredMixin, DetailView):
    """View for displaying a single thread and its replies."""
    model = Thread
    template_name = 'threads/thread_detail.html'
    context_object_name = 'thread'

    def get_queryset(self):
        # Only show non-deleted threads
        return Thread.objects.filter(is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add replies to the context
        thread = self.get_object()
        context['replies'] = thread.replies.order_by('created_at')

        # Add form for replying
        context['reply_form'] = ThreadReplyForm()

        # Mark any mentions of the current user as read
        if self.request.user.is_authenticated:
            mentions = Mention.objects.filter(
                thread=thread,
                mentioned_user=self.request.user,
                is_read=False
            )
            for mention in mentions:
                mention.mark_as_read()

        return context


class ThreadCreateView(LoginRequiredMixin, CreateView):
    """View for creating a new thread."""
    model = Thread
    form_class = ThreadForm
    template_name = 'threads/thread_form.html'

    def form_valid(self, form):
        # Set the author to the current user
        form.instance.author = self.request.user

        # Set the company if the user is associated with one
        if hasattr(self.request.user, 'workplace') and self.request.user.workplace:
            form.instance.company = self.request.user.workplace
        else:
            # Create a default company if the user doesn't have one
            from companies.models import Company
            company = Company.objects.first()
            if not company:
                company = Company.objects.create(name='FeedIT Company', country='US')
            self.request.user.workplace = company
            self.request.user.save()
            form.instance.company = company
            messages.info(self.request, 'You have been associated with the default company.')

        messages.success(self.request, 'Thread created successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('thread_detail', kwargs={'pk': self.object.pk})


class ThreadReplyCreateView(LoginRequiredMixin, CreateView):
    """View for creating a reply to a thread."""
    model = Thread
    form_class = ThreadReplyForm
    template_name = 'threads/thread_reply_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add the parent thread to the context
        context['thread'] = get_object_or_404(Thread, pk=self.kwargs.get('pk'))
        return context

    def form_valid(self, form):
        # Get the parent thread
        parent_thread = get_object_or_404(Thread, pk=self.kwargs.get('pk'))

        # Set the author to the current user
        form.instance.author = self.request.user

        # Set the parent thread
        form.instance.parent = parent_thread

        # Set the company to the same as the parent thread
        form.instance.company = parent_thread.company

        # Set the type and visibility to match the parent
        form.instance.type = parent_thread.type
        form.instance.visibility = parent_thread.visibility

        # Set a title for the reply (optional)
        form.instance.title = f"Re: {parent_thread.title}"

        messages.success(self.request, 'Reply added successfully!')
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('thread_detail', kwargs={'pk': self.object.parent.pk})


class ThreadUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating a thread."""
    model = Thread
    form_class = ThreadForm
    template_name = 'threads/thread_form.html'

    def get_queryset(self):
        # Only allow the author to update the thread
        return Thread.objects.filter(author=self.request.user)

    def get_success_url(self):
        return reverse('thread_detail', kwargs={'pk': self.object.pk})


class ThreadDeleteView(LoginRequiredMixin, DeleteView):
    """View for deleting a thread."""
    model = Thread
    template_name = 'threads/thread_confirm_delete.html'
    success_url = reverse_lazy('thread_list')

    def get_queryset(self):
        # Only allow the author to delete the thread
        return Thread.objects.filter(author=self.request.user)

    def post(self, request, *args, **kwargs):
        # Get the thread
        thread = self.get_object()

        # Soft delete the thread (BaseModel.delete() handles this)
        thread.delete()

        # Add success message
        messages.success(self.request, f'Thread "{thread.title}" has been deleted.')

        # Redirect to success URL
        return HttpResponseRedirect(self.success_url)