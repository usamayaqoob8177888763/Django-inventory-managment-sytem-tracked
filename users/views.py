from django.shortcuts import render

from django.http import HttpResponse

def home(request):
    return HttpResponse("Users Home Page")

# Create your views here.
