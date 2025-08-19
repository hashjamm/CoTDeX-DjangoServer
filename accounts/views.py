from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from .models import UserProfile
from .forms import SignupForm
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView
from .forms import LoginForm

def signup(request):
    if request.method == 'POST':
        # 폼에서 받은 값들 사용 예시
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        phone = request.POST['phone_number']

        user = User.objects.create_user(username=username, password=password, email=email)
        UserProfile.objects.create(user=user, phone_number=phone)

        return redirect('login')


def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('login')  # 회원가입 후 로그인 페이지로 이동
    else:
        form = SignupForm()
    return render(request, 'accounts/signup.html', {'form': form})


def custom_logout(request):
    logout(request)
    return redirect('/network/')

class CustomLoginView(LoginView):
    form_class = LoginForm
    template_name = 'accounts/login.html'