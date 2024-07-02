from django.dispatch import receiver
from allauth.account.signals import user_logged_in, user_logged_out


# @receiver(user_logged_in)
# def my_callback(request, user, **kwargs):
#     print(request, user, [k for k in kwargs])
#     print("user logged in!")


# @receiver(user_logged_out)
# def my_callback(request, user, **kwargs):
#     print(request, user, [k for k in kwargs])
#     print("user logged out!")
