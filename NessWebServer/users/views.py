import secrets

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.http import JsonResponse


def locked_out(request):
    return render(request, 'users/locked_out.html', status=403)


@login_required
def backup_codes(request):
    from django_otp.plugins.otp_static.models import StaticDevice
    device, _ = StaticDevice.objects.get_or_create(user=request.user, name='backup')
    codes = list(device.token_set.values_list('token', flat=True))
    return JsonResponse({'codes': codes, 'count': len(codes)})


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
    request.user.shortcut_token = ''
    request.user.save(update_fields=['shortcut_token'])
    return JsonResponse({'ok': True})


@login_required
@require_POST
def generate_backup_codes(request):
    from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
    device, _ = StaticDevice.objects.get_or_create(user=request.user, name='backup')
    device.token_set.all().delete()
    codes = [StaticToken.random_token() for _ in range(10)]
    device.token_set.bulk_create([StaticToken(device=device, token=t) for t in codes])
    return JsonResponse({'codes': codes, 'count': len(codes)})
