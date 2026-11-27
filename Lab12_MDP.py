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
