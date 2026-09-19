import pytest
import pandas as pd
from app.generator import tren


def test_tren_beginner_generates_poses():
    data = {
        "Название": ["Поза Собака", "Поза Кошка", "Сложная Поза"],
        "Сложность (1-4)": [1, 2, 4],
        "Полный цикл, сек": [30, 30, 30],
        "Фокус (группы мышц)": ["спина", "спина", "шея"]
    }
    df = pd.DataFrame(data)

    result = tren(df, level="beginner", duration=60, focus="back")

    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0] in ["Поза Собака", "Поза Кошка"]
