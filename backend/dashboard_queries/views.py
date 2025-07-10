from django.shortcuts import render
from django.http import JsonResponse

# Create your views here.

def dashboard_queries(request):
    """API to handle dashboard queries"""
    return JsonResponse({
        'success': True,
        'message': 'Dashboard queries endpoint is working!'
    })
