from django.contrib import admin

from .models import (
    AcceptanceCriteria,
    Classroom,
    ClassroomInstructor,
    Flag,
    HelpfulResource,
    Project,
    Question,
    QuestionChoice,
    Regex,
    Task,
)

# Register your models here.
admin.site.register(Classroom)

admin.site.register(ClassroomInstructor)

admin.site.register(Project)

admin.site.register(Task)

admin.site.register(AcceptanceCriteria)

admin.site.register(Regex)

admin.site.register(Flag)

admin.site.register(Question)

admin.site.register(QuestionChoice)

admin.site.register(HelpfulResource)
