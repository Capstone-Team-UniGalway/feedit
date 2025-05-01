from django import forms
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import (
    ListView,
    DetailView,
    CreateView,
    UpdateView,
    DeleteView,
)
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.db.models import Q, Prefetch

from .models import Thread, Mention
from .forms import ThreadForm, ThreadReplyForm
from app.mixins import FullyActivatedUserMixin


class ThreadListView(FullyActivatedUserMixin, ListView):
    """View for listing threads."""

    model = Thread
    template_name = "pages/threads/thread_list.html"
    context_object_name = "threads"
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        # Access threads via user.workplace (employee) or user.company (employer)
        company = user.workplace or getattr(user, "company", None)
        if not company:
            return Thread.objects.none()

        queryset = company.threads.filter(parent__isnull=True, is_deleted=False)

        # Apply search
        search = self.request.GET.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(content__icontains=search)
            )

        # Apply type filter
        thread_type = self.request.GET.get("type")
        if thread_type:
            queryset = queryset.filter(type=thread_type)

        # Apply visibility filtering by role
        if user.workplace:
            # Employee: internal + private, allow narrowing by GET param
            allowed_visibilities = [
                Thread.ThreadVisibility.INTERNAL,
                Thread.ThreadVisibility.PRIVATE,
            ]
            requested_visibility = self.request.GET.get("visibility")
            if requested_visibility in allowed_visibilities:
                queryset = queryset.filter(visibility=requested_visibility)
            else:
                queryset = queryset.filter(visibility__in=allowed_visibilities)
        else:
            # Employer: only internal, no GET param filtering
            queryset = queryset.filter(visibility=Thread.ThreadVisibility.INTERNAL)

        # Sorting
        sort_by = self.request.GET.get("sort", "-created_at")
        valid_sort_fields = [
            "created_at",
            "-created_at",
            "updated_at",
            "-updated_at",
            "title",
            "-title",
        ]
        queryset = queryset.order_by(
            sort_by if sort_by in valid_sort_fields else "-created_at"
        )

        return queryset.select_related("author", "company").prefetch_related("replies")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        context["page_title"] = "Threads"
        context["search_query"] = self.request.GET.get("search", "")
        context["thread_type"] = self.request.GET.get("type", "")
        context["sort_by"] = self.request.GET.get("sort", "-created_at")
        context["thread_types"] = Thread.ThreadType.choices

        # Only add visibility filter context if employee
        if user.workplace:
            context["visibility"] = self.request.GET.get("visibility", "")
            context["visibility_types"] = Thread.ThreadVisibility.choices

        return context


class ThreadDetailView(FullyActivatedUserMixin, DetailView):
    """View for displaying a single thread and its replies."""

    model = Thread
    template_name = "pages/threads/thread_detail.html"
    context_object_name = "thread"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()

        user = request.user
        is_employer = getattr(user, "company", None)
        same_company = (user.workplace and user.workplace == self.object.company) or (
            is_employer and user.company == self.object.company
        )

        if not same_company or (
            self.object.visibility == Thread.ThreadVisibility.PRIVATE and is_employer
        ):
            messages.error(request, "You do not have access to this thread.")
            return redirect("thread_list")

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        return (
            Thread.objects.filter(is_deleted=False)
            .select_related("author", "company")
            .prefetch_related(
                Prefetch(
                    "replies",
                    queryset=Thread.objects.filter(is_deleted=False).select_related(
                        "author"
                    ),
                )
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thread = self.object

        # Replies already prefetched → no extra query
        context["replies"] = thread.replies.order_by("created_at")
        context["reply_form"] = ThreadReplyForm()

        if self.request.user.is_authenticated:
            Mention.objects.filter(
                thread=thread, mentioned_user=self.request.user, is_read=False
            ).update(is_read=True)

        return context


class ThreadCreateView(FullyActivatedUserMixin, CreateView):
    """View for creating a new thread."""

    model = Thread
    form_class = ThreadForm
    template_name = "pages/threads/thread_form.html"

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.workplace and not getattr(user, "company", None):
            messages.info(
                request,
                "Please join, claim or create a company before creating a thread.",
            )
            return redirect("companies:list")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user = self.request.user

        # Patch POST data to inject required hidden values before validation
        if self.request.method == "POST":
            data = kwargs["data"].copy()  # make mutable

            if user.type == user.UserType.EMPLOYEE:
                data["type"] = Thread.ThreadType.FORUM
            elif user.type == user.UserType.EMPLOYER:
                data["visibility"] = Thread.ThreadVisibility.INTERNAL

            kwargs["data"] = data

        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user

        # Hide restricted fields in the form
        if user.type == user.UserType.EMPLOYEE:
            form.fields["type"].widget = forms.HiddenInput()
        elif user.type == user.UserType.EMPLOYER:
            form.fields["visibility"].widget = forms.HiddenInput()

        return form

    def form_valid(self, form):
        user = self.request.user
        form.instance.author = user

        # Enforce type and visibility rules at save level
        # (in case someone bypasses the form)
        if user.type == user.UserType.EMPLOYEE:
            form.instance.company = user.workplace
            form.instance.type = Thread.ThreadType.FORUM  # hard-enforced
        elif user.type == user.UserType.EMPLOYER:
            form.instance.company = user.company
            form.instance.visibility = Thread.ThreadVisibility.INTERNAL  # hard-enforced

        messages.success(self.request, "Thread created successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()


class ThreadUpdateView(FullyActivatedUserMixin, UpdateView):
    """View for updating a thread."""

    model = Thread
    form_class = ThreadForm
    template_name = "pages/threads/thread_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.author != request.user:
            messages.error(request, "You are not allowed to edit this thread.")
            return redirect("thread_list")

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        user = self.request.user

        if self.request.method == "POST":
            data = kwargs["data"].copy()

            if user.type == user.UserType.EMPLOYEE:
                data["type"] = Thread.ThreadType.FORUM
            elif user.type == user.UserType.EMPLOYER:
                data["visibility"] = Thread.ThreadVisibility.INTERNAL

            kwargs["data"] = data

        return kwargs

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user

        if user.type == user.UserType.EMPLOYEE:
            form.fields["type"].widget = forms.HiddenInput()
        elif user.type == user.UserType.EMPLOYER:
            form.fields["visibility"].widget = forms.HiddenInput()

        return form

    def form_valid(self, form):
        user = self.request.user

        if user.type == user.UserType.EMPLOYEE:
            form.instance.company = user.workplace
            form.instance.type = Thread.ThreadType.FORUM
        elif user.type == user.UserType.EMPLOYER:
            form.instance.company = user.company
            form.instance.visibility = Thread.ThreadVisibility.INTERNAL

        messages.success(self.request, "Thread updated successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.get_absolute_url()


class ThreadDeleteView(FullyActivatedUserMixin, DeleteView):
    """View for deleting a thread."""

    model = Thread
    template_name = "pages/threads/thread_confirm_delete.html"
    success_url = reverse_lazy("thread_list")

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()

        if self.object.author != request.user and not request.user.is_superuser:
            messages.error(request, "You are not allowed to delete this thread.")
            return redirect("thread_list")

        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        thread = self.get_object()
        thread.delete()  # soft delete via BaseModel
        messages.success(request, f'Thread "{thread.title}" has been deleted.')
        return HttpResponseRedirect(self.success_url)


class ThreadReplyCreateView(FullyActivatedUserMixin, CreateView):
    """View for creating a reply to a thread."""

    model = Thread
    form_class = ThreadReplyForm
    template_name = "pages/threads/thread_reply_form.html"

    def get_parent_thread(self):
        return get_object_or_404(Thread, pk=self.kwargs["pk"], is_deleted=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["thread"] = self.get_parent_thread()
        return context

    def form_valid(self, form):
        parent = self.get_parent_thread()
        form.instance.author = self.request.user
        form.instance.parent = parent
        form.instance.company = parent.company
        form.instance.type = parent.type
        form.instance.visibility = parent.visibility
        form.instance.title = f"Re: {parent.title}"
        messages.success(self.request, "Reply added successfully!")
        return super().form_valid(form)

    def get_success_url(self):
        return self.object.parent.get_absolute_url()
