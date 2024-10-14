from django.contrib import admin
from django_summernote.admin import SummernoteModelAdmin
from .models import Page


@admin.register(Page)
class PageAdmin(SummernoteModelAdmin):
    list_display = ("title", "slug", "date_modified")
    search_fields = [
        "title", "content", "last_editor.username"
    ]
    raw_id_fields = ["last_editor",]
