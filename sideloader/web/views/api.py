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
from django.http import HttpResponse, Http404

from django.conf import settings

from sideloader.web import forms, tasks
from sideloader.db import models

@csrf_exempt
def api_build(request, hash):
    project = models.Project.objects.get(idhash=hash)
    if project:
        if request.method == 'POST':
            if request.POST.get('payload'):
                r = json.loads(request.POST['payload'])
            else:
                r = json.loads(request.body)
            ref = r.get('ref', '')
            branch = ref.split('/',2)[-1]
            if branch != project.branch:
                return HttpResponse('{"result": "Request ignored"}',
                        content_type='application/json')

        current_builds = models.Build.objects.filter(project=project, state=0)
        if not current_builds:
            build = models.Build.objects.create(project=project, state=0)
            task = tasks.build(build)
            build.task_id = task.task_id
            build.save()

            return HttpResponse('{"result": "Building"}',
                    content_type='application/json')
        return HttpResponse('{"result": "Already building"}',
                content_type='application/json')

    return redirect('home')

@csrf_exempt
def api_sign(request, hash):
    signoff = models.ReleaseSignoff.objects.get(idhash=hash)
    signoff.signed = True
    signoff.save()

    if signoff.release.waiting:
        if signoff.release.check_signoff():
            tasks.runRelease.delay(signoff.release)

    return render(request, "sign.html", {
        'signoff': signoff
    })

@csrf_exempt
def api_checkin(request):
    # Server checkin endpoint
    if request.method == 'POST':
        if verifyHMAC(request, request.body):
            data = json.loads(request.body)
            try:
                server = models.Server.objects.get(name=data['hostname'])

            except models.Server.DoesNotExist:
                server = models.Server.objects.create(name=data['hostname'])

            server.last_checkin = datetime.now()

            server.save()

            return HttpResponse(json.dumps({}), 
                content_type='application/json')

    return HttpResponse(
            json.dumps({"error": "Not authorized"}), 
            content_type='application/json'
        )

@csrf_exempt
def api_enc(request, server):
    # Puppet ENC
    if verifyHMAC(request):
        # Build our ENC dict
        try:
            server = models.Server.objects.get(name=server)
        except:
            server = None

        if server:
            releases = [target.release for target in server.target_set.all()]
            server.last_checkin = datetime.now()
            server.last_puppet_run = datetime.now()
            server.change = False
            server.status = "Success"

            cdict = {}
            for release in releases:
                for manifest in release.servermanifest_set.all():
                    key = manifest.module.key
                    try:
                        value = json.loads(manifest.value)
                    except Exception, e:
                        server.status = "Validation error in manifest "
                        server.status += "%s -> %s -> %s: %s" % (
                            release.project.name,
                            release.name,
                            manifest.module.name,
                            e
                        )
                        continue 

                    if isinstance(value, list):
                        if key in cdict:
                            cdict[key].extend(value)
                        else:
                            cdict[key] = value

                    if isinstance(value, dict):
                        for k, v in value.items():
                            if key in cdict:
                                cdict[key][k] = v
                            else:
                                cdict[key] = {k: v}

            server.save()

            node = {
                'parameters': cdict
            }
        else:
            node = {}

        return HttpResponse(yaml.safe_dump(node),
            content_type='application/yaml')

    return HttpResponse(
            json.dumps({"error": "Not authorized"}), 
            content_type='application/json'
        )

