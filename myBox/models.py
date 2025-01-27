from django.db import models
from django.forms import ModelForm
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

sexChoices = {
    "male": '男',
    "female": '女',
    "unknown": '保密'
}

sexPreferChoices = {
    "male": '男',
    "female": '女',
    "both": '男女均可',
    "unknown": '未知'
}

MEDIA_ADDR = 'http://localhost/images'

# 模型类

class Profile(models.Model):
    username  = models.CharField(max_length=150)
    avatar    = ProcessedImageField(verbose_name="头像", upload_to='avatars/%Y/%m/%d', default='avatars/default.png', processors=[ResizeToFill(160, 160)])
    name      = models.CharField("名字", max_length=8, default="A OUCer")
    intro     = models.TextField("自我介绍", default="帅哥/靓女一枚")
    weight    = models.IntegerField("体重(kg)", default=60)
    email     = models.EmailField('邮箱', blank=True, null=True)
    height    = models.IntegerField("身高(cm)", default=170)
    age       = models.IntegerField("年龄", default=18)
    sex       = models.CharField("性别", max_length=8, choices=sexChoices, default="unknown")
    address   = models.TextField("地址", default="中国海洋大学")
    sexPrefer = models.CharField("性取向", max_length=8, choices=sexPreferChoices, default="unknown")

    def __str__(self):
        return self.name

    def get_avatar(self):
        return MEDIA_ADDR + str(self.avatar)

class Comment(models.Model):
    username = models.CharField(max_length=150)
    content = models.TextField()
    author = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    parent_comment = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='replies')

    def __str__(self):
        return self.content

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, label='邮箱')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("该邮箱已被注册，请使用其他邮箱。")
        return email

# 表单类

class AvatarForm(ModelForm):
    class Meta:
        model = Profile
        fields = ['avatar']

class ProfileForm(ModelForm):
    class Meta:
        model = Profile
        exclude = ['username', 'avatar', 'email']

class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ['content']