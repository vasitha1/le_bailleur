from django.shortcuts import render

def home(request):
    return render(request, 'home.html')

def onboarding(request):
    return render(request, 'onboarding.html')

def about(request):
    return render(request, 'about.html')