from django.shortcuts import render, get_object_or_404
from .models import Page


# Create your views here.
def view_page(request, slug):
    page = get_object_or_404(Page, slug=slug)
    return render(request, "page.html", {"page": page})
