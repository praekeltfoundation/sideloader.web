from datetime import timedelta, datetime
import uuid
import urlparse
import json
import hashlib, hmac, base64
import time
import yaml

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.csrf import csrf_exempt
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.conf import settings

from django.views.generic.base import TemplateView

from sideloader.web import forms, tasks, models


@login_required
def accounts_profile(request):
    if request.method == "POST":
        form = forms.UserForm(request.POST, instance=request.user)

        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('home')
    else:
        form = forms.UserForm(instance=request.user)

    return render(request, "accounts_profile.html", {
        'form': form,
        'projects': getProjects(request)
    })

@login_required
def manage_index(request):
    if not request.user.is_superuser:
        return redirect('home')

    users = User.objects.all().order_by('username')
    repos = models.PackageRepo.objects.all().order_by('name')

    hives = []
    for k, v in tasks.getClusterStatus().items():
        v['hostname'] = k
        hives.append({
            'hostname': k,
            'lastseen': time.ctime(v['lastseen']),
            'status': v['status']
        })

    return render(request, "manage/index.html", {
        'projects': getProjects(request),
        'users': users,
        'repos': repos,
        'hives': hives
    })

@login_required
def manage_create_repo(request):
    if not request.user.is_superuser:
        return redirect('home')

    if request.method == "POST":
        form = forms.PackageRepoForm(request.POST)
        if form.is_valid():
            release = form.save(commit=False)
            release.save()

            return redirect('manage_index')
    else:
        form = forms.PackageRepoForm()

    return render(request, "manage/create_repo.html", {
        'form': form,
        'projects': getProjects(request),
    })

@login_required
def manage_delete_repo(request, id):
    repo = models.PackageRepo.objects.get(id=id)
    repo.delete()

    return redirect('manage_index')

            
