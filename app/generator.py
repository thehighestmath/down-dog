def get_poses_by_focus(df, focus):

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


def time_realize_warm(t_max, poses):

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


def time_realize_mid(t_max, poses):

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


def time_realize_hard(t_max, poses):

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


def tren(df, level, duration, focus=None):

    poses = get_poses_by_focus(df, focus)

    if poses.empty:
        return []

    if level == "beginner":

        return time_realize_warm(
            duration,
            poses
        )

    elif level == "intermediate":

        result = []

        result.extend(
            time_realize_warm(
                duration // 3,
                poses
            )
        )

        result.extend(
            time_realize_mid(
                duration * 2 // 3,
                poses
            )
        )

        return result

    elif level == "advanced":

        result = []

        result.extend(
            time_realize_hard(
                duration // 5,
                poses
            )
        )

        result.extend(
            time_realize_mid(
                duration * 3 // 5,
                poses
            )
        )

        result.extend(
            time_realize_hard(
                duration // 5,
                poses
            )
        )

        return result

    return []