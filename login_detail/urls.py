# -*- coding:utf-8 -*-
from django.urls import path
from . import views

# 设置命名空间名称
app_name = 'login_detail'

urlpatterns = [
    path('login_register/',views.login_register,name='login_register'),
    path('unique_username/',views.unique_username,name='unique_username'),
    path('unique_email/',views.unique_email,name='unique_email'),
    path('email_send/',views.email_send,name='email_send'),
    path('action_accounts/',views.action_accounts,name='action_accounts'),
]
