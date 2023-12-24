from django.shortcuts import render


def handler500(request):
    data = {}
    response = render(request, 'error_page/500.html', data)
    response.status_code = 500
    return response


def handler404(request, exception):
    response = render(request, 'error_page/404.html', context={'error': exception})
    response.status_code = 404
    return response
