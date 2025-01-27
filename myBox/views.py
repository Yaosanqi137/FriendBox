from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib import messages
from django.core.mail import EmailMessage
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode

from myBox.models import *
from .models import Profile


def login_view(request):
    if request.method == "GET":
        return render(request, 'Login.html')
    elif request.method == "POST":
        username_or_email = request.POST.get('username')
        password = request.POST.get('password')

        # 判断输入的是用户名还是邮箱
        if '@' in username_or_email:  # 如果是邮箱
            try:
                user = User.objects.get(email=username_or_email)
                username = user.username
            except User.DoesNotExist:
                return render(request, 'Login.html', {'error': '邮箱未注册!'})
        else:  # 如果是用户名
            username = username_or_email

        # 使用用户名和密码进行认证
        user = authenticate(username=username, password=password)
        if user is None:
            return render(request, 'Login.html', {'error': '用户名或密码错误!'})
        elif not user.is_active:
            return render(request, 'Login.html', {'error': '账户未激活，请查收邮件并激活!'})
        else:
            login(request, user)
            return HttpResponseRedirect('/')

def logout_view(request):
    logout(request)
    return HttpResponseRedirect('/login')

def register_view(request):
    if request.method == "GET":
        regForm = CustomUserCreationForm()
        return render(request, 'Register.html', {'regForm': regForm})
    elif request.method == "POST":
        regForm = CustomUserCreationForm(request.POST)
        if regForm.is_valid():
            user = regForm.save(commit=False)
            user.is_active = False
            user.save()

            subject = '邮箱验证'
            message = render_to_string('Reg_email.html', {
                'user': user,
                'domain': 'ouc.gstech.fun',  # 你的域名
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user),
            })
            email = EmailMessage(subject, message, 'm17866819721@163.com', [user.email])
            email.content_subtype = "html"
            try:
                email.send(fail_silently=False)
            except Exception as e:
                messages.error(request, f'验证邮件发送失败!{e},请重新注册试试!')
                user.delete()
                return redirect('/login')
            messages.success(request, '验证邮件发送成功！已将您重定向回登录页面!')
            return redirect('/login')
        else:
            return render(request, 'Register.html', {'regForm': regForm})

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        newUser = Profile.objects.create(username=user.username, email=user.email)
        newUser.save()
        login(request, user)

        return redirect('/')  # 成功
    else:
        return redirect('/register')  # 失败

@login_required(login_url='/login/')
def profile_view(request):
    profile = get_object_or_404(Profile, username=request.user.username)
    avatar = get_object_or_404(Profile, username=request.user.username)
    if request.method == "POST":
        if 'avatar' in request.FILES:  # 判断是否提交了头像
            avatarForm = AvatarForm(request.POST, request.FILES, instance=avatar)
            if avatarForm.is_valid():
                avatarForm.save()
                return HttpResponseRedirect('/profile')
        else:  # 处理资料表单
            profileForm = ProfileForm(request.POST, instance=profile)
            if profileForm.is_valid():
                profileForm.save()
                return HttpResponseRedirect('/profile')
    else:
        profileForm = ProfileForm(instance=profile)
        avatarForm = AvatarForm(instance=avatar)
    context = {
        'profileForm': profileForm,
        'avatarForm': avatarForm,
        'profile': profile,
    }
    return render(request, 'Profile.html', context)

@login_required(login_url='/login/')
def hub_view(request):
    profile = get_object_or_404(Profile, username=request.user.username)
    context = {
        'profile': profile,
        'boybox': reverse('boybox'),
        'mybox': reverse('mybox'),
        'girlbox': reverse('girlbox'),
    }
    if request.method == "GET":
        return render(request, 'Hub.html', context)

# @login_required(login_url='/login/')
# def comment_view(request):
#     person_name = request.GET.get('person_name')
#     comments = Comment.objects.filter(username=person_name, parent_comment=None)
#     if request.method == "POST":
#         commentForm = CommentForm(request.POST)
#         if commentForm.is_valid():
#             content = commentForm.cleaned_data['content']
#             parent_comment = commentForm.cleaned_data['parent_comment']
#             if parent_comment:
#                 parent_comment = Comment.objects.filter(parent_comment=parent_comment)
#                 comment = Comment(content=content, author=request.user.username, parent_comment=parent_comment)
#             else:
#                 comment = Comment(content=content, author=request.user.username)
#             comment.save()
#             return HttpResponseRedirect('/comments/' + person_name)
#     else:
#         commentForm = CommentForm()
#     return render(request, 'Comments.html', {'comments': comments, 'commentForm': commentForm})

def mybox_view(request):
    profile = Profile.objects.get(username=request.user.username)
    if profile.sex != 'unknown':
        if profile.sexPrefer == 'both':
            boxes = Profile.objects.exclude(username=request.user.username)
        elif profile.sexPrefer == 'male' or profile.sex == 'male':
            boxes = Profile.objects.exclude(username=request.user.username).filter(sexPrefer=profile.sex, sex=profile.sexPrefer)
    else:
        boxes = {}
    return render(request, 'MyBox.html', {'profile': profile, 'boxes': boxes})

@login_required(login_url='/login/')
def delete_view(request):
    if request.method == "POST":
        confirm = request.POST.get('confirm')
        if confirm == '我确认':
            user = request.user
            user.delete()
            Profile.objects.filter(username=request.user.username).delete()
            messages.success(request, "您的账户已经成功删除，感谢您的陪伴...")
            return redirect('/login')
    return render(request, 'Delete.html')

def boybox_view(request):
    query_name = request.GET.get('name')
    query_height = request.GET.get('height')
    query_weight = request.GET.get('weight')
    query_age = request.GET.get('age')
    boys = Profile.objects.filter(sex='male')
    if query_name:
        boys = boys.filter(name__icontains=query_name)
    if query_height:
        boys = boys.filter(height__icontains=query_height)
    if query_weight:
        boys = boys.filter(weight__icontains=query_weight)
    if query_age:
        boys = boys.filter(age__icontains=query_age)
    return render(request, 'BoyBox.html', {'boys': boys})

def girlbox_view(request):
    query_name = request.GET.get('name')
    query_height = request.GET.get('height')
    query_weight = request.GET.get('weight')
    query_age = request.GET.get('age')
    girls = Profile.objects.filter(sex='female')
    if query_name:
        girls = girls.filter(name__icontains=query_name)
    if query_height:
        girls = girls.filter(height__icontains=query_height)
    if query_weight:
        girls = girls.filter(weight__icontains=query_weight)
    if query_age:
        girls = girls.filter(age__icontains=query_age)
    return render(request, 'GirlBox.html', {'girls': girls})





