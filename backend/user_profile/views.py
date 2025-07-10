from django.http import JsonResponse

# Create your views here.

def user_profile(request):
    """API to fetch user profile details"""
    return JsonResponse({
        'success': True,
        'message': 'User profile endpoint is working!'
    })
