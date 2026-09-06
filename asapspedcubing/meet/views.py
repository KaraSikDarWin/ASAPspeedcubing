from django.shortcuts import render, redirect, get_object_or_404
from .models import Meet, Discipline, RoundsOfDiscipline, Results, Competitors, MeetFile
from contest.models import ResultsContest
from .forms import MeetForm, DisciplineForm, RoundsOfDisciplineFormSet, ExcludeCompetitors, ResultsForm, IncludeCompetitors, MeetFileForm, MeetFileFormSet
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .serializers import ResultsSerializer
from django.http import HttpResponse 
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.paginator import Paginator
from django.views.generic import CreateView, ListView, UpdateView, DeleteView
from django.urls import reverse_lazy
from contest.forms import ResultsContestForm

def format_time(value):
    """
    Преобразует целое число в строку времени по правилам количества цифр.
    Правила:
    - 2 цифры: 0.XX (пример: 69 -> 0.69)
    - 3 цифры: S.XX (пример: 890 -> 8.90)
    - 4 цифры: SS.XX (пример: 1000 -> 10.00)
    - 5 цифр: M:SS.XX (пример: 12345 -> 1:23.45)
    - 6 цифр: MM:SS.XX (пример: 195678 -> 19:56.78)
    - None -> "DNF"
    """
    if value is None:
        return "DNF"
    try:
        s = str(int(value)).strip()
    except (ValueError, TypeError):
        return "DNF"
    if not s:
        return "DNF"
    length = len(s)
    if length == 2:
        return f"0.{s}"
    elif length == 3:
        return f"{s[0]}.{s[1:]}"
    elif length == 4:
        return f"{s[:2]}.{s[2:]}"
    elif length == 5:
        return f"{s[0]}:{s[1:3]}.{s[3:]}"
    elif length == 6:
        return f"{s[:2]}:{s[2:4]}.{s[4:]}"
    else:
        return s


def index(request):
    title = "Список мероприятий"
    meets = Meet.objects.all().select_related('format_type').order_by('-date')
    paginator = Paginator(meets, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        "title": title,
        "page_obj": page_obj
    }
    return render(request, 'meet/index.html', context)


class CompetitorMixin:
    model = Competitors

class CompetitorsActionsMixin:
    permission_classes = [IsAuthenticated]
    fields = '__all__'
    success_url = reverse_lazy('meet:competitors_list')
    template_name = 'meet/competitors/competitors_actions.html'


class CompetitorListView(CompetitorMixin, CompetitorsActionsMixin, ListView):
    paginate_by = 10
    ordering = ('name', 'surname')
    template_name = 'meet/competitors/competitors_list.html'


class CompetitorCreateView(CompetitorMixin, CompetitorsActionsMixin, CreateView):
    pass


class CompetitorUpdateView(CompetitorMixin, CompetitorsActionsMixin, UpdateView):
    pass


class CompetitorDeleteView(CompetitorMixin, DeleteView):
    success_url = reverse_lazy('meet:competitors_list')
    template_name = 'meet/competitors/competitors_confirm_delete.html'



class DisciplinesMixin:
    model = Discipline


class DisciplinesActionsMixin:
    permission_classes = [IsAuthenticated]
    fields = '__all__'
    success_url = reverse_lazy('meet:disciplines_list')
    template_name = 'meet/disciplines/disciplines_actions.html'

class DisciplinesListView(DisciplinesMixin, DisciplinesActionsMixin, ListView):
    paginate_by = 10
    ordering = ('name')
    template_name = 'meet/disciplines/disciplines_list.html'

class DisciplinesCreateView(DisciplinesMixin, DisciplinesActionsMixin, CreateView):
    pass

class DisciplinesUpdateView(DisciplinesMixin, DisciplinesActionsMixin, UpdateView):
    pass

class DisciplinesDeleteView(DisciplinesMixin, DeleteView):
    success_url = reverse_lazy('meet:disciplines_list')
    template_name = 'meet/disciplines/disciplines_confirm_delete.html'


def list_competitors(request):
    page_number = request.GET.get('page')
    competitors = Competitors.objects.all().order_by('name', 'surname')
    paginator = Paginator(competitors, 5)
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj
    }
    
    return render(request, 'meet/competitors.html', context)


def meet_detail(request, pk):

    meet = Meet.objects.get(pk=pk)
    if (meet.format_type.format_name == 'Сходка'):
        results = Results.objects.filter(meet__pk=pk).select_related(
            'competitor', 'discipline').order_by('competitor__surname', 'discipline__name', 'round_number')
    elif (meet.format_type.format_name in ['Контест', 'Топ-кубик']):
        results = ResultsContest.objects.filter(meet__pk=pk).select_related('discipline').order_by('competitor', 'discipline__name', 'round_number')

    disciplines_with_rounds = RoundsOfDiscipline.objects.filter(
        meet__pk=pk).select_related("discipline")
    all_res = []
    for i in disciplines_with_rounds:
        rounds = []
        for j in range(i.rounds):
            res = results.filter(discipline=i.discipline, round_number=j+1).order_by('average')
            for p in res:
                p.attempt_1 = format_time(p.attempt_1)
                p.attempt_2 = format_time(p.attempt_2)
                p.attempt_3 = format_time(p.attempt_3)
                p.attempt_4 = format_time(p.attempt_4)
                p.attempt_5 = format_time(p.attempt_5)
            rounds.append(
                {
                    'number': j+1,
                    'results': res
                }
            )
        all_res.append([i.discipline.name, rounds])

    add_result_form = ResultsForm(meet_pk=pk)
    form_add = ExcludeCompetitors(meet_pk=pk)
    form_delete = IncludeCompetitors(meet_pk=pk)
    add_result_contest = ResultsContestForm(meet_pk=pk)

#ОБРАБОТКА ПОСТ ЗАПРОСОВ
    if request.method == "POST":

        #Добавление участника к сходке
        if 'add_competitor' in request.POST:
            form_add = ExcludeCompetitors(request.POST, meet_pk=pk)
            if form_add.is_valid():
                selected_comp = form_add.cleaned_data['comp']
                meet.competitors.add(selected_comp)
                messages.success(
                    request, f'Участник "{selected_comp}" добавлен к сходке.')
            return redirect('meet:meet_detail', pk=meet.pk)

        #Удаление участника со сходки
        elif 'delete_competitor' in request.POST:
            form_delete = IncludeCompetitors(request.POST, meet_pk=pk)
            if form_delete.is_valid():
                results = Results.objects.filter(meet=meet.pk, competitor=form_delete.cleaned_data['competitors'])
                results.delete()
                meet.competitors.remove(form_delete.cleaned_data['competitors'])
                return redirect('meet:meet_detail', pk=meet.pk)

        #Добавление результата участника на сходке
        elif 'add_result' in request.POST:
            add_result_form = ResultsForm(request.POST, meet_pk=pk)
            if add_result_form.is_valid():
                competitor = add_result_form.cleaned_data['competitor']
                discipline = add_result_form.cleaned_data['discipline']
                round_number = add_result_form.cleaned_data['round_number']
                defaults = {
                    "attempt_1": add_result_form.cleaned_data['attempt_1'],
                    "attempt_2": add_result_form.cleaned_data['attempt_2'],
                    "attempt_3": add_result_form.cleaned_data['attempt_3'],
                    "attempt_4": add_result_form.cleaned_data['attempt_4'],
                    "attempt_5": add_result_form.cleaned_data['attempt_5'],
                }

                obj, created = Results.objects.update_or_create(
                    competitor=competitor,
                    meet=meet,
                    discipline=discipline,
                    round_number=round_number,
                    defaults=defaults
                )
                obj.save()

                messages.success(request, 'Результат успешно сохранён.')
                return redirect('meet:meet_detail', pk=meet.pk)
            else:
                print("Ошибки отправки:", add_result_form.errors)

        #Добавление результата участника к контесту
        elif 'add_result_contest' in request.POST:
            if request.method == 'POST':
                add_result_contest = ResultsContestForm(request.POST, meet_pk=pk)
                if add_result_contest.is_valid():
                    competitor = add_result_contest.cleaned_data['competitor']
                    discipline = add_result_contest.cleaned_data['discipline']
                    round_number = add_result_contest.cleaned_data['round_number']
                    attempt_1 = add_result_contest.cleaned_data['attempt_1']
                    attempt_2 = add_result_contest.cleaned_data['attempt_2']
                    attempt_3 = add_result_contest.cleaned_data['attempt_3']
                    attempt_4 = add_result_contest.cleaned_data['attempt_4']
                    attempt_5 = add_result_contest.cleaned_data['attempt_5']
                    
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
                    print("Ошибки отправки:", add_result_contest.errors)

    context = {
        "meet": meet,
        "results": all_res,
        'add_result_form': add_result_form,
        'add_competitor_form': form_add,
        'form_delete': form_delete,
        'add_result_contest': add_result_contest
    }
    return render(request, "meet/detail.html", context)


@login_required
def manage_meet_files(request, pk):
    meet = get_object_or_404(Meet, pk=pk)
    
    if request.method == 'POST':
        formset = MeetFileFormSet(
            request.POST, 
            request.FILES, 
            instance=meet,
            prefix='files'
        )
        
        if formset.is_valid():
            formset.save()
            messages.success(request, "Файлы успешно сохранены!")
            return redirect('meet:manage_meet_files', pk=pk)
        else:
            messages.error(request, "Ошибка при сохранении файлов")
    else:
        formset = MeetFileFormSet(instance=meet, prefix='files')
    
    context = {
        'meet': meet,
        'formset': formset,
    }
    return render(request, 'meet/manage_files.html', context)

@login_required
def delete_meet_file(request, meet_pk, file_pk):
    """Удаление отдельного файла"""
    file = get_object_or_404(MeetFile, pk=file_pk, meet__pk=meet_pk)
    
    # Удаляем файл с диска
    if file.file:
        file.file.delete(save=False)
    
    file.delete()
    messages.success(request, f'Файл "{file.title}" удален')
    return redirect('meet:manage_meet_files', pk=meet_pk)



@login_required
def add_meet(request, pk=None):
    if pk is not None:
        instance = get_object_or_404(Meet, pk=pk)
    else:
        instance = None

    if request.method == 'POST':
        form = MeetForm(request.POST, instance=instance)
        formset = RoundsOfDisciplineFormSet(
            request.POST, instance=instance)  # instance пока нет
        if form.is_valid() and formset.is_valid():
            meet = form.save()  # сохраняем Meet
            # Привязываем formset к созданному meet
            formset.instance = meet
            formset.save()  # сохраняем связи с дисциплинами
            if request.GET.get('detail'):
                return redirect('meet:meet_detail', pk=pk)
            else:
                return redirect('meet:index')  
    else:
        form = MeetForm(instance=instance)
        formset = RoundsOfDisciplineFormSet(instance=instance)

    context = {
        'form': form,
        'formset': formset,
    }
    return render(request, 'meet/add_meet.html', context)

@login_required
def disciplineList(request):
    disciplines = Discipline.objects.all()
    context = {"disciplines": disciplines}
    return render(request, "meet/disciplines.html", context)

@login_required
def add_discipline(request):
    form = DisciplineForm(request.POST or None)
    context = {'form': form}

    if form.is_valid():
        form.save()

    return render(request, 'meet/add_discipline.html', context)

@login_required
def edit_results(request, pk):
    meet = get_object_or_404(Meet, pk=pk)

    # Инициализируем обе формы (для GET и для POST)
    form_add = ExcludeCompetitors(meet_pk=pk)          # форма добавления участника
    form_results = ResultsForm(meet_pk=pk)  # форма ввода результатов
    form_delete = IncludeCompetitors(meet_pk=pk)
    if request.method == "POST":
        # Определяем, какая форма отправлена по наличию поля
        if 'add_competitor' in request.POST:  # кнопка для добавления участника
            form_add = ExcludeCompetitors(request.POST, meet_pk=pk)
            if form_add.is_valid():
                selected_comp = form_add.cleaned_data['comp']
                meet.competitors.add(selected_comp)
                messages.success(
                    request, f'Участник "{selected_comp}" добавлен к сходке.')
                return redirect('meet:edit_results', pk=meet.pk)

        elif 'delete_competitor' in request.POST:
            form_delete = IncludeCompetitors(request.POST, meet_pk=pk)
            if form_delete.is_valid():
                results = Results.objects.filter(meet=meet.pk, competitor=form_delete.cleaned_data['competitor'])
                results.delete()
                meet.competitors.remove(form_delete.cleaned_data['competitor'])
                return redirect('meet:edit_results', pk=meet.pk)
        else:
            # Это отправка формы результатов
            form_results = ResultsForm(request.POST, meet_pk=pk)
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
                if Results.objects.filter(
                    competitor=competitor,
                    meet=meet,
                    discipline=discipline,
                    round_number=round_number
                ).exists():
                    messages.warning(
                        request, 'Запись для этого участника, дисциплины и раунда уже существует.')
                else:
                    Results.objects.create(
                        competitor=competitor,
                        meet=meet,
                        discipline=discipline,
                        round_number=round_number,
                        attempt_1=attempt_1,
                        attempt_2=attempt_2,
                        attempt_3=attempt_3,
                        attempt_4=attempt_4,
                        attempt_5=attempt_5
                    )
                    messages.success(
                        request, 'Результат успешно сохранён (попытки позже).')
                return redirect('meet:edit_results', pk=meet.pk)
            else:
                print("Ошибки отправки:", form_results.errors)

    context = {
        'meet': meet,
        'form_add': form_add,
        'form_delete': form_delete,
        'form_results': form_results,
    }
    return render(request, "meet/edit_results.html", context)

@login_required
def delete_meet(request, pk):
    # Получаем объект модели или выбрасываем 404 ошибку.
    instance = get_object_or_404(Meet, pk=pk)
    # В форму передаём только объект модели;
    # передавать в форму параметры запроса не нужно.
    form = MeetForm(instance=instance)
    context = {'form': form, 'data': instance}
    # Если был получен POST-запрос...
    if request.method == 'POST':
        # ...удаляем объект:
        instance.delete()
        # ...и переадресовываем пользователя на страницу со списком записей.
        return redirect('meet:index')
    # Если был получен GET-запрос — отображаем форму.
    return render(request, 'meet/add_meet.html', context)

@login_required
def change_result_status(request):
    if request.method == 'POST':
        result_id = int(request.POST.get('result_id'))
        try:
            result = ResultsContest.objects.get(id=result_id)
            result.is_published = not result.is_published
            result.save()
            messages.success(request, f'Статус изменен на {"Опубликовано" if result.is_published else "Скрыто"}')
        except ResultsContest.DoesNotExist:
            messages.error(request, 'Результат не найден')
        
        # Перенаправляем обратно
        return redirect(request.META.get('HTTP_REFERER', 'meet:index'))

class GetResultsAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        meet_pk = request.query_params.get('meet_pk')
        discipline_id = request.query_params.get('discipline_id')
        round_number = request.query_params.get('round')
        all_flag = request.query_params.get('all')
        print(all_flag)

        if all_flag != '1':
            competitor_id = request.query_params.get('competitor_id')
            if not all([meet_pk, competitor_id, discipline_id, round_number]):
                return Response(
                    {'error': 'Missing parameters. Required: meet_pk, competitor_id, discipline_id, round'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                # Ищем результат по всем параметрам
                result = Results.objects.get(
                    meet__pk=meet_pk,
                    competitor__pk=competitor_id,
                    discipline__pk=discipline_id,
                    round_number=round_number
                )

                serializer = ResultsSerializer(result)
                return Response(serializer.data)
            except Results.DoesNotExist:
                return Response({})
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        else:
            if not all([meet_pk, all_flag, discipline_id, round_number]):
                return Response(
                    {'error': 'Missing parameters. Required: meet_pk, all_flag, discipline_id, round'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            try:
                # Ищем результат по всем параметрам
                results = Results.objects.filter(
                    meet__pk=meet_pk,
                    discipline__pk=discipline_id,
                    round_number=round_number
                )
                serializer = ResultsSerializer(results, many=True)
                return Response(serializer.data)
            except Results.DoesNotExist:
                return Response({})
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )


class DeleteResultsAPIView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request):
        meet_pk = request.GET.get('meet_pk')
        competitor_id = request.GET.get('competitor_id')
        discipline_id = request.GET.get('discipline_id')
        round_number = request.GET.get('round')

        if not all([meet_pk, competitor_id, discipline_id, round_number]):
            return Response(
                {'error': 'Missing parameters. Required: meet_pk, competitor_id, discipline_id, round'},
                status=status.HTTP_400_BAD_REQUEST
            )

        result = get_object_or_404(Results,
                                   meet__pk=meet_pk,
                                   competitor__pk=competitor_id,
                                   discipline__pk=discipline_id,
                                   round_number=round_number
                                   )
        result.delete()
        return Response({})

