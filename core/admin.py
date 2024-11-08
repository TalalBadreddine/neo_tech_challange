from django.contrib import admin
from django.urls import path
from django.template.response import TemplateResponse
from django.db import connection
from core.models.etl_job import ETLJob
from core.models.view import MaterializedViewRefresh
from core.models.transaction_statistics_view import TransactionStatistics

@admin.register(ETLJob)
class ETLJobAdmin(admin.ModelAdmin):
    change_list_template = 'admin/core/etljob/change_list.html'

    list_display = ['job_name', 'status', 'started_at', 'completed_at', 'records_processed']
    list_filter = ['status', 'job_name']
    search_fields = ['job_name']
    readonly_fields = ['started_at', 'completed_at']

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('etl-dashboard/',
                 self.admin_site.admin_view(self.etl_dashboard_view),
                 name='core_etljob_dashboard'),
        ]
        return my_urls + urls

    def etl_dashboard_view(self, request):
        context = {
            **self.admin_site.each_context(request),
            'title': 'ETL Dashboard',
            'opts': self.model._meta,
            'recent_jobs': ETLJob.objects.all()[:10],
            'failed_jobs': ETLJob.objects.filter(status='failed')[:5],
            'has_permission': True,
        }
        return TemplateResponse(request, 'admin/etl_dashboard.html', context)

@admin.register(MaterializedViewRefresh)
class MaterializedViewRefreshAdmin(admin.ModelAdmin):
    list_display = ['view_name', 'started_at', 'completed_at', 'success', 'duration_seconds']
    list_filter = ['view_name', 'success']
    search_fields = ['view_name']

@admin.register(TransactionStatistics)
class TransactionStatisticsAdmin(admin.ModelAdmin):
    list_display = [
        'client_id',
        'total_transactions',
        'total_spent',
        'total_gained'
    ]
    list_filter = ['client_id']
    search_fields = ['client_id']

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False