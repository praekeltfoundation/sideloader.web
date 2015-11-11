from django.conf.urls import patterns, include, url

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Index
    url(r'^$', 'sideloader.web.views.index', name='home'),

    # Projects
    url(r'^projects/create$', 'sideloader.web.views.projects_create', name='projects_create'),
    url(r'^projects/edit/(?P<id>[\d]+)$', 'sideloader.web.views.projects_edit', name='projects_edit'),
    url(r'^projects/view/(?P<id>[\d]+)$', 'sideloader.web.views.projects_view', name='projects_view'),
    url(r'^projects/build/(?P<id>[\d]+)$', 'sideloader.web.views.projects_build', name='projects_build'),
    url(r'^projects/delete/(?P<id>[\d]+)$', 'sideloader.web.views.projects_delete', name='projects_delete'),
    url(r'^projects/server/request/(?P<project>[\d]+)$', 'sideloader.web.views.server_request', name='server_request'),

    url(r'^projects/build/view/(?P<id>[\d]+)$', 'sideloader.web.views.build_view', name='build_view'),
    url(r'^projects/build/log/(?P<id>[\d]+)$', 'sideloader.web.views.build_output', name='build_output'),
    url(r'^projects/build/cancel/(?P<id>[\d]+)$', 'sideloader.web.views.build_cancel', name='build_cancel'),
    url(r'^projects/graph/(?P<id>[\d]+)$', 'sideloader.web.views.project_graph', name='project_graph'),

    # Repos
    url(r'^repo/create/(?P<project>[\d]+)$', 'sideloader.web.views.repo_create', name='repo_create'),
    url(r'^repo/edit/(?P<id>[\d]+)$', 'sideloader.web.views.repo_edit', name='repo_edit'),
    url(r'^repo/delete/(?P<id>[\d]+)$', 'sideloader.web.views.repo_delete', name='repo_delete'),


    # Streams
    url(r'^stream/edit/(?P<id>[\d]+)$', 'sideloader.web.views.stream_edit', name='stream_edit'),
    url(r'^stream/delete/(?P<id>[\d]+)$', 'sideloader.web.views.stream_delete', name='stream_delete'),
    url(r'^stream/suck/(?P<id>[\d]+)$', 'sideloader.web.views.release_delete', name='release_delete'),
    url(r'^stream/create/(?P<project>[\d]+)$', 'sideloader.web.views.stream_create', name='stream_create'),
    url(r'^stream/push/(?P<flow>[\d]+)/(?P<build>[\d]+)$', 'sideloader.web.views.stream_push', name='stream_push'),
    url(r'^stream/schedule/(?P<flow>[\d]+)/(?P<build>[\w-]+)$', 'sideloader.web.views.stream_schedule', name='stream_schedule'),

    #url(r'^stream/manifests/(?P<id>[\d]+)$', 'sideloader.web.views.manifest_view', name='manifest_view'),
    #url(r'^stream/manifests/add/(?P<id>[\d]+)$', 'sideloader.web.views.manifest_add', name='manifest_add'),
    #url(r'^stream/manifests/edit/(?P<id>[\d]+)$', 'sideloader.web.views.manifest_edit', name='manifest_edit'),
    #url(r'^stream/manifests/delete/(?P<id>[\d]+)$', 'sideloader.web.views.manifest_delete', name='manifest_delete'),

    # Targets
    url(r'^deploy/create/(?P<project>[\d]+)$', 'sideloader.web.views.target_create', name='target_create'),
    url(r'^deploy/edit/(?P<id>[\d]+)$', 'sideloader.web.views.target_delete', name='target_delete'),
    url(r'^deploy/delete/(?P<id>[\d]+)$', 'sideloader.web.views.target_edit', name='target_edit'),

    # Modules
    url(r'^modules/edit/(?P<id>[\w]+)$', 'sideloader.web.views.module_edit', name='module_edit'),
    url(r'^modules/create$', 'sideloader.web.views.module_create', name='module_create'),
    url(r'^modules/get_scheme/(?P<id>[\w]+)$', 'sideloader.web.views.module_scheme', name='module_scheme'),
    url(r'^modules/$', 'sideloader.web.views.module_index', name='module_index'),

    # Releases
    url(r'^releases/edit/(?P<id>[\d]+)$', 'sideloader.web.views.release_edit', name='edit_release'),
    url(r'^releases/create$', 'sideloader.web.views.release_create', name='create_release'),
    url(r'^releases/$', 'sideloader.web.views.release_index', name='release_index'),

    # Servers
    url(r'^servers/$', 'sideloader.web.views.server_index', name='server_index'),
    url(r'^servers/log/(?P<id>[\d]+)$', 'sideloader.web.views.server_log', name='server_log'),
    url(r'^servers/json/$', 'sideloader.web.views.get_servers', name='get_servers'),
    url(r'^servers/json/stream/(?P<id>[\d]+)$', 'sideloader.web.views.get_stream_servers', name='get_stream_servers'),

    # Help
    url(r'^help/$', 'sideloader.web.views.help_index', name='help_index'),

    # Admin
    url(r'^manage/$', 'sideloader.web.views.manage_index', name='manage_index'),
    url(r'^manage/repo/create$', 'sideloader.web.views.manage_create_repo', name='manage_create_repo'),
    url(r'^manage/repo/delete/(?P<id>[\d+])$', 'sideloader.web.views.manage_delete_repo', name='manage_delete_repo'),

    # API
    url(r'^api/build/(?P<hash>[\w]+)$', 'sideloader.web.views.api_build', name='api_build'),
    url(r'^api/rap/(?P<hash>[\w]+)$', 'sideloader.web.views.api_sign', name='api_sign'),
    url(r'^api/checkin$', 'sideloader.web.views.api_checkin', name='api_checkin'),
    url(r'^api/enc/(?P<server>[\w.-]+)$', 'sideloader.web.views.api_enc', name='api_enc'),

    # Authentication
    url(r'^accounts/login/$', 'django.contrib.auth.views.login', {'template_name': 'login.html'}),
    url(r'^accounts/logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='auth_logout'),
    url(r'^accounts/profile/$', 'sideloader.web.views.accounts_profile', name='accounts_profile'),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
)
