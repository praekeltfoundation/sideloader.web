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
from django.views.generic.edit import FormView

from sideloader.web import forms, tasks, models


class PageMixin(object):
    @classmethod
    def as_view(cls, **initkwargs):
        view = super(PageMixin, cls).as_view(**initkwargs)
        return login_required(view)

    def hasProjectPermission(self, project):
        return (self.request.user.is_superuser) or (
            project in self.request.user.project_set.all())

    def updateArgs(self):
        for k, v in self.kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)

    def getProjects(self):
        if self.request.user.is_superuser:
            return models.Project.objects.all().order_by('name')
        else:
            return self.request.user.project_set.all().order_by('name')

    def renderData(self):
        pass

    def redirect(self, *a, **kw):
        return redirect(*a, **kw)

class SideloaderView(PageMixin, TemplateView):
    def get_context_data(self, **kwargs):
        context = super(SideloaderView, self).get_context_data(**kwargs)

        self.updateArgs()

        # Merge context data
        self.projects = self.getProjects()
        context['projects'] = self.projects

        data = self.renderData()

        for k, v in data.items():
            context[k] = v

        return context

class SideloaderFormView(PageMixin, FormView):
    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        return self.formSubmited(form)

    def formSubmitted(self, form):
        pass

    def get_context_data(self, **kwargs):
        self.updateArgs()
        context = super(SideloaderFormView, self).get_context_data(**kwargs)

        # Merge context data
        self.projects = self.getProjects()
        context['projects'] = self.projects
        context['form'] = self.get_form()

        self.setupForm(context['form'])

        data = self.renderData()

        for k, v in data.items():
            context[k] = v

        return context

    def get_form_kwargs(self):
        kwargs = super(SideloaderFormView, self).get_form_kwargs()
        self.updateArgs()
        if hasattr(self, 'getObject'):
            kwargs.update({'instance': self.getObject()})
        return kwargs

    def setupForm(self, form):
        pass

class APIMixin(object):
    def verifyHMAC(request, data=None):
        clientauth = request.META['HTTP_AUTHORIZATION']
        sig = request.META['HTTP_SIG']

        if clientauth != settings.SPECTER_AUTHCODE:
            return False

        sign = [settings.SPECTER_AUTHCODE, request.method, request.path]

        if data:
            sign.append(
                hashlib.sha1(data).hexdigest()
            )

        mysig = hmac.new(
            key = settings.SPECTER_SECRET,
            msg = '\n'.join(sign),
            digestmod = hashlib.sha1
        ).digest()

        return base64.b64encode(mysig) == sig

