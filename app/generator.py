from typing import List, Optional

import pandas as pd


def get_poses_by_focus(df: pd.DataFrame,
                       focus: Optional[str],
                       ) -> pd.DataFrame:
    if focus is None or focus == "full_body":
        return df

    focus_map = {
        "back": [
            "спина",
            "поясница",
            "верхняя часть спины"
        ],
        "neck": [
            "шея"
        ],
        "legs": [
            "ноги",
            "ягодицы",
            "квадрицепсы",
            "икры",
            "задняя поверхность бедра"
        ],
        "relaxation": [
            "расслабление"
        ]
    }

    search_words = focus_map.get(focus)

    if search_words is None:
        return df

    selected_rows = []

    for index, row in df.iterrows():

        muscle_groups = str(
            row["Фокус (группы мышц)"]
        ).lower()

        for word in search_words:

            if word.lower() in muscle_groups:
                selected_rows.append(index)
                break

    return df.loc[selected_rows]


def time_realize_warm(
        t_max: int,
        poses: pd.DataFrame,
) -> List[str]:
    result = []

    while t_max > 0 and not poses.empty:

        possible = poses[
            poses["Сложность (1-4)"] <= 2
            ]

        if possible.empty:
            break

        pose = possible.sample().iloc[0]

        name = pose["Название"]
        value = pose["Полный цикл, сек"]

        if value <= t_max:
            result.append(name)
            t_max -= value
        else:
            break

    return result


def time_realize_mid(
        t_max: int,
        poses: pd.DataFrame,
) -> List[str]:
    result = []

    while t_max > 0 and not poses.empty:

        possible = poses[
            poses["Сложность (1-4)"] == 3
            ]

        if possible.empty:
            break

        pose = possible.sample().iloc[0]

        name = pose["Название"]
        value = pose["Полный цикл, сек"]

        if value <= t_max:
            result.append(name)
            t_max -= value
        else:
            break

    return result


def time_realize_hard(
        t_max: int,
        poses: pd.DataFrame,
) -> List[str]:
    result = []

    while t_max > 0 and not poses.empty:

        possible = poses[
            poses["Сложность (1-4)"] >= 4
            ]

        if possible.empty:
            break

        pose = possible.sample().iloc[0]

        name = pose["Название"]
        value = pose["Полный цикл, сек"]

        if value <= t_max:
            result.append(name)
            t_max -= value
        else:
            break

    return result


def tren(
        df: pd.DataFrame,
        level: str,
        duration: int,
        focus: Optional[str] = None,
) -> List[str]:
    poses = get_poses_by_focus(df, focus)
    if poses.empty:
        return []

    plans = {
        "beginner": [
            (time_realize_warm, 1, 1),
        ],
        "intermediate": [
            (time_realize_warm, 1, 3),
            (time_realize_mid, 2, 3),
        ],
        "advanced": [
            (time_realize_hard, 1, 5),
            (time_realize_mid, 3, 5),
            (time_realize_hard, 1, 5),
        ],
    }

    result = []
    for func, num, den in plans.get(level, []):
        result.extend(func(duration * num // den, poses))

    return result
