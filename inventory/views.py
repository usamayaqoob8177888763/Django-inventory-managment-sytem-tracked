from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return HttpResponse("Inventory Home Page")

# Create your views here.
