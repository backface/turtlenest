from django.dispatch import receiver
from allauth.account.signals import user_logged_in
from .models import Group


@receiver(user_logged_in)
def on_user_logged_in(request, user, **kwargs):
    if user.is_puppet:
        #print("user is puppet")
        group = Group.objects.filter(membership__user=user).first()
        request.session["group"] = group.id
