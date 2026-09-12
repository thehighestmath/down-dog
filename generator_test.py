import pandas as pd

df = pd.read_excel("Pose.xlsx").copy()


def time_realize_warm(t_max, s=None):
    if s is None:
        s = []

    name = df.loc[
        df["Сложность (1-4)"] < 3,
        "Название"
    ].sample().iloc[0]

    value = df.loc[
        df["Название"] == name,
        "Полный цикл, сек"
    ].iloc[0]

    if value <= t_max:
        s.append(name)
        t_max -= value
        return time_realize_warm(t_max, s)
    else:
        return s


def time_realize_mid(t_max, s=None):
    if s is None:
        s = []

    name = df.loc[
        (df["Сложность (1-4)"] >= 3) &
        (df["Сложность (1-4)"] < 4),
        "Название"
    ].sample().iloc[0]

    value = df.loc[
        df["Название"] == name,
        "Полный цикл, сек"
    ].iloc[0]

    if value <= t_max:
        s.append(name)
        t_max -= value
        return time_realize_mid(t_max, s)
    else:
        return s


def time_realize_hard(t_max, s=None):
    if s is None:
        s = []

    name = df.loc[
        df["Сложность (1-4)"] > 3,
        "Название"
    ].sample().iloc[0]

    value = df.loc[
        df["Название"] == name,
        "Полный цикл, сек"
    ].iloc[0]

    if value <= t_max:
        s.append(name)
        t_max -= value
        return time_realize_hard(t_max, s)
    else:
        return s


def tren(complexity, time):
    if complexity == "beginner":
        return time_realize_warm(time)

    elif complexity == "intermediate":
        s = []
        s.extend(time_realize_warm(time // 3))
        s.extend(time_realize_mid(time * 2 // 3))
        return s

    elif complexity == "hard":
        s = []
        s.extend(time_realize_hard(time // 5))
        s.extend(time_realize_mid(time * 3 // 5))
        s.extend(time_realize_hard(time // 5))
        return s
    else:
        return print("Ошибка")