import secrets

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse


def locked_out(request):
    return render(request, 'users/locked_out.html', status=403)


@login_required
@require_POST
def generate_shortcut_token(request):
    token = secrets.token_urlsafe(40)
    request.user.shortcut_token = token
    request.user.save(update_fields=['shortcut_token'])
    return JsonResponse({'token': token})


@login_required
@require_POST
def revoke_shortcut_token(request):
    request.user.shortcut_token = None
    request.user.save(update_fields=['shortcut_token'])
    return JsonResponse({'ok': True})
