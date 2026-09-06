from django.db import models
import re
from decimal import Decimal, InvalidOperation
from django.core.validators import FileExtensionValidator
import math
import os


def seconds_to_time_format_floor(seconds):
            if seconds is None or seconds < 0:
                return "DNF"
            
            try:
                # Округляем вниз до 2 знаков после запятой
                # seconds_floor = math.floor(seconds * 100) / 100
                
                # Вычисляем минуты и секунды
                minutes = int(seconds // 60)
                remaining_seconds = round(seconds % 60, 2)

                if minutes != 0:
                    # Форматируем строку: минуты:секунды.сотые
                    return f"{minutes}:{remaining_seconds}"
                else:
                    return f"{remaining_seconds:.2f}"
            
            except (ValueError, TypeError):
                return "DNF"

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
        # Если больше 6 цифр, можно попытаться интерпретировать как обычное время (секунды/сотые)
        # но по условию не указано, поэтому возвращаем как есть или ошибка
        return s


def parse_time_string_to_seconds(time_str):
    """
    Преобразует строку с числами в секунды по правилам количества цифр.
    
    Правила:
    - 2 цифры:  XX -> 0.XX секунд (пример: 69 -> 0.69)
    - 3 цифры:  SXX -> S.XX секунд (пример: 890 -> 8.90)
    - 4 цифры:  SSXX -> SS.XX секунд (пример: 1000 -> 10.00)
    - 5 цифр:   MSSXX -> M*60 + SS.XX секунд (пример: 12345 -> 83.45)
    - 6 цифр:   MMSSXX -> MM*60 + SS.XX секунд (пример: 195678 -> 1176.78)
    
    Аргументы:
        time_str: str - строка с числом
    Возвращает:
        float - количество секунд или None для DNF
    """
    if not time_str or str(time_str).strip() == "":
        return None
    
    time_str = str(time_str).strip().upper()

    if time_str in ("DNF", "dnf", "d"):
        return float('inf')
    
    try:
        s = str(int(time_str))
    except (ValueError, TypeError):
        return None
    
    length = len(s)
    
    if length == 2:
        # XX -> 0.XX
        centiseconds = int(s)
        return centiseconds / 100
    
    elif length == 3:
        # SXX -> S.XX
        seconds = int(s[0])
        centiseconds = int(s[1:])
        return seconds + centiseconds / 100
    
    elif length == 4:
        # SSXX -> SS.XX
        seconds = int(s[:2])
        centiseconds = int(s[2:])
        return seconds + centiseconds / 100
    
    elif length == 5:
        # MSSXX -> M:SS.XX
        minutes = int(s[0])
        seconds = int(s[1:3])
        centiseconds = int(s[3:])
        return minutes * 60 + seconds + centiseconds / 100
    
    elif length == 6:
        # MMSSXX -> MM:SS.XX
        minutes = int(s[:2])
        seconds = int(s[2:4])
        centiseconds = int(s[4:])
        return minutes * 60 + seconds + centiseconds / 100
    
    else:
        # Если больше 6 цифр или меньше 2 - возвращаем None
        return None


class MeetFile(models.Model):
    """Модель для хранения файлов, прикрепленных к соревнованию"""
    
    meet = models.ForeignKey(
        'Meet', 
        on_delete=models.CASCADE, 
        related_name='files',
        verbose_name="Соревнование"
    )
    
    file = models.FileField(
        upload_to='meet_files/%Y/%m/%d/',
        validators=[FileExtensionValidator(allowed_extensions=['pdf', 'doc', 'docx', 'txt'])],
        verbose_name="Файл"
    )
    
    title = models.CharField(
        max_length=255, 
        blank=True,
        verbose_name="Название файла"
    )
    
    description = models.TextField(
        blank=True, 
        verbose_name="Описание"
    )
    
    uploaded_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата загрузки"
    )
    
    
    class Meta:
        verbose_name = "Файл соревнования"
        verbose_name_plural = "Файлы соревнований"
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.title or os.path.basename(self.file.name)
    
    def save(self, *args, **kwargs):
        # Автоматически устанавливаем название файла, если не задано
        if not self.title and self.file:
            self.title = os.path.basename(self.file.name)
        
        
        super().save(*args, **kwargs)


# Create your models here.
class Competitors(models.Model):
    name = models.CharField(max_length=255, verbose_name="Имя участника")
    surname = models.CharField(max_length=255, verbose_name="Фамилия участника")
    uni_id = models.SlugField(max_length=8, verbose_name="RSFID")

    class Meta:
        verbose_name = "Участник"
        verbose_name_plural = "Участники"

    def __str__(self):
        return f"{self.name} {self.surname}"


class Discipline(models.Model):
    slug_id = models.SlugField(max_length=8, verbose_name="Слаг поле дисциплины")
    name = models.CharField(max_length=25, verbose_name="Название дисциплины")

    class Meta:
        verbose_name = "Дисциплина"
        verbose_name_plural = "Дисциплины"

    def __str__(self):
        return self.name


class RoundsOfDiscipline(models.Model):
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE, verbose_name="Дисциплина")
    rounds = models.IntegerField(default=1, verbose_name="Количество раундов")
    meet = models.ForeignKey('Meet', on_delete=models.CASCADE, verbose_name="Сходка")  # Используем строку 'Meet'

    class Meta:
        verbose_name = "Раунд дисциплины"
        verbose_name_plural = "Раунды дисциплин"

    def __str__(self):
        return f"{self.discipline.name} - {self.rounds} раундов"

class FormatType(models.Model):
    format_name = models.CharField(max_length=30, verbose_name='Название типов')

    class Meta:
        verbose_name = 'Формат проведения'
        verbose_name_plural = 'Форматы проведения'

    def __str__(self):
        return self.format_name


class Meet(models.Model):
    name = models.CharField(max_length=255, verbose_name="Название сходки")
    date = models.DateTimeField(verbose_name="Дата проведения сходки")
    locations = models.CharField(max_length=30, default="ДВФУ", blank=True, verbose_name='Место проведения')
    description = models.TextField(verbose_name="Описание сходки")
    competitors = models.ManyToManyField(Competitors, verbose_name="Участники сходки")
    disciplines = models.ManyToManyField(Discipline, through=RoundsOfDiscipline, verbose_name="Дисциплины сходок")
    format_type = models.ForeignKey(FormatType, on_delete=models.SET_NULL, blank=True, null=True, verbose_name='Формат проведения')
    

    class Meta:
        verbose_name = "Сходка"
        verbose_name_plural = "Сходки"
        ordering = ("date", )

    def __str__(self):
        return self.name

class Results(models.Model):
    competitor = models.ForeignKey("Competitors", on_delete=models.CASCADE)
    meet = models.ForeignKey(Meet, on_delete=models.CASCADE)
    discipline = models.ForeignKey(Discipline, on_delete=models.CASCADE)
    round_number = models.IntegerField(default=1, verbose_name="Номер раунда")

    attempt_1 = models.CharField(max_length=15, default=0, verbose_name="Первая попытка")
    attempt_2 = models.CharField(max_length=15, default=0, verbose_name="Вторая попытка")
    attempt_3 = models.CharField(max_length=15, default=0, verbose_name="Третья попытка")
    attempt_4 = models.CharField(max_length=15, default=0, verbose_name="Четвертая попытка")
    attempt_5 = models.CharField(max_length=15, default=0, verbose_name="Пятая попытка")

    average = models.DecimalField(default=0.00, decimal_places=2, max_digits=6, verbose_name="Среднее")
    best = models.DecimalField(default=0.00, decimal_places=2, max_digits=6, verbose_name="Лучшее")



    def save(self, *args, **kwargs):
        # Парсим попытки, но не изменяем сами поля (храним ввод пользователя)
        parsed = [
            parse_time_string_to_seconds(self.attempt_1),
            parse_time_string_to_seconds(self.attempt_2),
            parse_time_string_to_seconds(self.attempt_3),
            parse_time_string_to_seconds(self.attempt_4),
            parse_time_string_to_seconds(self.attempt_5)
        ]

        print(parsed)

        # Убираем None (пустые или нулевые попытки)
        valid = [x for x in parsed if x is not None]
        print(valid)

        # Вычисление лучшего времени (минимальное числовое, DNF игнорируется)
        numeric = [x for x in valid if x != float('inf')]
        print(numeric)
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

        # Сохраняем модель (поля attempt_* остаются в исходном виде)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Результат"
        verbose_name_plural = "Результаты"
        unique_together = ('competitor', 'meet', 'discipline', 'round_number')