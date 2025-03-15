from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.views.generic import ListView
from django.views.generic import DetailView
from .models import Demo

# Create your views here.
def demo_view(request):
    return HttpResponse("Hello World")

# Create your views here.
def demo_single(request, demo_id, something):
    return HttpResponse("Hello World. Your id is: " + str(demo_id) + something)


def all_demos(request):
    context = {
        'items': Demo.objects.all().order_by('amount')
    }
    template = 'all-demos.html'

    return render(request, template, context)


def single_demo(request, demo_id):
    context = {
        'item': get_object_or_404(Demo, pk=demo_id)
    }
    template = 'single-demo.html'

    return render(request, template, context)


class DemoListView(ListView):
    model = Demo
    template_name = 'all-demos.html'
    context_object_name = 'items'


class DemoDetailView(DetailView):
    model = Demo
    template_name = 'single-demo.html'
    context_object_name = 'item'
    slug_field = 'id'  # Use 'id' as the slug field
    slug_url_kwarg = 'id'  # Match the URL parameter