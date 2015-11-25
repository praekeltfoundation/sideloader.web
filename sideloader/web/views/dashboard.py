from sideloader.web.views import SideloaderView
from sideloader.db import models


class DashboardView(SideloaderView):
    template_name = "index.html"

    def renderData(self):
        if self.request.user.is_superuser:
            builds = models.Build.objects.filter(state=0).order_by('-build_time')
            last_builds = models.Build.objects.filter(state__gt=0).order_by('-build_time')[:10]

            requests = models.ServerRequest.objects.filter(provisioned=False).order_by('request_date')
        else:
            all_builds = models.Build.objects.filter(state=0).order_by('-build_time')
            last_builds = models.Build.objects.filter(state__gt=0, project__in=self.projects).order_by('-build_time')[:10]

            requests = []

            builds = []
            for build in all_builds:
                if build.project in self.projects:
                    builds.append(build)
                else:
                    builds.append({'build_time': build.build_time, 'project': {'name': 'Private'}})

        return {
            'builds': builds,
            'last_builds': last_builds,
            'requests': requests,
        }

