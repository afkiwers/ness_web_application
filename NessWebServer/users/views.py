from django.shortcuts import render


def locked_out(request):
    return render(request, 'users/locked_out.html', status=403)
