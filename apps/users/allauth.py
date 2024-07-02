from apps.classrooms.models import Group
from allauth.account.adapter import DefaultAccountAdapter


class AccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        if request.user.is_puppet:
            group = Group.objects.filter(membership__user=request.user).first()
            return f"/group/{group.id}"
        else:
            return super().get_login_redirect_url(request)
