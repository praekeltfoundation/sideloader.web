from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
#from django.contrib import admin

from sideloader.web.views import dashboard, project

#admin.autodiscover()

urlpatterns = patterns('',
    # Index
    url(r'^$', dashboard.DashboardView.as_view(), name='home'),

    # Projects
    url(r'^projects/create$', 'sideloader.web.views.project.projects_create', name='projects_create'),
    url(r'^projects/edit/(?P<id>[\d]+)$', 'sideloader.web.views.project.projects_edit', name='projects_edit'),
    url(r'^projects/view/(?P<id>[\d]+)$', project.ProjectView.as_view(), name='projects_view'),
    url(r'^projects/build/(?P<id>[\d]+)$', 'sideloader.web.views.project.projects_build', name='projects_build'),
    url(r'^projects/delete/(?P<id>[\d]+)$', 'sideloader.web.views.project.projects_delete', name='projects_delete'),
    url(r'^projects/server/request/(?P<project>[\d]+)$', 'sideloader.web.views.project.server_request', name='server_request'),

    url(r'^projects/build/view/(?P<id>[\d]+)$', 'sideloader.web.views.project.build_view', name='build_view'),
    url(r'^projects/build/log/(?P<id>[\d]+)$', 'sideloader.web.views.project.build_output', name='build_output'),
    url(r'^projects/build/cancel/(?P<id>[\d]+)$', 'sideloader.web.views.project.build_cancel', name='build_cancel'),
    url(r'^projects/graph/(?P<id>[\d]+)$', 'sideloader.web.views.project.project_graph', name='project_graph'),

    # Repos
    url(r'^repo/create/(?P<project>[\d]+)$', 'sideloader.web.views.project.repo_create', name='repo_create'),
    url(r'^repo/edit/(?P<id>[\d]+)$', 'sideloader.web.views.project.repo_edit', name='repo_edit'),
    url(r'^repo/delete/(?P<id>[\d]+)$', 'sideloader.web.views.project.repo_delete', name='repo_delete'),


    # Streams
    url(r'^stream/create/(?P<project>[\d]+)$', project.StreamCreate.as_view(), name='stream_create'),
    url(r'^stream/edit/(?P<id>[\d]+)$', project.StreamEdit.as_view(), name='stream_edit'),
    url(r'^stream/delete/(?P<id>[\d]+)$', 'sideloader.web.views.project.stream_delete', name='stream_delete'),
    url(r'^stream/suck/(?P<id>[\d]+)$', 'sideloader.web.views.project.release_delete', name='release_delete'),
    url(r'^stream/push/(?P<flow>[\d]+)/(?P<build>[\d]+)$', 'sideloader.web.views.project.stream_push', name='stream_push'),
    url(r'^stream/schedule/(?P<flow>[\d]+)/(?P<build>[\w-]+)$', 'sideloader.web.views.project.stream_schedule', name='stream_schedule'),

    #url(r'^stream/manifests/(?P<id>[\d]+)$', 'sideloader.web.views.project.manifest_view', name='manifest_view'),
    #url(r'^stream/manifests/add/(?P<id>[\d]+)$', 'sideloader.web.views.project.manifest_add', name='manifest_add'),
    #url(r'^stream/manifests/edit/(?P<id>[\d]+)$', 'sideloader.web.views.project.manifest_edit', name='manifest_edit'),
    #url(r'^stream/manifests/delete/(?P<id>[\d]+)$', 'sideloader.web.views.project.manifest_delete', name='manifest_delete'),

    # Targets
    url(r'^deploy/create/(?P<project>[\d]+)$', 'sideloader.web.views.project.target_create', name='target_create'),
    url(r'^deploy/edit/(?P<id>[\d]+)$', 'sideloader.web.views.project.target_delete', name='target_delete'),
    url(r'^deploy/delete/(?P<id>[\d]+)$', 'sideloader.web.views.project.target_edit', name='target_edit'),

    # Releases
    #url(r'^releases/edit/(?P<id>[\d]+)$', 'sideloader.web.views.project.release_edit', name='edit_release'),
    #url(r'^releases/create$', 'sideloader.web.views.project.release_create', name='create_release'),
    #url(r'^releases/$', 'sideloader.web.views.project.release_index', name='release_index'),

    # Servers
    #url(r'^servers/$', 'sideloader.web.views.project.server_index', name='server_index'),
    #url(r'^servers/log/(?P<id>[\d]+)$', 'sideloader.web.views.project.server_log', name='server_log'),
    #url(r'^servers/json/$', 'sideloader.web.views.project.get_servers', name='get_servers'),
    #url(r'^servers/json/stream/(?P<id>[\d]+)$', 'sideloader.web.views.project.get_stream_servers', name='get_stream_servers'),

    # Help
    url(r'^help/$', 'sideloader.web.views.project.help_index', name='help_index'),

    # Admin
    url(r'^manage/$', 'sideloader.web.views.admin.manage_index', name='manage_index'),
    url(r'^manage/repo/create$', 'sideloader.web.views.admin.manage_create_repo', name='manage_create_repo'),
    url(r'^manage/repo/delete/(?P<id>[\d+])$', 'sideloader.web.views.admin.manage_delete_repo', name='manage_delete_repo'),

    # API
    url(r'^api/build/(?P<hash>[\w]+)$', 'sideloader.web.views.project.api_build', name='api_build'),
    url(r'^api/rap/(?P<hash>[\w]+)$', 'sideloader.web.views.project.api_sign', name='api_sign'),
    url(r'^api/checkin$', 'sideloader.web.views.project.api_checkin', name='api_checkin'),
    url(r'^api/enc/(?P<server>[\w.-]+)$', 'sideloader.web.views.project.api_enc', name='api_enc'),

    # Authentication
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='auth_logout'),
    url(r'^accounts/profile/$', 'sideloader.web.views.admin.accounts_profile', name='accounts_profile'),

    # Uncomment the next line to enable the admin:
    #url(r'^admin/', include(admin.site.urls)),
)
