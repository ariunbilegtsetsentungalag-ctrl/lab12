# %% [markdown]
# # Лаборатори 12: Ухаалаг шийдвэр — MDP ба утгын давталт

# %% [markdown]
# ## Алхам 1: Орчин бэлтгэх

# %%
import sys
import platform
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

print("Python:", sys.version.split()[0])
print("numpy:", np.__version__)
print("OS:", platform.platform())

# Шүхэр авах уу? Бороо орох магадлал 0.3
take = [(0.3, 70), (0.7, 80)]
leave = [(0.3, 0), (0.7, 100)]
eu = lambda outs: sum(p * u for p, u in outs)
print(eu(take), eu(leave))  # 77.0 70.0

# %% [markdown]
# ## Алхам 2: Хүлээгдэж буй ашиг


# %%
# Хүлээгдэж буй ашгийг EU = Σ P(o)·u(o) томьёогоор тооцно.
# Магадлалын нийлбэр 1 биш бол ValueError өгнө.
def expected_utility(outcomes):
    total = sum(p for p, _ in outcomes)
    if abs(total - 1.0) > 1e-9:
        raise ValueError(f"Магадлалын нийлбэр 1 биш: {total}")
    return sum(p * u for p, u in outcomes)


choices = {
    "Шалгалтад бэлдэх": [(0.9, 80), (0.1, 10)],
    "Тоглох": [(0.4, 100), (0.6, 0)],
    "А: шууд мөнгө": [(1.0, 100000)],
    "Б: зоос шидэх": [(0.5, 250000), (0.5, 0)],
}
for name, outs in choices.items():
    print(f"{name:20s} EU = {expected_utility(outs)}")

try:
    expected_utility([(0.5, 10), (0.4, 20)])
except ValueError as e:
    print("Шалгах:", e)
