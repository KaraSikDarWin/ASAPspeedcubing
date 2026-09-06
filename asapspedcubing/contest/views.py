from django.shortcuts import render, redirect, get_object_or_404
from meet.models import Meet, Results, RoundsOfDiscipline, format_time
from .forms import ResultsContestForm
from .models import ResultsContest
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import UpdateView, DeleteView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.urls import reverse_lazy


def submit_result(request, pk):
    meet = get_object_or_404(Meet, pk=pk, format_type__format_name='Контест')
    form = ResultsContestForm(meet_pk=pk)

    if request.method == 'POST':
        form_results = ResultsContestForm(request.POST, meet_pk=pk)
        if form_results.is_valid():
            competitor = form_results.cleaned_data['competitor']
            discipline = form_results.cleaned_data['discipline']
            round_number = form_results.cleaned_data['round_number']
            attempt_1 = form_results.cleaned_data['attempt_1']
            attempt_2 = form_results.cleaned_data['attempt_2']
            attempt_3 = form_results.cleaned_data['attempt_3']
            attempt_4 = form_results.cleaned_data['attempt_4']
            attempt_5 = form_results.cleaned_data['attempt_5']
        
                        # Проверяем, нет ли уже такой записи (уникальность)
            if ResultsContest.objects.filter(
                competitor=competitor,
                meet=meet,
                discipline=discipline,
                round_number=round_number
                                    ).exists():
                messages.warning(request, 'Запись для этого участника, дисциплины и раунда уже существует.')
            else:
                ResultsContest.objects.create(
                                competitor=competitor,
                                meet=meet,
                                discipline=discipline,
                                round_number=round_number,
                                attempt_1=attempt_1,
                                attempt_2=attempt_2,
                                attempt_3=attempt_3,
                                attempt_4=attempt_4,
                                attempt_5=attempt_5,
                                is_published = False
                            )
                messages.success(
                                request, 'Результат успешно сохранён')
                return redirect('meet:meet_detail', pk=meet.pk)
        else:
            print("Ошибки отправки:", form_results.errors)
        
    context = {
        'meet': meet,
        'form_results': form,
    }
    return render(request, "contest/submit_result.html", context)

class ResultContestUpdateView(UpdateView):
    permisson_classes = [IsAuthenticated]
    model = ResultsContest
    template_name = 'contest/contest_actions.html'
    fields = ['competitor', 'discipline', 'round_number', 'attempt_1', 'attempt_2', 'attempt_3', 'attempt_4', 'attempt_5']

    def get_success_url(self):
        result = self.object
        return reverse_lazy('meet:meet_detail', kwargs={'pk': result.meet.pk})

class ResultContestDeleteView(DeleteView):
    permisson_classes = [IsAuthenticated]
    model = ResultsContest
    template_name = 'contest/contest_submit_delete.html'

    def get_success_url(self):
            result = self.object
            return reverse_lazy('meet:meet_detail', kwargs={'pk': result.meet.pk})

    
