# -*- coding: utf-8 -*-
"""Раздел 4: Анализ и преобразование данных + Раздел 5: Целостность и безопасность."""

TRANSFORM_CONTENT = r"""
# 4. Анализ и преобразование данных

После первичного осмотра начинается этап активной работы с данными: обработка пропусков, дубликатов, типов, дат, текста, выбросов, объединений и агрегаций. Каждый шаг должен сопровождаться проверкой результата — иначе легко незаметно потерять строки, изменить тип или сломать индекс. В этом разделе мы проходим все ключевые приёмы и для каждого показываем, как убедиться, что преобразование сработало как ожидалось.

## 4.1. Поиск и обработка пропусков

Пропуски в реальных данных — норма, а не исключение. Важно понимать, что с ними делать: удалить, заполнить константой, заполнить статистикой (медиана, среднее, мода) или оставить как есть, если для анализа они не критичны. Выбор стратегии зависит от доли пропусков, природы столбца и цели анализа. Главное правило — любое действие с пропусками должно сопровождаться проверкой `isna().sum()` до и после.

```env=Jupyter Notebook
# Рабочая копия — исходный sales_df не трогаем
df_work = sales_df.copy()

# Сколько пропусков
print(df_work.isna().sum())

# Удаление строк с любым пропуском
df_drop_any = df_work.dropna()
print("Было:", len(df_work), "Стало:", len(df_drop_any))

# Удаление строк, где пропуск в конкретном столбце
df_drop_amount = df_work.dropna(subset=["amount"])

# Удаление столбцов, где все значения — пропуски
df_drop_cols = df_work.dropna(axis=1, how="all")

# Заполнение константой
df_fill_const = df_work.fillna({"client": "Unknown", "amount": 0})

# Заполнение статистикой
median_amount = df_work["amount"].median()
df_fill_med = df_work.copy()
df_fill_med["amount"] = df_work["amount"].fillna(median_amount)

# Заполнение вперёд (forward fill) — для временных рядов
df_ffill = df_work.sort_values("order_date").ffill()

# Заполнение назад (backward fill)
df_bfill = df_work.sort_values("order_date").bfill()
```

>WARN: fillna без словаря меняет все столбцы
`df.fillna(0)` заполнит нулями все пропуски во всех столбцах. В числовых столбцах это нормально, но в строковых появится "0" как строка. Всегда передавайте словарь: `df.fillna({"col_num": 0, "col_str": "Unknown"})`.

>TIP: Проверка после заполнения
После любого заполнения убедитесь, что результат именно тот, что вы задумали: `df["col"].isna().sum()` должно вернуть 0, а `df["col"].value_counts()` — показать новое значение. Частая ошибка — заполнить "мало", а потом обнаружить, что остались редкие NaN в неожиданных местах.

## 4.2. Поиск и удаление дубликатов

Дубликаты бывают двух типов: полные (вся строка повторяется) и по подмножеству столбцов (например, два заказа с одинаковым `order_id`). `duplicated()` возвращает логическую маску, `drop_duplicates()` сразу удаляет. Параметр `keep` управляет тем, какую копию оставить: `"first"` (по умолчанию), `"last"` или `False` (удалить все дубликаты).

```env=Jupyter Notebook
# Число дубликатов (полных)
print("Полных дубликатов:", df_work.duplicated().sum())

# Дубликаты по подмножеству столбцов
print("Дубли по order_id:", df_work.duplicated(subset=["order_id"]).sum())

# Удаление полных дубликатов
df_dedup = df_work.drop_duplicates()

# Удаление дубликатов по конкретным столбцам, оставить последний
df_dedup_id = df_work.drop_duplicates(subset=["order_id"], keep="last")

# Удаление всех дубликатов (оставить только уникальные)
df_only_unique = df_work.drop_duplicates(subset=["order_id"], keep=False)

# Проверка
print("После удаления:", len(df_dedup), "Было:", len(df_work))
print("Осталось дубликатов:", df_dedup.duplicated().sum())
```

>NOTE: keep=False для аналитики
Если вы хотите найти "подозрительные" строки, у которых есть двойник — используйте `keep=False`. Это вернёт все строки, у которых есть хотя бы один дубликат, без выбора "основного". Удобно для аудита данных.

[[IMAGE:build/extra_illus/illus_duplicates.png:420]]

## 4.3. Проверка и преобразование типов

Корректные типы столбцов — основа корректной аналитики. Числа в строковом виде не агрегируются, даты в строковом виде не поддерживают временные операции, категории в строковом виде занимают больше памяти. После чтения всегда проверяйте типы и при необходимости преобразуйте через `astype()`, `to_datetime()`, `to_numeric()`.

```env=Jupyter Notebook
# Текущие типы
print(df_work.dtypes)

# Преобразование числового столбца, который оказался строкой
df_work["amount_num"] = pd.to_numeric(df_work["amount"], errors="coerce")

# Преобразование строки в дату
df_work["order_date_dt"] = pd.to_datetime(df_work["order_date"], errors="coerce")

# Преобразование строки в категорию (экономит память)
df_work["category_cat"] = df_work["category"].astype("category")

# Преобразование в int с обработкой пропусков (int не поддерживает NaN)
df_work["quantity_int"] = df_work["quantity"].fillna(0).astype(int)

# Проверка
print(df_work[["amount", "amount_num", "order_date", "order_date_dt"]].dtypes)
```

>WARN: int и NaN
Стандартный `int64` в pandas не поддерживает пропуски. Если в столбце есть NaN, `astype(int)` упадёт. Используйте `Int64` (с большой буквы) — это Nullable Integer type, который допускает пропуски: `df["col"].astype("Int64")`.

>TIP: errors="coerce" — удобное падение
Параметр `errors="coerce"` в `to_numeric` и `to_datetime` превращает не разбираемые значения в `NaN`, а не падает с ошибкой. После преобразования проверьте, сколько новых пропусков появилось: `df["col"].isna().sum()`. Если их много — где-то проблема в исходных данных.

## 4.4. Обработка дат

Даты требуют особого внимания. Формат может быть разным (`YYYY-MM-DD`, `DD.MM.YYYY`, `MM/DD/YYYY`), а часовые пояса добавляют отдельный уровень сложности. Pandas предоставляет `to_datetime()` с гибким параметром `format` для явного указания формата. После преобразования открываются возможности: извлечение компонент (год, месяц, день недели), расчёт разницы, скользящие окна.

```env=Jupyter Notebook
# Преобразование с автоматическим определением формата
df_work["date_dt"] = pd.to_datetime(df_work["order_date"], errors="coerce")

# Явное указание формата — быстрее и точнее
df_work["date_dt"] = pd.to_datetime(df_work["order_date"], format="%Y-%m-%d")

# Извлечение компонент
df_work["year"] = df_work["date_dt"].dt.year
df_work["month"] = df_work["date_dt"].dt.month
df_work["day"] = df_work["date_dt"].dt.day
df_work["weekday"] = df_work["date_dt"].dt.day_name()
df_work["is_weekend"] = df_work["date_dt"].dt.weekday >= 5

# Разница между датами
df_work["days_since_start"] = (df_work["date_dt"] - df_work["date_dt"].min()).dt.days

# Фильтрация по диапазону дат
mask_2024 = (df_work["date_dt"] >= "2024-01-01") & (df_work["date_dt"] <= "2024-12-31")
df_2024 = df_work[mask_2024]

# Проверка
print(df_work[["date_dt", "year", "month", "weekday", "is_weekend"]].head())
```

>NOTE: Формат даты и локаль
`%Y` — четырёхзначный год, `%m` — месяц (01-12), `%d` — день (01-31), `%H` — часы, `%M` — минуты, `%S` — секунды. Полный список — в документации Python `datetime.strftime`. Если даты на русском (например, "31 января 2024"), придётся использовать `format="%d %B %Y"` с учётом локали.

## 4.5. Очистка текстовых значений

Текстовые столбцы часто содержат мусор: лишние пробелы, разный регистр, скрытые символы, опечатки. Pandas через `.str` даёт доступ к строковым методам. Регулярная очистка текста перед агрегацией или объединением таблиц — обязательный шаг, иначе два "одинаковых" значения окажутся разными.

```env=Jupyter Notebook
# Удаление пробелов в начале и конце
df_work["client_clean"] = df_work["client"].str.strip()

# Приведение к нижнему регистру
df_work["client_lower"] = df_work["client"].str.lower()

# Замена внутренних пробелов на одно
df_work["client_norm"] = df_work["client"].str.replace(r"\s+", " ", regex=True).str.strip()

# Замена значения
df_work["channel_clean"] = df_work["channel"].str.replace("Online", "WEB")

# Заполнение пропусков в строковом столбце
df_work["client_filled"] = df_work["client"].fillna("Unknown")

# Проверка: как выглядят категории после очистки
print(df_work["client_clean"].value_counts(dropna=False))
```

>TIP: str.strip() перед value_counts
Перед `value_counts()` всегда делайте `str.strip()` — это объединит "Books" и "Books " в одну категорию. Для ещё большей надёжности добавьте `str.lower()` или `str.title()`, чтобы привести все варианты к одному регистру.

## 4.6. Фильтрация и сортировка с проверкой

Фильтрация выбирает строки по условию, сортировка меняет порядок. Обе операции не должны изменять сами значения, но влияют на индекс и порядок. После каждой фильтрации полезно проверять: сколько строк осталось, не потеряли ли мы что-то важное, как изменился диапазон значений.

```env=Jupyter Notebook
# Фильтрация
df_high = sales_df[sales_df["amount"] > 100]
df_moscow = sales_df[sales_df["region"] == "Moscow"]
df_combined = sales_df[(sales_df["amount"] > 100) & (sales_df["region"] == "Moscow")]

# Проверка
print("Было:", len(sales_df))
print("Осталось:", len(df_combined))
print("Доля:", len(df_combined) / len(sales_df))

# Сортировка
df_sorted = df_combined.sort_values("amount", ascending=False)

# Проверка сортировки
print("Максимум:", df_sorted["amount"].max())
print("Первое значение:", df_sorted["amount"].iloc[0])

# Сброс индекса после фильтрации
df_reset = df_sorted.reset_index(drop=True)
print(df_reset.head())
```

[[IMAGE:build/extra_illus/fig_filter.png:420]]

>NOTE: reset_index(drop=True)
После фильтрации индекс сохраняет "дыры" от удалённых строк. Часто удобнее сбросить индекс, чтобы он снова стал 0, 1, 2, ... `drop=True` отбрасывает старый индекс, а не добавляет его как столбец.

## 4.7. Поиск выбросов

Выбросы — значения, значительно открывающиеся от основной массы. Они могут быть как ошибками данных, так и реальными аномалиями. Для поиска используют IQR (межквартильный размах), z-оценку или простой порог по перцентилю. После нахождения нужно решить: удалить, заменить на границу, оставить с пометкой.

```env=Jupyter Notebook
# IQR-метод
q1 = df_work["amount"].quantile(0.25)
q3 = df_work["amount"].quantile(0.75)
iqr = q3 - q1
lower = q1 - 1.5 * iqr
upper = q3 + 1.5 * iqr

print(f"IQR границы: [{lower:.2f}, {upper:.2f}]")

# Маска выбросов
mask_outliers = (df_work["amount"] < lower) | (df_work["amount"] > upper)
print("Выбросов:", mask_outliers.sum())

# Удаление выбросов
df_no_outliers = df_work[~mask_outliers]

# Ограничение выбросов (clip)
df_clipped = df_work.copy()
df_clipped["amount"] = df_clipped["amount"].clip(lower=lower, upper=upper)

# Перцентильный порог (например, удалить верхние 1%)
threshold = df_work["amount"].quantile(0.99)
df_below_99 = df_work[df_work["amount"] <= threshold]
```

>WARN: Не удаляйте выбросы автоматически
Выброс — не всегда ошибка. В финансовых данных это могут быть крупные сделки, в логах — аномальные события. Сначала изучите природу выброса, потом решайте. Удаление всех "хвостов" может убрать из данных самую интересную часть.

[[IMAGE:build/extra_illus/illus_outliers.png:420]]

## 4.8. Объединение наборов данных

Объединение таблиц — ежедневная задача аналитика. Pandas предоставляет `merge()` (по ключам, как JOIN в SQL), `concat()` (по строкам или столбцам), `join()` (по индексу). Важно понимать тип соединения: `inner` (только совпадающие ключи), `outer` (все ключи), `left`/`right` (приоритет одной таблице).

[[IMAGE:build/extra_illus/fig_workflow.png:420]]

```env=Jupyter Notebook
# Создадим второй набор — справочник клиентов
clients_df = pd.DataFrame({
    "client": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
    "city": ["Moscow", "Saint Petersburg", "Kazan", "Novosibirsk", "Moscow"],
    "tier": ["Gold", "Silver", "Silver", "Bronze", "Gold"],
})

# merge по ключу
df_merged = df_work.merge(clients_df, on="client", how="left")

# merge по разным именам столбцов
df_merged2 = df_work.merge(
    clients_df.rename(columns={"client": "customer"}),
    left_on="client",
    right_on="customer",
    how="left",
)

# Проверка
print("Было:", df_work.shape, "Стало:", df_merged.shape)
print("Новые столбцы:", set(df_merged.columns) - set(df_work.columns))
print("Пропуски в новых столбцах:")
print(df_merged[["city", "tier"]].isna().sum())

# concat по строкам
df_more = pd.concat([sales_df, sales_df], ignore_index=True)
print("Дубликаты после concat:", df_more.duplicated().sum())

# concat по столбцам
df_side_by_side = pd.concat([sales_df.reset_index(drop=True), clients_df.head(len(sales_df))], axis=1)
```

>TIP: Проверяйте размер после merge
После `merge` число строк может неожиданно вырасти — если в правой таблице есть несколько записей с тем же ключом, произойдёт "размножение" строк левой. Всегда проверяйте `df.shape` до и после. Если число строк изменилось непредсказуемо — изучите дубликаты в ключах правой таблицы: `right_df["key"].value_counts()`.

## 4.9. Агрегации и groupby

`groupby` — основной инструмент агрегации в pandas. Группируем по одному или нескольким столбцам, применяем агрегатные функции. Полезные функции: `sum`, `mean`, `median`, `min`, `max`, `count`, `nunique`, `std`, `var`. `agg()` позволяет применить несколько функций сразу к разным столбцам.

```env=Jupyter Notebook
# Простая агрегация по одной колонке
df_work.groupby("region")["amount"].sum()

# Несколько функций к одному столбцу
df_work.groupby("region")["amount"].agg(["sum", "mean", "count"])

# Разные функции к разным столбцам
df_work.groupby("region").agg({
    "amount": ["sum", "mean"],
    "quantity": "sum",
    "order_id": "count",
})

# Группировка по нескольким столбцам
df_work.groupby(["region", "category"])["amount"].sum()

# Переименование результатов агрегации
df_work.groupby("region").agg(
    total_amount=("amount", "sum"),
    avg_amount=("amount", "mean"),
    n_orders=("order_id", "count"),
)

# reset_index после groupby — чтобы превратить индекс в столбцы
agg_result = df_work.groupby(["region", "category"], as_index=False)["amount"].sum()
```

>NOTE: as_index=False — группировка без индекса
По умолчанию `groupby` превращает группирующий столбец в индекс. Если вам нужен обычный DataFrame со столбцами, передайте `as_index=False` или вызовите `reset_index()` после. Это удобнее для дальнейшей фильтрации и визуализации.

## 4.10. Сводные таблицы

`pivot_table` — мощный инструмент перекрёстной агрегации. Создаёт матрицу: строки — одни категории, столбцы — другие, ячейки — агрегированные значения. Полезен для отчётов, табличной визуализации и быстрого сравнения групп.

```env=Jupyter Notebook
# Сводная таблица: регион × категория, сумма amount
pivot_sum = df_work.pivot_table(
    values="amount",
    index="region",
    columns="category",
    aggfunc="sum",
    fill_value=0,
)

# Несколько агрегатных функций
pivot_multi = df_work.pivot_table(
    values="amount",
    index="region",
    columns="category",
    aggfunc=["sum", "mean"],
)

# С margins — итоги по строкам и столбцам
pivot_margins = df_work.pivot_table(
    values="amount",
    index="region",
    columns="category",
    aggfunc="sum",
    margins=True,
    margins_name="Итого",
)

print(pivot_margins)
```

>TIP: pivot_table vs groupby
`pivot_table` удобен, когда нужен результат в виде "матрицы" для отчёта или тепловой карты. `groupby` лучше, когда результат пойдёт в дальнейший код или визуализацию через длинный формат. Внутренне они оба работают через groupby + unstack.

[[IMAGE:build/extra_illus/illus_pivot.png:420]]

## 4.11. transform: агрегация с сохранением формы

`transform` возвращает Series той же длины, что и исходный DataFrame. Это удобно, когда нужно добавить агрегированное значение обратно в каждую строку. Например, добавить средний чек по региону в каждую строку заказа.

[[IMAGE:build/extra_illus/illus_transform.png:420]]

```env=Jupyter Notebook
# Средний чек по региону в каждой строке
df_work["region_avg"] = df_work.groupby("region")["amount"].transform("mean")

# Доля суммы заказа от суммы по региону
df_work["share_of_region"] = df_work["amount"] / df_work.groupby("region")["amount"].transform("sum")

# Ранг по сумме внутри каждого региона
df_work["rank_in_region"] = df_work.groupby("region")["amount"].rank(
    method="dense", ascending=False
)

# Проверка
print(df_work[["order_id", "region", "amount", "region_avg", "share_of_region"]].head())
```

>NOTE: transform vs agg
`agg` возвращает сжатый результат — одну строку на группу. `transform` возвращает Series с тем же индексом и длиной, что и исходный DataFrame. Используйте `transform`, когда нужно добавить агрегат в каждую строку, и `agg`, когда нужен итог по группам.

## 4.12. value_counts как базовый аналитический инструмент

`value_counts()` — одна из самых часто используемых команд. Она считает частоты уникальных значений и возвращает Series, отсортированный по убыванию частоты. Подходит для быстрой проверки категорий, поиска редких значений, анализа распределений.

```env=Jupyter Notebook
# Базовый вызов
print(df_work["region"].value_counts())

# С долями
print(df_work["region"].value_counts(normalize=True).round(3))

# С пропусками
print(df_work["client"].value_counts(dropna=False))

# Топ-3
print(df_work["category"].value_counts().head(3))

# Без сортировки (в порядке появления значений)
print(df_work["region"].value_counts(sort=False))

# Бины для числового столбца
print(df_work["amount"].value_counts(bins=5))
```

>TIP: value_counts(bins=N) — быстрый гистограммный анализ
Параметр `bins=N` разбивает числовой столбец на N равных интервалов и считает число значений в каждом. Это быстрый способ увидеть распределение без построения графика: `df["amount"].value_counts(bins=10)`.
"""

SAFETY_CONTENT = r"""
# 5. Целостность и безопасность данных

Самая частая причина потери рабочих часов — не ошибка в коде, а незаметное изменение исходных данных. Аналитик открывает ноутбук на следующий день, повторно запускает ячейки и обнаруживает, что `df_raw` уже не тот. Поэтому в этом разделе мы разбираем дисциплину работы: исходный набор не трогаем, все изменения — в рабочей копии, промежуточные результаты сохраняем, контрольные суммы и размеры проверяем до и после каждого преобразования.

## 5.1. Дисциплина df_raw, df_work, df_clean

В этом материале мы договорились о трёх переменных. `df_raw` — то, что мы получили из источника (файла, базы, API). Его мы не меняем. `df_work` — рабочая копия, в которой выполняем очистку, преобразование, агрегацию. `df_clean` — финальный набор, который пойдёт в визуализацию и сохранение. Такая структура помогает вернуться к исходным данным в любой момент и сравнить результат с тем, что было.

```env=Jupyter Notebook
import pandas as pd

# df_raw — исходный набор, не трогаем
df_raw = sales_df.copy()
print("df_raw shape:", df_raw.shape)
print("df_raw dtypes:\n", df_raw.dtypes)

# df_work — рабочая копия для очистки
df_work = df_raw.copy()

# Любое изменение — на df_work
df_work["amount"] = df_work["amount"].fillna(df_work["amount"].median())
df_work = df_work.drop_duplicates()

# Проверка: df_raw не изменился
print("df_raw shape после очистки:", df_raw.shape)
print("df_work shape после очистки:", df_work.shape)

# df_clean — финальный набор для визуализации и сохранения
df_clean = df_work.copy()
```

>WARN: copy() — обязательно
Присваивание `df_work = df_raw` НЕ создаёт копию — это просто второе имя для того же объекта. Любое изменение `df_work` изменит и `df_raw`. Всегда используйте `df_raw.copy()` для создания рабочей версии. Если вы редактируете столбец и видите `SettingWithCopyWarning` — это сигнал, что что-то не так с копией.

## 5.2. Риски незаметного изменения

pandas во многих случаях возвращает представление (view), а не копию. Это значит, что изменение через одно имя может затронуть и другое. Особенно коварны следующие ситуации: выбор столбца через `df[["a"]]` возвращает копию, а `df["a"]` возвращает Series, который может быть view. Фильтрация `df[df["a"] > 0]` возвращает копию, но `df.loc[df["a"] > 0, "b"]` — может быть view на исходник.

```env=Jupyter Notebook
# Опасный пример: цепная индексация
# df_work[df_work["amount"] > 100]["amount"] = 999  # SettingWithCopyWarning

# Безопасно: loc
df_work.loc[df_work["amount"] > 100, "amount"] = 999

# Опасный пример: slice без .copy()
subset = df_work[df_work["region"] == "Moscow"]  # view, не копия
# subset["new_col"] = 1  # Warning!

# Безопасно: .copy() после фильтрации
subset = df_work[df_work["region"] == "Moscow"].copy()
subset["new_col"] = 1  # OK
```

>TIP: Правило копии после фильтрации
После любой фильтрации, которая возвращает DataFrame, всегда добавляйте `.copy()`, если планируете изменять результат. Это гарантированно создаёт новый объект, и вы не получите `SettingWithCopyWarning`. Накладные расходы по памяти — минимальные, а безопасность — существенная.

## 5.3. Контрольные итоги до и после преобразования

Перед любым "разрушающим" преобразованием (удаление строк, изменение типов, агрегация) полезно зафиксировать контрольные показатели: число строк, сумма ключевого числового столбца, число пропусков. После преобразования сравниваем. Если сумма изменилась на 30% — что-то пошло не так, хотя код не выдал ошибку.

```env=Jupyter Notebook
# Фиксация контрольных показателей
def snapshot(df: pd.DataFrame, name: str = "") -> dict:
    '''Снимок состояния DataFrame для последующего сравнения.'''
    return {
        "name": name,
        "rows": len(df),
        "cols": df.shape[1],
        "amount_sum": df["amount"].sum() if "amount" in df.columns else None,
        "amount_mean": df["amount"].mean() if "amount" in df.columns else None,
        "n_na_amount": df["amount"].isna().sum() if "amount" in df.columns else None,
    }

before = snapshot(df_work, "before")
print("Before:", before)

# Выполняем преобразование
df_work = df_work.dropna(subset=["amount"])
df_work = df_work.drop_duplicates()

after = snapshot(df_work, "after")
print("After:", after)

# Сравнение
print("Δ rows:", after["rows"] - before["rows"])
print("Δ amount_sum:", round(after["amount_sum"] - before["amount_sum"], 2))
print("Δ amount_mean:", round(after["amount_mean"] - before["amount_mean"], 2))
```

>NOTE: Что должно совпадать
При удалении дубликатов и пропусков строки исчезают, но сумма amount в оставшихся строках должна быть близка к исходной (уменьшится ровно на сумму удалённых строк). Если сумма упала сильно больше, чем число удалённых строк × среднее — где-то ошибка в логике.

[[IMAGE:build/extra_illus/illus_safety_check.png:420]]

## 5.4. Резервные копии и промежуточные срезы

Перед серьёзным шагом (объединение с другой таблицей, агрегация с потерей строк, перезапись столбца) полезно сделать промежуточную копию. Если что-то пойдёт не так, не придётся начинать сначала — достаточно вернуться к `df_work_backup`. Это особенно важно при работе в Jupyter, где ячейки можно запустить в любом порядке, и состояние переменных непредсказуемо.

```env=Jupyter Notebook
# Резервная копия перед опасным шагом
df_work_backup = df_work.copy()

# Опасный шаг: merge с другой таблицей
df_work = df_work.merge(clients_df, on="client", how="left")

# Проверка
print("До merge:", df_work_backup.shape)
print("После merge:", df_work.shape)

# Если что-то не так — откат
if df_work.shape[0] != df_work_backup.shape[0]:
    print("Размер изменился! Проверяю дубликаты в ключе.")
    print(clients_df["client"].value_counts().head())
    # Откат при необходимости:
    # df_work = df_work_backup.copy()
```

>TIP: Резервные копии в одну строку
Создавайте резервные копии систематически: `df_bak_1 = df.copy()` перед первым шагом, `df_bak_2 = df.copy()` перед вторым. Это дешёвая страховка — память освобождается, как только вы удаляете переменную через `del df_bak_1`.

[[IMAGE:build/extra_illus/illus_backup.png:420]]

## 5.5. Сохранение исходных данных в неизменном виде

Самая надёжная защита — физически хранить исходный файл в режиме "только для чтения" и никогда не перезаписывать его результатами. При сохранении результатов используйте другое имя файла, а не имя исходника. Для критичных данных можно сделать несколько поколений копий: `sales_v1.csv`, `sales_v2.csv`, и т.д.

```env=Jupyter Notebook
# Чтение исходника
df_raw = pd.read_csv("data/sales.csv")

# Сохранение результата — НИКОГДА не под тем же именем!
df_clean.to_csv("data/sales_clean.csv", index=False)

# С версионированием
from datetime import datetime
version = datetime.now().strftime("%Y%m%d_%H%M")
df_clean.to_csv(f"data/sales_clean_{version}.csv", index=False)

# Проверка: исходник не тронут
df_raw_again = pd.read_csv("data/sales.csv")
print("Исходник не изменился:", df_raw.equals(df_raw_again))
```

>WARN: Никогда не перезаписывайте исходный файл
`df_raw.to_csv("data/sales.csv")` перезапишет исходник. Если вы потом поймёте, что в очистке была ошибка — восстановить данные не получится. Сохраняйте результаты под другими именами: `sales_clean.csv`, `sales_processed.csv`, `sales_v2.csv`.

## 5.6. Проверка размеров, типов, пропусков — три уровня контроля

Контроль должен быть трёхуровневым: до (фиксируем исходное состояние), во время (после каждого важного шага), после (финальная проверка). Такой подход превращает "магию" в воспроизводимый процесс. Если что-то пойдёт не так, вы всегда сможете сказать, на каком шаге это произошло.

```env=Jupyter Notebook
def audit(df: pd.DataFrame, step_name: str) -> None:
    '''Контроль состояния DataFrame после шага.'''
    print(f"\n=== {step_name} ===")
    print(f"shape: {df.shape}")
    print(f"dtypes:\n{df.dtypes}")
    print(f"na sum:\n{df.isna().sum()}")
    print(f"memory (MB): {df.memory_usage(deep=True).sum() / 1e6:.2f}")

audit(df_raw, "Шаг 0: исходный")

df_work = df_raw.copy()
df_work["amount"] = df_work["amount"].fillna(df_work["amount"].median())
audit(df_work, "Шаг 1: заполнение пропусков в amount")

df_work = df_work.drop_duplicates()
audit(df_work, "Шаг 2: удаление дубликатов")

df_work = df_work.dropna(subset=["client"])
audit(df_work, "Шаг 3: удаление строк без клиента")
```

>NOTE: Аудит в виде функции
Функция `audit` — отличный кандидат на добавление в `utils.py`. Она выводит ключевую информацию за один вызов и экономит время на диагностике. Можно расширить её: добавить проверку уникальности ключей, диапазонов числовых столбцов, частот категорий.

## 5.7. Защита от потери типов и порядка

Несколько типичных "подводных камней" при экспорте и импорте. CSV не сохраняет типы — все данные становятся строками при чтении. После `to_csv()` и нового `read_csv()` числовой столбец может оказаться `object`. Excel сохраняет типы в ячейках, но `read_excel` иногда присваивает `object` вместо `int64`. Parquet сохраняет типы полностью — это его главное преимущество.

[[IMAGE:build/extra_illus/fig_safety.png:420]]

```env=Jupyter Notebook
# Сценарий: сохранили в CSV и прочитали обратно
df_work.to_csv("data/temp.csv", index=False)
df_back = pd.read_csv("data/temp.csv")

# Сравнение типов
print("Исходные типы:\n", df_work.dtypes)
print("После CSV round-trip:\n", df_back.dtypes)

# Parquet: типы сохраняются
df_work.to_parquet("data/temp.parquet")
df_back_pq = pd.read_parquet("data/temp.parquet")
print("После Parquet round-trip:\n", df_back_pq.dtypes)
print("Equal dtypes:", df_work.dtypes.equals(df_back_pq.dtypes))
```

>WARN: CSV round-trip меняет типы
Если в числовом столбце был `int64`, после `to_csv` + `read_csv` он может стать `int64` снова, если нет пропусков. Но если есть NaN — станет `float64`. И `datetime` после CSV всегда становится строкой. После чтения CSV обязательно повторно проверяйте типы и при необходимости приводите: `pd.to_datetime`, `pd.to_numeric`.

## 5.8. Контрольный пример: полный сценарий очистки

Соберём все принципы в один сквозной сценарий. Исходник — `df_raw`. Рабочая копия — `df_work`. Аудит — на каждом шаге. Финал — `df_clean`, который готов к визуализации и сохранению. Этот блок можно скопировать в реальный проект и адаптировать под свои столбцы.

```env=Jupyter Notebook
# 1. Исходник
df_raw = sales_df.copy()
audit(df_raw, "Шаг 0: исходный")

# 2. Рабочая копия
df_work = df_raw.copy()

# 3. Удаление дубликатов
df_work = df_work.drop_duplicates()
audit(df_work, "Шаг 1: drop_duplicates")

# 4. Заполнение пропусков
df_work["amount"] = df_work["amount"].fillna(df_work["amount"].median())
df_work["client"] = df_work["client"].fillna("Unknown")
df_work["quantity"] = df_work["quantity"].fillna(1).astype(int)
audit(df_work, "Шаг 2: fillna")

# 5. Преобразование даты
df_work["order_date"] = pd.to_datetime(df_work["order_date"])
audit(df_work, "Шаг 3: to_datetime")

# 6. Финальный набор
df_clean = df_work.copy()
audit(df_clean, "Шаг 4: df_clean")

print("\n=== ИТОГО ===")
print(f"Исходник: {df_raw.shape}, Чистый: {df_clean.shape}")
```

>TIP: Этот блок — шаблон для всех проектов
Скопируйте этот сценарий в свой проект, замените имена столбцов на свои — и вы получите воспроизводимую очистку с аудитом. Это особенно полезно, когда данные обновляются регулярно и нужно убедиться, что новая порция прошла все проверки.
"""
