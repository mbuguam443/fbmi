from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView
from .models import BibleStudyNote


class BibleStudyListView(LoginRequiredMixin, ListView):
    model = BibleStudyNote
    template_name = 'bible_study/study_list.html'
    context_object_name = 'studies'
    paginate_by = 15

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class BibleStudyDetailView(LoginRequiredMixin, DetailView):
    model = BibleStudyNote
    template_name = 'bible_study/study_detail.html'
    context_object_name = 'study'

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)
