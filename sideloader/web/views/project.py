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

from sideloader.web import forms, tasks, models
from sideloader.web.views import SideloaderView, SideloaderFormView


class StreamCreate(SideloaderFormView):
    template_name = 'stream/create_edit.html'
    form_class = forms.StreamForm

    project = None

    def renderData(self):
        return {
            'project': models.Project.objects.get(id=int(self.project))
        }

    def formSubmited(self, form):
        s = form.save(commit=False)
        s.project = self.project
        s.save()
        form.save_m2m()

        return self.redirect('projects_view', id=project)
    
    def setupForm(self, form):
        p = models.Project.objects.get(id=int(self.project))
        form.fields['targets'].queryset = p.target_set.all().order_by('description')
        form.fields['repo'].queryset = p.repo_set.all().order_by('github_url')

class StreamEdit(SideloaderFormView):
    template_name = 'stream/create_edit.html'
    form_class = forms.StreamForm

    id = None

    def getObject(self):
        print self.kwargs
        return models.Stream.objects.get(id=int(self.id))

    def renderData(self):
        stream = self.getObject()
        return {
            'stream': stream,
            'project': stream.project
        }

    def formSubmitted(self, form):
        stream = form.save(commit=False)
        stream.save()
        form.save_m2m()

        return self.redirect('projects_view', id=stream.repo.project.id)

    def setupForm(self, form):
        stream = self.getObject()
        form.fields['targets'].queryset = stream.project.target_set.all().order_by('description')

@login_required
def stream_delete(request, id):
    stream = models.Stream.objects.get(id=id)
    project = stream.project
    if (request.user.is_superuser) or (
        project in request.user.project_set.all()):
        stream.delete()

    return redirect('projects_view', id=project.id)

@login_required
def stream_push(request, flow, build):
    flow = models.ReleaseStream.objects.get(id=flow)
    project = flow.project
    build = models.Build.objects.get(id=build)

    if (request.user.is_superuser) or (
        project in request.user.project_set.all()):
        
        tasks.doRelease.delay(build, flow)

    return redirect('projects_view', id=project.id)

@login_required
def stream_schedule(request, flow, build):
    flow = models.ReleaseStream.objects.get(id=flow)
    build = models.Build.objects.get(id=build)

    if request.method == "POST":
        form = forms.ReleasePushForm(request.POST)
        if form.is_valid():
            release = form.cleaned_data

            schedule = release['scheduled'] + timedelta(hours=int(release['tz']))

            tasks.doRelease.delay(build, flow, scheduled=schedule)

            return redirect('projects_view', id=flow.project.id)
    else:
        form = forms.ReleasePushForm()

    return render(request, 'stream/schedule.html', {
        'projects': getProjects(request),
        'project': flow.project,
        'form': form,
        'flow': flow,
        'build': build
    })

@login_required
def target_create(request, project):
    project = models.Project.objects.get(id=project)

    if request.method == "POST":
        form = forms.TargetForm(request.POST)

        if form.is_valid():
            target = form.save(commit=False)
            target.project = project
            target.save()

            return redirect('projects_view', id=project.id)

    else:
        form = forms.TargetForm()
        #form.fields['server'].queryset = m.all().order_by('github_url')

    return render(request, 'target/create_edit.html', {
        'form': form, 
        'project': project,
        'projects': getProjects(request)
    })

@login_required
def target_edit(request, id):
    target = models.Target.objects.get(id=id)

    if request.method == "POST":
        form = forms.TargetForm(request.POST, instance=target)

        if form.is_valid():
            target = form.save(commit=False)
            target.save()

            return redirect('projects_view', id=target.project.id)

    else:
        form = forms.TargetForm(instance=target)

    return render(request, 'target/create_edit.html', {
        'form': form, 
        'target': target,
        'project': target.project,
        'projects': getProjects(request)
    })

@login_required
def target_delete(request, id):
    target = models.Target.objects.get(id=id)
    project = target.project
    if (request.user.is_superuser) or (
        project in request.user.project_set.all()):
        target.delete()

    return redirect('projects_view', id=project.id)


@login_required
def release_delete(request, id):
    release = models.Release.objects.get(id=id)
    project = release.flow.project
    if (request.user.is_superuser) or (
        project in request.user.project_set.all()):
        release.delete()

    return redirect('projects_view', id=project.id)


@login_required
def build_view(request, id):
    build = models.Build.objects.get(id=id)

    d = {
        'projects': getProjects(request),
        'project': build.project
    }

    if (request.user.is_superuser) or (
        build.project in request.user.project_set.all()):
        d['build'] = build

    return render(request, 'projects/build_view.html', d)

class ProjectView(SideloaderView):
    template_name = 'projects/view.html'
    id = None

    def renderData(self):
        project = models.Project.objects.get(id=int(self.id))

        if self.hasProjectPermission(project):
            repos = project.repo_set.all().order_by('github_url')

            builds = []
            streams = []
            releases = []

            for repo in repos:
                builds.extend(repo.build_set.all().order_by('-build_time'))
                streams.extend(repo.stream_set.all().order_by('name'))

            for stream in streams:
                releases.extend(stream.release_set.all().order_by(
                    '-release_date'))

            releases.sort(key=lambda r: r.release_date)

            builds.sort(key=lambda r: r.build_time)

            streams.sort(key=lambda r: r.name)

            requests = project.serverrequest_set.filter(approval=0).order_by('request_date')

            d = {
                'project': project,
                'repos': repos,
                'targets': project.target_set.all().order_by('description'),
                'builds': reversed(builds),
                'streams': streams,
                'releases': reversed(releases[-5:]),
                'requests': requests
            }
        else:
            d = {}

        return d

@login_required
def project_graph(request, id):
    # Server checkin endpoint
    project = models.Project.objects.get(id=id)

    data = {
        'project': project.name,
        'repos': [],
        'targets': [],
        'streams': []
    }

    for repo in project.repo_set.all():
        data['repos'].append({
            'name': repo.github_url,
            'id': 'R%s' % repo.id
        })

    for target in project.target_set.all():
        data['targets'].append({
            'name': target.description,
            'id': 'T%s' % target.id
        })

    for stream in project.stream_set.all():
        data['streams'].append({
            'id': 'S%s' % stream.id,
            'name': stream.name,
            'branch': stream.branch,
            'repo_link': 'R%s' % stream.repo.id,
            'target_link': ['T%s' % t.id for t in stream.targets.all()]
        })

    return HttpResponse(json.dumps(data), 
        content_type='application/json')

@login_required
def projects_delete(request, id):
    if not request.user.is_superuser:
        return redirect('home')

    models.Project.objects.get(id=id).delete()

    return redirect('home')

@login_required
def projects_create(request):
    if not request.user.is_superuser:
        return redirect('home')

    if request.method == "POST":
        form = forms.ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.save()

            return redirect('projects_view', id=project.id)

    else:
        form = forms.ProjectForm()

    return render(request, 'projects/create_edit.html', {
        'projects': getProjects(request),
        'form': form
    })

@login_required
def projects_edit(request, id):
    if not request.user.is_superuser:
        return redirect('home')

    project = models.Project.objects.get(id=id)
    if request.method == "POST":
        form = forms.ProjectForm(request.POST, instance=project)

        if form.is_valid():
            project = form.save(commit=False)
            project.save()
            form.save_m2m()

            return redirect('projects_view', id=id)

    else:
        form = forms.ProjectForm(instance=project)
    d = {
        'form': form, 
        'project': project,
        'projects': getProjects(request)
    }

    return render(request, 'projects/create_edit.html', d)

@login_required
def server_request(request, project):
    project = models.Project.objects.get(id=project)

    if request.method == "POST":
        form = forms.ServerRequestForm(request.POST)
        if form.is_valid():
            server = form.save(commit=False)
            server.requested_by = request.user
            server.project = project
            server.save()

            return redirect('projects_view', id=project.id)

    else:
        form = forms.ServerRequestForm()


    return render(request, 'projects/server_request.html', {
        'form': form,
        'project': project,
        'projects': getProjects(request),
    })

@login_required
def repo_edit(request, id):
    repo = models.Repo.objects.get(id=id)
    project = repo.project
    if request.method == "POST":
        form = forms.RepoForm(request.POST, instance=repo)

        if form.is_valid():
            repo = form.save(commit=False)
            repo.project = project
            repo.save()

            return redirect('projects_view', id=id)

    else:
        form = forms.RepoForm(instance=repo)
    d = {
        'projects': getProjects(request),
        'repo': repo,
        'form': form
    }

    return render(request, 'repo/create_edit.html', d)

@login_required
def repo_delete(request, id):
    repo = models.Repo.objects.get(id=id)
    projectid = repo.project.id
    repo.delete()

    return redirect('projects_view', id=projectid)

@login_required
def repo_create(request, project):
    project = models.Project.objects.get(id=project)

    if request.method == "POST":
        form = forms.RepoForm(request.POST)
        if form.is_valid():
            repo = form.save(commit=False)
            repo.created_by_user = request.user
            repo.idhash = uuid.uuid1().get_hex()
            repo.project = project
            repo.save()

            return redirect('projects_view', id=project.id)

    else:
        form = forms.RepoForm()

    return render(request, 'repo/create_edit.html', {
        'projects': getProjects(request),
        'project': project,
        'form': form
    })

@login_required
def help_index(request):
    return render(request, 'help/index.html')

@login_required
def build_cancel(request, id):
    build = models.Build.objects.get(id=id)
    if build.project in request.user.project_set.all():
        build.state = 3 
        build.save()

    return redirect('home')

@login_required
def projects_build(request, id):
    project = models.Project.objects.get(id=id)

    if project and (request.user.is_superuser or (
        project in request.user.project_set.all())):
        current_builds = models.Build.objects.filter(project=project, state=0)
        if current_builds:
            return redirect('build_view', id=current_builds[0].id)
        else:
            bcount = project.build_counter + 1

            build = models.Build.objects.create(project=project, state=0, build_num=bcount)

            task_id = tasks.build(build)

            build.task_id = task_id
            build.save()

            project.build_counter = bcount
            project.save()

            return redirect('build_view', id=build.id)

    return redirect('home')

@login_required
def build_output(request, id):
    build = models.Build.objects.get(id=id)

    if (request.user.is_superuser) or (
        build.project in request.user.project_set.all()):
        d = {'state': build.state, 'log': build.log}
    else:
        d = {}

    return HttpResponse(json.dumps(d), content_type='application/json')

@login_required
def get_servers(request):
    d = [s.name for s in models.Server.objects.all()]

    return HttpResponse(json.dumps(d), content_type='application/json')

@login_required
def get_stream_servers(request, id):
    stream = models.ReleaseStream.objects.get(id=id)

    d = [s.server.name for s in stream.target_set.all()]

    return HttpResponse(json.dumps(d), content_type='application/json')

#############
# API methods

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

