# -*- coding: utf-8 -*-
"""Раздел 6: Визуализация + Раздел 7: Сохранение результатов + Раздел 8: Среды."""

VIZ_CONTENT = r"""
# 6. Визуализация

Визуализация — это финальный шаг аналитического сценария, на котором данные становятся понятными без чтения таблиц. Графики помогают заметить выбросы, увидеть тренды, сравнить группы. Мы используем matplotlib и seaborn: первый даёт полный контроль, второй упрощает статистические графики. В этом разделе — пять ключевых типов графиков, которые покрывают 90% задач аналитика: столбчатая диаграмма, гистограмма, boxplot, линейный график и тепловая карта корреляций.

## 6.1. Подготовка данных и общий шаблон

Перед построением графика данные нужно подготовить: выбрать нужный срез, агрегировать, привести к длинному или широкому формату. Не пытайтесь построить график прямо из "сырого" DataFrame с тысячами строк — сначала агрегируйте до 10-50 значений. Также важно настроить стиль: размер фигуры, шрифт, тему. Эти настройки можно сделать один раз в начале ноутбука.

```env=Jupyter Notebook
import matplotlib.pyplot as plt
import seaborn as sns

# Настройка стиля для всего ноутбука
sns.set_theme(style="whitegrid", palette="muted")
plt.rcParams["figure.figsize"] = (10, 6)
plt.rcParams["font.size"] = 11

# Подготовка данных для визуализации
df_viz = df_clean.copy()
print(df_viz.shape)
df_viz.head()
```

>TIP: Один стиль на весь ноутбук
Вызов `sns.set_theme()` в начале ноутбука задаёт единый стиль для всех графиков. Не нужно повторять настройки в каждой ячейке. Параметр `palette="muted"` даёт спокойные, профессиональные цвета.

## 6.2. Столбчатая диаграмма

Столбчатая диаграмма показывает агрегированные значения по категориям. Подходит для сравнения суммы или среднего по группам: выручка по регионам, число заказов по категориям. В seaborn используется `barplot()` (агрегирует данные) или `countplot()` (считает частоты).

[[IMAGE:build/figures/fig_bar.png:400]]

```env=Jupyter Notebook
# Подготовка: сумма заказов по регионам
region_sum = df_viz.groupby("region")["amount"].sum().reset_index()

# Столбчатая диаграмма
fig, ax = plt.subplots(figsize=(10, 6))
sns.barplot(data=region_sum, x="region", y="amount", ax=ax, color="#1F3A5F")
ax.set_title("Сумма заказов по регионам", fontsize=14)
ax.set_xlabel("Регион")
ax.set_ylabel("Сумма, у.е.")
ax.tick_params(axis="x", rotation=20)

# Сохранение
fig.savefig("figures/bar_region.png", dpi=150, bbox_inches="tight")
plt.show()
```

>TIP: color вместо palette для одного цвета
В новых версиях seaborn для однотонных графиков нужно передавать `color`, а не `palette`. Если вы используете `palette` с одним значением, появится предупреждение. Для нескольких категорий используйте `hue` и `palette`.

[[IMAGE:build/extra_illus/illus_bar_anatomy.png:420]]

## 6.3. Гистограмма

Гистограмма показывает распределение числового признака. Подходит для оценки формы распределения: симметричное, скошенное, с выбросами. Параметр `bins` управляет числом корзин: слишком мало — потеряем детали, слишком много — будет шумно. Хорошее правило — `bins=30` для небольших данных, `bins="auto"` для автоматического подбора.

[[IMAGE:build/figures/fig_hist.png:400]]

```env=Jupyter Notebook
fig, ax = plt.subplots(figsize=(10, 6))
sns.histplot(data=df_viz, x="amount", bins=20, kde=True, color="#2F5A8F", ax=ax)
ax.set_title("Распределение суммы заказов", fontsize=14)
ax.set_xlabel("Сумма заказа")
ax.set_ylabel("Число заказов")
ax.axvline(df_viz["amount"].mean(), color="red", linestyle="--", label=f"Среднее: {df_viz['amount'].mean():.1f}")
ax.axvline(df_viz["amount"].median(), color="green", linestyle="--", label=f"Медиана: {df_viz['amount'].median():.1f}")
ax.legend()
fig.savefig("figures/hist_amount.png", dpi=150, bbox_inches="tight")
plt.show()
```

>NOTE: kde=True добавляет сглаженную кривую
Параметр `kde=True` накладывает поверх гистограммы ядерную оценку плотности — сглаженную кривую распределения. Это помогает визуально оценить форму, не отвлекаясь на шум от корзин.

## 6.4. Boxplot

Boxplot (ящик с усами) показывает медиану, квартили, размах и выбросы по группам. Незаменим для сравнения распределений нескольких категорий: видны медианы, размахи, аномалии. Boxplot "молчит" о форме распределения внутри ящика, но отлично показывает выбросы.

[[IMAGE:build/figures/fig_box.png:400]]

```env=Jupyter Notebook
fig, ax = plt.subplots(figsize=(10, 6))
sns.boxplot(data=df_viz, x="category", y="amount", ax=ax, color="#1F3A5F")
ax.set_title("Распределение суммы по категориям", fontsize=14)
ax.set_xlabel("Категория")
ax.set_ylabel("Сумма заказа")

# Подписи medians на графике
medians = df_viz.groupby("category")["amount"].median()
for i, cat in enumerate(medians.index):
    ax.text(i, medians[cat], f"{medians[cat]:.0f}", ha="center", va="bottom", fontsize=10, color="red")

fig.savefig("figures/boxplot_category.png", dpi=150, bbox_inches="tight")
plt.show()
```

>WARN: Boxplot не показывает размер выборки
Если в одной категории 10 наблюдений, а в другой — 1000, boxplot выглядит одинаково. Для честного сравнения добавьте `sns.stripplot()` поверх `boxplot()`, чтобы показать отдельные точки, или используйте `sns.violinplot()` для оценки плотности.

[[IMAGE:build/extra_illus/illus_boxplot_anatomy.png:420]]

## 6.5. Линейный график

Линейный график показывает изменение признака во времени. Подходит для временных рядов: выручка по дням, число заказов по месяцам, средний чек по неделям. Перед построением убедитесь, что данные отсортированы по дате и сгруппированы до нужной гранулярности (день, неделя, месяц).

[[IMAGE:build/figures/fig_line.png:400]]

```env=Jupyter Notebook
# Подготовка: сумма по дням
df_viz["order_date"] = pd.to_datetime(df_viz["order_date"])
daily = df_viz.groupby("order_date")["amount"].sum().reset_index()

fig, ax = plt.subplots(figsize=(12, 6))
sns.lineplot(data=daily, x="order_date", y="amount", ax=ax, color="#1F3A5F", marker="o")
ax.set_title("Динамика суммы заказов по дням", fontsize=14)
ax.set_xlabel("Дата")
ax.set_ylabel("Сумма, у.е.")
ax.tick_params(axis="x", rotation=30)

# Добавим скользящее среднее
daily["rolling_7"] = daily["amount"].rolling(window=7, min_periods=1).mean()
ax.plot(daily["order_date"], daily["rolling_7"], color="#B25435", linewidth=2, label="Скользящее 7д")
ax.legend()

fig.savefig("figures/line_daily.png", dpi=150, bbox_inches="tight")
plt.show()
```

>TIP: Скользящее среднее для сглаживания
Скользящее среднее (`rolling(window=N).mean()`) сглаживает краткосрочные колебания и показывает тренд. Окно 7 — для дневных данных (неделя), 30 — для месячного сглаживания. `min_periods=1` позволяет считать среднее даже в начале, когда данных меньше окна.

[[IMAGE:build/extra_illus/illus_rolling.png:420]]

## 6.6. Тепловая карта корреляций

Тепловая карта корреляций показывает, какие числовые признаки связаны друг с другом. Значения от -1 (обратная связь) до +1 (прямая). Подходит для разведочного анализа: поиск дублирующих признаков, потенциальных предикторов, скрытых связей.

[[IMAGE:build/figures/fig_heatmap.png:400]]

```env=Jupyter Notebook
# Выбираем только числовые столбцы
numeric_df = df_viz.select_dtypes(include="number")
corr = numeric_df.corr()

fig, ax = plt.subplots(figsize=(10, 8))
sns.heatmap(
    corr,
    annot=True,
    fmt=".2f",
    cmap="RdBu_r",
    center=0,
    vmin=-1,
    vmax=1,
    square=True,
    linewidths=0.5,
    ax=ax,
)
ax.set_title("Корреляция числовых признаков", fontsize=14)
fig.savefig("figures/heatmap_corr.png", dpi=150, bbox_inches="tight")
plt.show()
```

>NOTE: Что показывает корреляция
Значения близко к +1 или -1 — сильная связь. Близко к 0 — связи нет. Но корреляция показывает только линейную связь: если признаки связаны нелинейно (например, U-образно), корреляция будет близка к нулю, хотя связь есть. Не интерпретируйте корреляцию как причинность.

[[IMAGE:build/extra_illus/illus_corr_examples.png:420]]

## 6.7. Сохранение графика в файл

Каждый график стоит сохранять в файл, особенно если он пойдёт в отчёт или презентацию. Параметр `dpi=150` даёт хорошее качество при разумном размере файла. `bbox_inches="tight"` обрезает пустые поля. Для векторной графики используйте формат PDF или SVG — они масштабируются без потери качества.

[[IMAGE:build/extra_illus/illus_line_save.png:420]]

```env=Jupyter Notebook
# Сохранение в PNG
fig.savefig("figures/chart.png", dpi=150, bbox_inches="tight")

# Сохранение в PDF (векторный)
fig.savefig("figures/chart.pdf", bbox_inches="tight")

# Сохранение в SVG (векторный, веб)
fig.savefig("figures/chart.svg", bbox_inches="tight")

# Сохранение в JPG (для фото)
fig.savefig("figures/chart.jpg", dpi=150, bbox_inches="tight", quality=90)
```

>TIP: Создавайте папку для фигур заранее
Перед сохранением убедитесь, что папка существует: `import os; os.makedirs("figures", exist_ok=True)`. Иначе `savefig` упадёт с `FileNotFoundError`. Это частая ошибка при первом запуске ноутбука на новой машине.
"""

SAVE_CONTENT = r"""
# 7. Сохранение результатов

После всех преобразований и анализа наступает этап сохранения результатов. Важно понимать, какой формат выбрать для какой задачи, какие параметры влияют на размер и качество файла, и как не перезаписать исходник случайно. В этом разделе — все ключевые параметры записи для Excel, CSV и Parquet, с примерами для локальной папки и Google Drive.

## 7.1. Сохранение в Excel

Для записи в Excel используется `to_excel()`. Базовый вызов прост, но параметры позволяют управлять именем листа, индексом, форматированием. Для записи в несколько листов нужно создать `ExcelWriter` — это позволяет записать несколько DataFrame в один файл.

```env=Jupyter Notebook
# Базовое сохранение
df_clean.to_excel("data/sales_clean.xlsx", index=False)

# С именем листа
df_clean.to_excel("data/sales_clean.xlsx", sheet_name="Sales 2024", index=False)

# Без заголовков
df_clean.to_excel("data/sales_clean.xlsx", header=False, index=False)

# Запись нескольких DataFrame в один файл
with pd.ExcelWriter("data/sales_multi.xlsx") as writer:
    df_clean.to_excel(writer, sheet_name="Clean", index=False)
    df_work.to_excel(writer, sheet_name="Work", index=False)
    clients_df.to_excel(writer, sheet_name="Clients", index=False)

# С явным движком
df_clean.to_excel("data/sales_clean.xlsx", engine="openpyxl", index=False)
```

>WARN: index=False — почти всегда
По умолчанию `to_excel` записывает индекс как первый столбец. В 95% случаев это нежелательно — индекс просто дублирует нумерацию строк. Передавайте `index=False`, если только индекс не несёт смысловой нагрузки (например, это дата или идентификатор).

>TIP: ExcelWriter с mode="a" — добавление листов
Если нужно добавить лист в существующий файл: `pd.ExcelWriter("data/file.xlsx", mode="a", engine="openpyxl")`. Без `mode="a"` файл будет перезаписан.

## 7.2. Сохранение в CSV

CSV — самый универсальный формат. Запись проста, но параметры сильно влияют на совместимость. Разделитель по умолчанию — запятая; для русского Excel используйте `sep=";"` и `encoding="utf-8-sig"` (с BOM, чтобы Excel корректно распознал кириллицу).

```env=Jupyter Notebook
# Базовое сохранение
df_clean.to_csv("data/sales_clean.csv", index=False)

# С разделителем ; (для русского Excel)
df_clean.to_csv("data/sales_ru.csv", sep=";", index=False, encoding="utf-8-sig")

# Без заголовков
df_clean.to_csv("data/sales_noheader.csv", header=False, index=False)

# Только выбранные столбцы
df_clean.to_csv("data/sales_subset.csv", columns=["order_id", "amount"], index=False)

# С запятой как десятичным разделителем (для русского Excel)
df_clean.to_csv("data/sales_ru_dec.csv", sep=";", decimal=",", index=False, encoding="utf-8-sig")

# Сжатый CSV (gzip)
df_clean.to_csv("data/sales.csv.gz", index=False, compression="gzip")
```

>NOTE: encoding="utf-8-sig" с BOM
`utf-8-sig` добавляет в начало файла три байта BOM (Byte Order Mark). Без них Excel на Windows может неверно определить кодировку и показать кракозябры. Для файлов, которые будут открываться в Excel на Windows, используйте `utf-8-sig`. Для других систем — обычный `utf-8`.

## 7.3. Сохранение в Parquet

Parquet оптимален для больших данных: компактный, с типами, с поддержкой сжатия. Запись через `to_parquet()` поддерживает несколько алгоритмов сжатия: `snappy` (по умолчанию, быстро), `gzip` (компактнее, медленнее), `brotli` (очень компактно, очень медленно). Выбор зависит от приоритета: скорость записи или размер файла.

```env=Jupyter Notebook
# Базовое сохранение
df_clean.to_parquet("data/sales_clean.parquet")

# Без индекса
df_clean.to_parquet("data/sales_clean.parquet", index=False)

# Со сжатием gzip (компактнее)
df_clean.to_parquet("data/sales_gzip.parquet", compression="gzip", index=False)

# Со сжатием snappy (быстрее)
df_clean.to_parquet("data/sales_snappy.parquet", compression="snappy", index=False)

# Через явный движок
df_clean.to_parquet("data/sales_fp.parquet", engine="fastparquet", compression="gzip")
```

>TIP: Сравните размеры файлов
После сохранения сравните размеры трёх форматов: `os.path.getsize("data/sales_clean.xlsx")`, `os.path.getsize("data/sales_clean.csv")`, `os.path.getsize("data/sales_clean.parquet")`. Для больших наборов Parquet обычно в 5-10 раз меньше CSV, и при этом сохраняет типы.

## 7.4. Сохранение в локальную папку, папку проекта и Google Drive

Путь сохранения зависит от среды. В локальном Jupyter — это путь относительно каталога ноутбука. В Colab — путь на примонтированном Google Drive. В PowerShell и Linux — это путь к целевому каталогу.

```env=Jupyter Notebook
# Локальная папка
df_clean.to_csv("output/sales_clean.csv", index=False)

# Папка проекта (создаём, если нет)
import os
os.makedirs("output/clean", exist_ok=True)
df_clean.to_csv("output/clean/sales_2024.csv", index=False)
```

```env=Google Colab
# Сохранение в Google Drive
df_clean.to_csv("/content/drive/MyDrive/projects/sales_clean.csv", index=False)

# Создание подпапки
import os
out_dir = "/content/drive/MyDrive/projects/clean"
os.makedirs(out_dir, exist_ok=True)
df_clean.to_csv(f"{out_dir}/sales_2024.csv", index=False)

# Сохранение в нескольких форматах
df_clean.to_excel(f"{out_dir}/sales_2024.xlsx", index=False)
df_clean.to_parquet(f"{out_dir}/sales_2024.parquet", index=False)
```

>WARN: Colab без Drive — временные файлы
Если не примонтировать Drive, файлы сохранятся в `/content/`, который очищается при закрытии ноутбука. Для постоянного хранения используйте Drive.

## 7.5. Проверка сохранённого файла

После сохранения всегда перечитывайте файл и сравнивайте с тем, что сохраняли. Это простой, но критичный шаг: если файл записался с ошибкой (нет прав, нет места на диске, путь неверный), лучше узнать сразу.

```env=Jupyter Notebook
import os

# Проверка, что файл существует и его размер
path = "data/sales_clean.csv"
print("Файл существует:", os.path.exists(path))
print("Размер, байт:", os.path.getsize(path))

# Перечитывание
df_check = pd.read_csv(path)

# Сравнение
print("Совпадение форм:", df_check.shape == df_clean.shape)
print("Совпадение столбцов:", list(df_check.columns) == list(df_clean.columns))
print("Число строк совпадает:", len(df_check) == len(df_clean))

# Полное сравнение (типы могут отличаться после CSV)
print("Типы до:", df_clean.dtypes.to_dict())
print("Типы после:", df_check.dtypes.to_dict())
```

>NOTE: Полное equals() работает не всегда
После CSV round-trip типы могут измениться: datetime становится object, int с NaN становится float. Поэтому `df_clean.equals(df_check)` вернёт False даже при правильных данных. Сравнивайте форму, столбцы и число строк, а типы — отдельно.

## 7.6. Какой формат выбрать

Выбор формата зависит от задачи. CSV — для обмена, небольших данных, ручного просмотра. Excel — для отчётов и обмена с пользователями Excel. Parquet — для аналитики, больших данных, машинного обучения. JSON — для API и веб-интеграции. SQLite — для локальной аналитической базы.

- CSV: универсальный обмен, чтение в любой среде, ручной просмотр. Минус — не сохраняет типы, большой размер.
- Excel: отчёты для коллег, ручное редактирование, несколько листов. Минус — медленно для больших данных.
- Parquet: хранение для аналитики, быстрые чтение/запись, сохранение типов. Минус — не открывается в Excel напрямую.
- JSON: API, веб-сервисы. Минус — плохо подходит для таблиц.
- SQLite: локальная БД, сложные запросы. Минус — нужно знать SQL.

>TIP: Для аналитики — Parquet, для обмена — CSV
Если вы единственный пользователь данных и они большие — Parquet. Если файлы передаются в другую систему или другой команде — CSV с UTF-8. Excel — только когда получатель не умеет работать с другими форматами.
"""

ENV_CONTENT = r"""
# 8. Работа в Jupyter, Colab, PowerShell и Linux

Каждая среда имеет свои особенности. В этом разделе — короткие рецепты для каждой: как запустить Jupyter, как клонировать проект, как активировать виртуальное окружение, как подключить Google Drive. Главное правило — не путать команды оболочки и Python-код: команды терминала в Jupyter должны предваряться `!`, а Python-код в PowerShell и Linux запускается через `python3`.

## 8.1. Jupyter Notebook

Jupyter — стандартная среда для аналитика. Запуск из терминала — `jupyter notebook` или `jupyter lab`. В ячейке можно смешивать код Python и команды оболочки (с `!`). Для просмотра документации — `?` после имени функции: `pd.read_csv?`.

```env=Linux
# Запуск Jupyter Lab
jupyter lab

# Или классический Jupyter Notebook
jupyter notebook

# Запуск на конкретном порту
jupyter lab --port=8889

# Запуск без открытия браузера (для удалённой работы)
jupyter lab --no-browser --ip=0.0.0.0
```

```env=PowerShell
# На Windows запуск аналогичный
jupyter lab

# Запуск с конкретным каталогом
jupyter lab --notebook-dir=C:\Users\USERNAME\projects
```

```env=Jupyter Notebook
# Команды оболочки внутри ячейки
!pip list
!python --version
!pwd

# Просмотр документации
pd.read_csv?

# Магические команды Jupyter
%time pd.read_csv("data/sales.csv")  # замер времени
%matplotlib inline                    # графики в ноутбуке
%load_ext autoreload                 # автоперезагрузка модулей
```

>NOTE: Магические команды
`%time` замеряет время выполнения, `%%time` — время всей ячейки. `%matplotlib inline` встраивает графики прямо в ноутбук. `%load_ext autoreload` и `%autoreload 2` автоматически перезагружают модули при изменении — удобно при разработке `utils.py`.

## 8.2. Google Colab

Colab — бесплатный Jupyter в облаке Google. Главное отличие — доступ к Google Drive и GPU/TPU. Файлы сохраняются в Drive или во временной папке `/content/`. Для длительной работы — монтируйте Drive.

```env=Google Colab
# Монтирование Google Drive
from google.colab import drive
drive.mount("/content/drive")

# Проверка подключения
import os
print(os.listdir("/content/drive/MyDrive"))

# Установка библиотек (если не входят в стандартный набор Colab)
!pip install pyarrow openpyxl

# Проверка версии Python и окружения
import sys
print("Python:", sys.version)
print("Executable:", sys.executable)
```

```env=Google Colab
# Скачивание файла из Colab на локальный компьютер
from google.colab import files
df_clean.to_csv("sales_clean.csv", index=False)
files.download("sales_clean.csv")

# Загрузка файла с локального компьютера в Colab
from google.colab import files
uploaded = files.upload()
for filename in uploaded.keys():
    print("Загружен:", filename)
```

>WARN: Colab перезапускается
Бесплатный Colab перезапускается через 12 часов (или раньше при неактивности). Все переменные теряются. Сохраняйте результаты в Drive, а не в `/content/`. Для длинных вычислений используйте `checkpointing`: периодически сохраняйте промежуточные DataFrame.

## 8.3. PowerShell (Windows)

PowerShell — стандартная оболочка на Windows. Используется для запуска Python-скриптов, активации виртуального окружения, клонирования репозитория. В PowerShell можно запускать команды git, python, pip без изменений. Виртуальное окружение активируется через `venv\Scripts\Activate.ps1`.

```env=PowerShell
# Создание виртуального окружения
python -m venv venv

# Активация
.\venv\Scripts\Activate.ps1

# Установка пакетов
pip install -r requirements.txt

# Запуск Jupyter
jupyter lab

# Клонирование репозитория
git clone https://github.com/USERNAME/REPOSITORY.git
cd REPOSITORY

# Установка зависимостей проекта
pip install -r requirements.txt

# Запуск ноутбука
jupyter notebook notebook/cheatsheet_demo.ipynb

# Запуск Python-скрипта
python scripts/build_pdf.py

# Деактивация виртуального окружения
deactivate
```

>NOTE: Если PowerShell ругается на Activate.ps1
По умолчанию в PowerShell запрещён запуск скриптов. Разрешите один раз: `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`. После этого `Activate.ps1` будет работать.

## 8.4. Linux и macOS

В Linux и macOS используется bash или zsh. Виртуальное окружение активируется через `source venv/bin/activate`. Команды git, python, pip работают аналогично. На Linux можно использовать системный Python или установить через `pyenv` для нескольких версий.

```env=Linux
# Создание виртуального окружения
python3 -m venv venv

# Активация
source venv/bin/activate

# Установка пакетов
pip install -r requirements.txt

# Запуск Jupyter
jupyter lab

# Клонирование репозитория
git clone https://github.com/USERNAME/REPOSITORY.git
cd REPOSITORY

# Установка зависимостей
pip install -r requirements.txt

# Запуск ноутбука
jupyter notebook notebook/cheatsheet_demo.ipynb

# Запуск Python-скрипта
python3 scripts/build_pdf.py

# Деактивация
deactivate
```

>TIP: venv в проекте — лучшая практика
Создавайте `venv` внутри каждого проекта. Тогда зависимости изолированы, и при обновлении одной библиотеки в одном проекте не сломается другой. Файл `requirements.txt` фиксирует точные версии — воспроизводимость гарантирована.

## 8.5. Клонирование репозитория и первый запуск

Полный сценарий: клонировать репозиторий, создать окружение, установить зависимости, запустить ноутбук. Эти шаги выполняются один раз при первом развертывании проекта на новой машине. Для обновления — `git pull` и при необходимости `pip install -r requirements.txt`.

```env=PowerShell
# Полный сценарий на Windows
git clone https://github.com/USERNAME/REPOSITORY.git
cd REPOSITORY
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
jupyter notebook notebook\cheatsheet_demo.ipynb
```

```env=Linux
# Полный сценарий на Linux/macOS
git clone https://github.com/USERNAME/REPOSITORY.git
cd REPOSITORY
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
jupyter notebook notebook/cheatsheet_demo.ipynb
```

>WARN: Не забывайте активировать venv
Если запустить `pip install` без активации `venv`, пакеты установятся в систему. Это приводит к конфликтам и нестабильности. Перед каждой установкой проверяйте: `which python` (Linux) или `where python` (Windows) — путь должен указывать в `venv`.

## 8.6. Запуск Jupyter в Colab с GitHub

Colab может открыть ноутбук прямо из GitHub. Это удобно для демонстраций и не требует локальной установки. Введите URL GitHub-ноутбука в форму на `https://colab.research.google.com/github/` — Colab откроет его. Если в ноутбуке нужны файлы из репозитория, клонируйте весь репозиторий в `/content/`.

```env=Google Colab
# Клонирование репозитория прямо в Colab
!git clone https://github.com/USERNAME/REPOSITORY.git
%cd REPOSITORY

# Установка зависимостей
!pip install -r requirements.txt

# Теперь можно импортировать модули репозитория
import pandas as pd
from utils import quick_inspect  # если есть utils.py

# Чтение данных из репозитория
df = pd.read_csv("data/sales.csv")
quick_inspect(df, "df")
```

>TIP: %cd — магическая команда смены каталога
В Colab `%cd` меняет рабочий каталог для всего ноутбука. Обычный `cd` не работает (это команда оболочки, а не Python). После `%cd REPOSITORY` пути вида `data/sales.csv` работают корректно.
"""

CHECKLIST_CONTENT = r"""
# 9. Итоговый чек-лист

Перед тем как считать работу выполненной, пройдите чек-лист. Он собран из практики: каждая пункта — это типичная ошибка, которую легко пропустить. Отметьте всё, что подтверждено; не отмечайте "на всякий случай" — лучше явно проверить.

## 9.1. Чек-лист для PDF-шпаргалки

[[CHECKLIST]]
- Все примеры кода запускаются без ошибок в чистом окружении с `requirements.txt`.
- Имена переменных согласованы: `df_raw`, `df_work`, `df_clean`, `sales_df` используются единообразно во всех разделах.
- Каждый блок кода имеет метку среды выполнения: Jupyter Notebook, Google Colab, PowerShell, Linux или Python.
- Все ссылки на репозиторий используют шаблоны `USERNAME` и `REPOSITORY`, а не реальные имена.
- Версии библиотек актуальны: pandas ≥ 2.0, openpyxl ≥ 3.1, pyarrow ≥ 14.0, matplotlib ≥ 3.7, seaborn ≥ 0.13.
- Разделы идут в логичном порядке: подготовка среды → чтение → осмотр → преобразование → безопасность → визуализация → сохранение → среды.
- Для каждого важного преобразования есть проверка результата (`shape`, `isna().sum()`, `dtypes`).
- В тексте нет таблиц; используется форматирование заголовками, списками и блоками кода.
- Нет несуществующих ссылок на репозитории или файлы.
- Блоки "Совет" и "Внимание" выделены и не перекрывают код.
[[END]]

## 9.2. Чек-лист для Jupyter Notebook

[[CHECKLIST]]
- Ноутбук запускается сверху вниз без ошибок: `Kernel → Restart & Run All`.
- Все ячейки с кодом имеют комментарии и markdown-пояснения.
- Воспроизводимый набор `sales_df` генерируется в первой ячейке после импортов.
- Демонстрационные данные не требуют внешних файлов — всё генерируется в коде.
- В ноутбуке есть проверки результатов после каждого важного шага.
- Используется дисциплина `df_raw`/`df_work`/`df_clean` во всех примерах.
- В конце ноутбука сохраняются результаты в трёх форматах: `.csv`, `.xlsx`, `.parquet`.
- Импорты согласованы и не дублируются.
- Версии библиотек можно проверить одной ячейкой: `pd.__version__`, `np.__version__` и т.д.
[[END]]

## 9.3. Чек-лист для репозитория на GitHub

[[IMAGE:build/extra_illus/fig_github.png:420]]

[[CHECKLIST]]
- Файл `README.md` существует, на русском языке, описывает проект и его назначение.
- Файл `requirements.txt` содержит все необходимые библиотеки с минорными версиями.
- Файл `LICENSE` существует и содержит лицензию MIT (или другую выбранную).
- Файл `.gitignore` игнорирует `venv/`, `__pycache__/`, `.ipynb_checkpoints/`, временные файлы.
- PDF-шпаргалка лежит в корне или в `docs/` и доступна для скачивания.
- Исходник PDF (Python-скрипт ReportLab) лежит в `scripts/` и может быть запущен.
- Jupyter Notebook лежит в `notebook/` и запускается.
- В README есть команды для клонирования и запуска на Linux и PowerShell.
- В README есть ссылка на открытие ноутбука в Colab.
- Репозиторий публичный (для общедоступного использования) или имеет описание в README.
[[END]]

## 9.4. Финальные советы

>NOTE: Перед публикацией — свежий взгляд
Откройте репозиторий на новой машине, пройдите по шагам README от клонирования до запуска. Если что-то не получается "с нуля" — это сигнал, что в README не хватает важного шага. Хорошо задокументированный проект узнаётся именно по этому тесту.

>TIP: Версии в requirements.txt
Используйте точные версии: `pandas==2.2.0`, а не `pandas>=2.0`. Это даёт гарантированную воспроизводимость. Для обновления — отдельный коммит с повышением версий и проверкой.

>WARN: Не коммитьте большие файлы
PDF размером до 10 МБ — нормально для Git. Больше — лучше через Git LFS или выложить отдельно (например, на GitHub Releases). Файлы данных в `data/` — только если они небольшие и нужны для примеров.

[[IMAGE:build/extra_illus/illus_save_formats.png:420]]
"""
