from django.contrib import admin
from .models import Competitors, Discipline, Meet, RoundsOfDiscipline, Results, FormatType

class RoundsOfDisciplineInstanceInline(admin.TabularInline):
    model = RoundsOfDiscipline

class MeetAdmin(admin.ModelAdmin):
    filter_horizontal = ('competitors',)
    list_display = ('name', 'date')
    inlines = [RoundsOfDisciplineInstanceInline]

# Register your models here.
admin.site.register(Discipline)
admin.site.register(Meet, MeetAdmin)
admin.site.register(Competitors)
admin.site.register(RoundsOfDiscipline)
admin.site.register(Results)
admin.site.register(FormatType)
