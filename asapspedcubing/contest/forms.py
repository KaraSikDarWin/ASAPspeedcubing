from django import forms
from meet.models import Meet, Discipline, Competitors, RoundsOfDiscipline, Results

class ResultsContestForm(forms.Form):

    competitor = forms.CharField(max_length=40, 
                                 label='Имя фамилия', 
                                 empty_value='Напишите имя и фамилию (имеено в таком порядке)', 
                                 widget=forms.TextInput(attrs={
                                    'class': 'form-control',
                                    'name': 'contest_id_competitor',
                                    'id': 'contest_id_competitor',
    }))
    discipline = forms.ModelChoiceField(
        queryset=Discipline.objects.none(),
        label="Дисциплина",
        empty_label="Выберите дисциплину",
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

        return cleaned_data