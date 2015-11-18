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

from sideloader.web import forms, tasks, models
from sideloader.web.views import (SideloaderView, SideloaderFormView,
    SideloaderDeleteView, SideloaderRedirectView, SideloaderJSONView)


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

class StreamDelete(SideloaderDeleteView):
    model = models.Stream
        
class StreamPush(SideloaderRedirectView):
    flow = None
    build = None

    def redirect(self):
        flow = models.ReleaseStream.objects.get(id=self.flow)
        project = flow.project
        if self.hasProjectPermission(project):
            tasks.pushRelease(self.build, flow)
            
        return redirect('projects_view', id=project.id)

class StreamSchedule(SideloaderFormView):
    flow = None
    build = None

    template_name = 'stream/schedule.html'
    form_class = forms.ReleasePushForm

    def renderData(self):
        flow = models.ReleaseStream.objects.get(id=self.flow)
        build = models.Build.objects.get(id=self.build)
        return {
            'project': flow.project,
            'flow': flow,
            'build': build,
        }

    def formSubmitted(self, form):
        flow = models.ReleaseStream.objects.get(id=self.flow)
        release = form.cleaned_data

        schedule = release['scheduled'] + timedelta(hours=int(release['tz']))

        tasks.pushRelease(self.build, flow, scheduled=schedule)
        
        return redirect('projects_view', id=flow.project.id)

class DeployCreate(SideloaderFormView):
    project = None
    template_name = 'target/create_edit.html'
    form_class = forms.TargetForm

    def renderData(self):
        project = models.Project.objects.get(id=project)
        return {'project': project}

    def formSubmitted(self, form):
        target = form.save(commit=False)
        target.project = project
        target.save()

        return self.redirect('projects_view', id=project.id)

class DeployEdit(SideloaderFormView):
    template_name = 'target/create_edit.html'
    form_class = forms.StreamForm

    id = None

    def getObject(self):
        return self.getObjectIfAllowed(models.Target, id=int(self.id))

    def renderData(self):
        target = self.getObject()
        return {
            'target': target,
            'project': stream.project
        }

    def formSubmitted(self, form):
        target = form.save(commit=False)
        target.save()

        return self.redirect('projects_view', id=target.project.id)

class DeployDelete(SideloaderDeleteView):
    model = models.Target

class ReleaseDelete(SideloaderDeleteView):
    model = models.Release

class BuildView(SideloaderView):
    template_name =  'projects/build_view.html'
    id = None

    def renderData(self):
        build = self.getObjectIfAllowed(models.Build, id=int(self.id))

        return {
            'build': build,
            'project': build.project
        }
            

class ProjectView(SideloaderView):
    template_name = 'projects/view.html'
    id = None

    def renderData(self):
        project = self.getProject(self.id)

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

        return {
            'project': project,
            'repos': repos,
            'targets': project.target_set.all().order_by('description'),
            'builds': reversed(builds),
            'streams': streams,
            'releases': reversed(releases[-5:]),
            'requests': requests
        }

class ProjectGraph(SideloaderJSONView):
    id = None

    def getData(self):
        project = self.getProject(self.id)

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

        return data


class ProjectDelete(SideloaderDeleteView):
    mode = models.Project

    def redirect(self, obj):
        return reverse('home')


class ProjectCreate(SideloaderFormView):
    template_name = 'projects/create_edit.html'
    form_class = forms.ProjectForm

    def formSubmitted(self, form):
        project = form.save(commit=False)
        project.save()
        form.save_m2m()

        return redirect('projects_view', id=project.id)

class ProjectEdit(SideloaderFormView):
    template_name = 'projects/create_edit.html'
    form_class = forms.ProjectForm

    def getObject(self):
        return self.getProject(kwargs['id'])

    def formSubmitted(self, form):
        project = form.save(commit=False)
        project.save()
        form.save_m2m()

        return redirect('projects_view', id=project.id)

    def renderData(self):
        project = self.getObject()
        return {
            'project': project
        }

class ServerRequest(SideloaderFormView):
    form_class = forms.ServerRequestForm
    template_name = 'projects/server_request.html'

    id = None

    def formSubmitted(self, form):
        project = self.getProject(self.id)

        server = form.save(commit=False)
        server.requested_by = self.request.user
        server.project = project
        server.save()

        return redirect('projects_view', id=project.id)

    def renderData(self):
        project = self.getProject(self.id)

        return {'project': project}

class RepoEdit(SideloaderFormView):
    form_class = forms.RepoForm
    template_name = 'repo/create_edit.html'

    def getObject(self):
        return self.getObjectIfAllowed(models.Repo, id=int(self.id))

    def formSubmitted(self, form):
        repo = form.save(commit=False)
        repo.save()

        return redirect('projects_view', id=id)

    def renderData(self):
        repo = self.getObject()

        return {
            'repo': repo,
            'project': repo.project
        }

class RepoDelete(SideloaderDeleteView):
    model = models.Repo

class RepoCreate(SideloaderFormView):
    form_class = forms.RepoForm
    template_name = 'repo/create_edit.html'

    project = None

    def formSubmitted(self, form):
        project = models.Project.objects.get(id=int(self.project))

        repo = form.save(commit=False)
        repo.created_by_user = request.user
        repo.idhash = uuid.uuid1().get_hex()
        repo.project = project
        repo.save()

        return redirect('projects_view', id=project.id)

    def renderData(self):
        project = models.Project.objects.get(id=int(self.project))

        return {'project': project}

class Help(SideloaderView):
    template_name = 'help/index.html'

class BuildCancel(SideloaderRedirectView):
    id = None
    def redirect(self):
        build = self.getObjectIfAllowed(models.Build, id=self.id)
        build.state = 3 
        build.save()

        return reverse('home')

class ProjectBuild(SideloaderRedirectView):
    id = None

    def redirect(self):
        project = self.getProject(self.id)

        current_builds = models.Build.objects.filter(project=project, state=0)
        if current_builds:
            return redirect('build_view', id=current_builds[0].id)
        else:
            build = models.Build.objects.create(project=project, state=0, build_num=bcount)

            task_id = tasks.build(build)

            build.task_id = task_id
            build.save()

            project.build_counter = bcount
            project.save()

            return reverse('build_view', id=build.id)

        return reverse('home')

class BuildOutput(SideloaderJSONView):
    id = None
    def getData(self):
        build = self.getObjectIfAllowed(models.Build, id=self.id)
        return {'state': build.state, 'log': build.log}

class ServerList(SideloaderJSONView):
    def getData(self):
        return [s.name for s in models.Server.objects.all()]

class StreamServers(SideloaderJSONView):
    id = None
    def getData(self):
        stream = self.getObjectIfAllowed(models.ReleaseStream, id=self.id)

        return [s.server.name for s in stream.target_set.all()]

