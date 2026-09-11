from django import forms
from .models import Meet, Discipline, Competitors, RoundsOfDiscipline, Results, MeetFile
from django.forms import inlineformset_factory
from django.contrib.admin.widgets import FilteredSelectMultiple
from django_select2.forms import Select2Widget, Select2MultipleWidget


class MeetForm(forms.ModelForm):
    competitors = forms.ModelMultipleChoiceField(
        queryset=Competitors.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control'}),
        required=False,
        label="Участники",
        help_text='Для выбора нескольких участников зажмите CTRL и выбирайте'
    )

    class Meta:
        model = Meet
        fields = ['name', 'description', 'competitors', 'date', 'locations', 'format_type', 'is_published']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'form-control'
            }, format='%Y-%m-%dT%H:%M'),
        }

class RoundsOfDisciplineForm(forms.ModelForm):
    class Meta:
        model = RoundsOfDiscipline
        fields = ['discipline', 'rounds']
        widgets = {
            'discipline': forms.Select(attrs={'class': 'form-control'}),
            'rounds': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

RoundsOfDisciplineFormSet = inlineformset_factory(
    Meet,
    RoundsOfDiscipline,
    form=RoundsOfDisciplineForm,
    extra=1,          # одна пустая форма для добавления
    can_delete=True,  # добавляет чекбокс удаления
    min_num=0,
    validate_min=False,
)

class formtest(forms.Form):
    text = forms.CharField(max_length=50)


class ExcludeCompetitors(forms.Form):
    comp = forms.ModelChoiceField(
        queryset=Competitors.objects.none(),
        label="Выберите участника"
    )

    def __init__(self, *args, meet_pk=None, **kwargs):
        super().__init__(*args, **kwargs)
        if meet_pk:
            self.fields['comp'].queryset = Competitors.objects.exclude(meet__pk=meet_pk)


class IncludeCompetitors(forms.Form):
    competitors = forms.ModelChoiceField(
        queryset=Competitors.objects.none(),
        label="Выберите участника"
    )

    def __init__(self, *args, meet_pk=None, **kwargs):
        super().__init__(*args, **kwargs)
        if meet_pk:
            self.fields['competitors'].queryset = Competitors.objects.filter(meet__pk=meet_pk)

class ResultsСontestForm(forms.Form):
    competitor = forms.CharField(max_length=30, label='Введите ИМЯ и ФАМИЛИЮ') 
    
    discipline = forms.ModelChoiceField(
        queryset=Discipline.objects.none(),
        label="Дисциплина",
        empty_label="Выберите дисциплину"
    )
    round_number = forms.IntegerField(
        label="Номер раунда",
        min_value=1,
        initial=1
    )

    attempt_1 = forms.CharField(max_length=10, label="Первая попытка")
    attempt_2 = forms.CharField(max_length=10, label="Вторая попытка")
    attempt_3 = forms.CharField(max_length=10, label="Третья попытка")
    attempt_4 = forms.CharField(max_length=10, label="Четвертая попытка")
    attempt_5 = forms.CharField(max_length=10, label="Пятая попытка")


    def __init__(self, *args, meet_pk=None, **kwargs):
        super().__init__(*args, **kwargs)
        if meet_pk:
            self.initial['meet_pk'] = meet_pk
                # Участники, связанные с этой встречей
                # Дисциплины, привязанные к встрече через промежуточную модель
            self.fields['discipline'].queryset = Discipline.objects.filter(
                    roundsofdiscipline__meet__pk=meet_pk
            ).distinct()
    
    def clean(self):

        cleaned_data = super().clean()
        competitor = cleaned_data.get('competitor')
        discipline = cleaned_data.get('discipline')
        round_number = cleaned_data.get('round_number')
        meet_pk = self.initial.get('meet_pk')
    
        if not all([competitor, discipline, round_number]):
            return cleaned_data
    
            # Получаем максимальное количество раундов для этой дисциплины на этой встрече
        try:
            rounds_of = RoundsOfDiscipline.objects.get(meet__pk=meet_pk, discipline=discipline)
            max_rounds = rounds_of.rounds
        except RoundsOfDiscipline.DoesNotExist:
            raise forms.ValidationError("Дисциплина не привязана к этой встрече.")
    
        if round_number > max_rounds:
            raise forms.ValidationError(f"Для выбранной дисциплины доступно только {max_rounds} раундов.")
    
        return cleaned_data


class ResultsForm(forms.Form):
    competitor = forms.ModelChoiceField(
        queryset=Competitors.objects.none(),
        label="Участник",
        empty_label="Выберите участника",
        widget=forms.Select(attrs={
            'class': 'form-control select2',
            'data-placeholder': 'Поиск участника...',
            'style': 'width: 100%;'
    })
    )
    discipline = forms.ModelChoiceField(
        queryset=Discipline.objects.none(),
        label="Дисциплина",
        empty_label="Выберите дисциплину"
    )
    round_number = forms.IntegerField(
        label="Номер раунда",
        min_value=1,
        initial=1
    )

    attempt_1 = forms.CharField(max_length=10, label="Первая попытка")
    attempt_2 = forms.CharField(max_length=10, label="Вторая попытка")
    attempt_3 = forms.CharField(max_length=10, label="Третья попытка")
    attempt_4 = forms.CharField(max_length=10, label="Четвертая попытка", required=False)
    attempt_5 = forms.CharField(max_length=10, label="Пятая попытка", required=False)

            
    def __init__(self, *args, meet_pk=None, **kwargs):
        super().__init__(*args, **kwargs)
        if meet_pk:
            self.initial['meet_pk'] = meet_pk
            # Участники, связанные с этой встречей
            self.fields['competitor'].queryset = Competitors.objects.filter(meet__pk=meet_pk)
            # Дисциплины, привязанные к встрече через промежуточную модель
            self.fields['discipline'].queryset = Discipline.objects.filter(
                roundsofdiscipline__meet__pk=meet_pk
            ).distinct()

    def clean(self):
        cleaned_data = super().clean()
        competitor = cleaned_data.get('competitor')
        discipline = cleaned_data.get('discipline')
        round_number = cleaned_data.get('round_number')
        meet_pk = self.initial.get('meet_pk')  # или можно передать через аргументы

        if not all([competitor, discipline, round_number]):
            return cleaned_data

        # Получаем максимальное количество раундов для этой дисциплины на этой встрече
        try:
            rounds_of = RoundsOfDiscipline.objects.get(meet__pk=meet_pk, discipline=discipline)
            max_rounds = rounds_of.rounds
        except RoundsOfDiscipline.DoesNotExist:
            raise forms.ValidationError("Дисциплина не привязана к этой встрече.")

        if round_number > max_rounds:
            raise forms.ValidationError(f"Для выбранной дисциплины доступно только {max_rounds} раундов.")

        fmt = discipline.result_format.name

        if (fmt == 'Ao5') and (not cleaned_data.get('attempt_4') and not cleaned_data.get('attempt_5')):
            self.add_error('attempt_4', 'Это поле обязательно для этого формата.')
            self.add_error('attempt_5', 'Это поле обязательно для этого формата.')
            
            

        return cleaned_data

class DisciplineForm(forms.ModelForm):
    class Meta:
        model = Discipline
        fields = "__all__"


class MeetFileForm(forms.ModelForm):
    class Meta:
        model = MeetFile
        fields = ['file', 'title', 'description']
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.txt'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Название файла (опционально)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Описание файла (опционально)'
            }),
        }
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            # Проверка размера файла (например, максимум 10 МБ)
            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError("Размер файла не должен превышать 10 МБ")
        return file

# Formset для управления несколькими файлами
from django.forms import inlineformset_factory

MeetFileFormSet = inlineformset_factory(
    Meet,
    MeetFile,
    form=MeetFileForm,
    extra=1,
    can_delete=True,
    can_delete_extra=True,
)
