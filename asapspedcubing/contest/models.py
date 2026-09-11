from django.db import models
from meet.models import parse_time_string_to_seconds, seconds_to_time_format_floor, Discipline, Meet


# Create your models here.
class ResultsContest(models.Model):
    competitor = models.CharField(max_length=40, verbose_name='Имя Фамилия')
    meet = models.ForeignKey(Meet, on_delete=models.CASCADE)
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, verbose_name='Дисциплина')
    round_number = models.IntegerField(default=1, verbose_name="Номер раунда")
    is_published = models.BooleanField(default=True, verbose_name='Опубликован')

    attempt_1 = models.CharField(max_length=15, default=0, verbose_name="Первая попытка")
    attempt_2 = models.CharField(max_length=15, default=0, verbose_name="Вторая попытка")
    attempt_3 = models.CharField(max_length=15, default=0, verbose_name="Третья попытка")
    attempt_4 = models.CharField(max_length=15, default=0, verbose_name="Четвертая попытка")
    attempt_5 = models.CharField(max_length=15, default=0, verbose_name="Пятая попытка")

    average = models.CharField(max_length=8, verbose_name="Среднее")
    best = models.CharField(max_length=8, verbose_name="Лучшее")


    def save(self, *args, **kwargs):
        if self.discipline.result_format.name == 'Ao5':
            parsed = [
                parse_time_string_to_seconds(self.attempt_1),
                parse_time_string_to_seconds(self.attempt_2),
                parse_time_string_to_seconds(self.attempt_3),
                parse_time_string_to_seconds(self.attempt_4),
                parse_time_string_to_seconds(self.attempt_5)
            ]
            valid = [x for x in parsed if x is not None]

            # Вычисление лучшего времени (минимальное числовое, DNF игнорируется)
            numeric = [x for x in valid if x != float('inf')]
            if numeric:
                best_sec = min(numeric)
                self.best = seconds_to_time_format_floor(best_sec)
            else:
                self.best = "DNF"

            # Вычисление среднего (удаление лучшей и худшей, если >=3 попыток)
            if len(valid) < 3:
                self.average = "DNF"
            else:
                sorted_vals = sorted(valid)          # inf (DNF) будет в конце
                middle_three = sorted_vals[1:-1]     # удаляем лучшую и худшую
                if any(x == float('inf') for x in middle_three):
                    self.average = "DNF"
                else:
                    print(middle_three)
                    avg = round((sum(middle_three) / 3), 2)
                    self.average = seconds_to_time_format_floor(avg)


        elif self.discipline.result_format.name == 'Mo3':
            parsed = [
                        parse_time_string_to_seconds(self.attempt_1),
                        parse_time_string_to_seconds(self.attempt_2),
                        parse_time_string_to_seconds(self.attempt_3),
                    ]
            valid = [x for x in parsed if x is not None]
            numeric = [x for x in valid if x != float('inf')]
            if numeric:
                best_sec = min(numeric)
                self.best = seconds_to_time_format_floor(best_sec)
            else:
                self.best = "DNF"

            if len(valid) < 2:
                self.average = "DNF"
            else:
                avg = round((sum(valid) / 3), 2)
                self.average = seconds_to_time_format_floor(avg)


        # Убираем None (пустые или нулевые попытки)
        

        # Сохраняем модель (поля attempt_* остаются в исходном виде)
        super().save(*args, **kwargs)
    class Meta:
        verbose_name = "Результат"
        verbose_name_plural = "Результаты"
        unique_together = ('competitor', 'meet', 'discipline', 'round_number')
