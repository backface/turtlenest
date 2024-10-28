"""
URL configuration for turtlenest project.

"""

from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls import include
from django.conf.urls.static import static
from django.views.generic import RedirectView
# from wagtail.admin import urls as wagtailadmin_urls
# from wagtail import urls as wagtail_urls
# from wagtail.documents import urls as wagtaildocs_urls

from api.api_legacy import api as api_legacy
from api.api_v1 import api as api_v1
from apps.classrooms.views import GroupListView

admin.site.site_header = "TurtleStitch Nest Administration"
admin.site.site_title = "TurtleNest Administration"
admin.site.index_title = "Nest Administration"

urlpatterns = [
    # path("", TemplateView.as_view(template_name="index.html"), name="index"),
    # path("", RedirectView.as_view(pattern_name="projects_index")),
    # path("login", TemplateView.as_view(template_name="account/login.html"), name="login"),
    path("login/", RedirectView.as_view(pattern_name="account_login")),
    path("logout/", RedirectView.as_view(pattern_name="account_logout")),
    path("signup/", RedirectView.as_view(pattern_name="account_signup")),
    path("sign_up/", RedirectView.as_view(pattern_name="account_signup")),
    path("accounts/profile/", RedirectView.as_view(pattern_name="users:profile")),
    path("accounts/", include("allauth.urls")),

    # path('/projects/search', include('projects.urls')), # snap
    # path('/categories', include('projects.urls')), # snap
    # path('mygroups/', include('classrooms.urls')),
    # path('users/', include('users.urls')),
    # path('users/:username/projects/:projetname', include('projects.urls')),
    # path('user?', include('users.urls')), # snap
    # path('project?', include('projects.urls')), # snap

    # grappelli urls
    #path("grappelli/", include("grappelli.urls")),  # grappelli URLS

    path("admin/", admin.site.urls),
    path("hijack/", include("hijack.urls")),
    path('summernote/', include('django_summernote.urls')),

    # wagtail urls
    # path("cms/login/", RedirectView.as_view(pattern_name="account_login")),
    # path("cms/", include(wagtailadmin_urls)),
    # path("documents/", include(wagtaildocs_urls)),
    # path("content/", include(wagtail_urls)),
    # #path("page/", include(wagtail_urls)),
    
    path("page/", include("apps.pages.urls")),    
    path("user/", include("apps.users.urls")),
    path("group/", include("apps.classrooms.urls")),
    path("mygroups", GroupListView.as_view(), name="my_groups"),
    
    # path("make/", include("apps.wp_blog.urls")),
    
    path("tos", RedirectView.as_view(url="/page/tos")),
    path("", include("apps.projects.urls")),
    
    path("api/", api_legacy.urls),
    path("api/v1/", api_v1.urls),

    path("__reload__/", include("django_browser_reload.urls")),
]

if not settings.TESTING:
    urlpatterns = [
        *urlpatterns,
        path("__debug__/", include("debug_toolbar.urls")),
    ]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static("run", document_root=f"{settings.STATIC_ROOT}/run")
    
