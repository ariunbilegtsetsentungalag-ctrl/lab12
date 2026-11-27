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

# %% [markdown]
# ## Алхам 3: Тор ертөнцийг тодорхойлох

# %%
W, H = 4, 3
WALL = {(2, 2)}
TERMINALS = {(4, 3): 1.0, (4, 2): -1.0}
STATES = [(x, y) for x in range(1, W + 1) for y in range(1, H + 1) if (x, y) not in WALL]
ACTIONS = {"^": (0, 1), "v": (0, -1), "<": (-1, 0), ">": (1, 0)}
SIDE = {"^": ("<", ">"), "v": ("<", ">"), "<": ("^", "v"), ">": ("^", "v")}
ARROW = {"^": "↑", "v": "↓", "<": "←", ">": "→"}
print("Төлөвийн тоо:", len(STATES))  # 11

# %% [markdown]
# ## Алхам 4: Хөдөлгөөн ба шилжилт


# %%
# s нүднээс a чиглэлд нэг алхам. Хана эсвэл захад мөргөвөл байрандаа үлдэнэ.
def move(s, a):
    dx, dy = ACTIONS[a]
    nx, ny = s[0] + dx, s[1] + dy
    if not (1 <= nx <= W and 1 <= ny <= H) or (nx, ny) in WALL:
        return s
    return (nx, ny)


SLIPPERY = True


# (магадлал, дараагийн төлөв) хосын жагсаалт: үндсэн чиглэл 0.8, хажуу 0.1, 0.1.
def trans(s, a):
    if not SLIPPERY:
        return [(1.0, move(s, a))]
    l, r = SIDE[a]
    return [(0.8, move(s, a)), (0.1, move(s, l)), (0.1, move(s, r))]


print(trans((1, 1), "^"))  # [(0.8,(1,2)), (0.1,(1,1)), (0.1,(2,1))]
print(trans((3, 2), ">"))

# %% [markdown]
# ## Алхам 5: Утгын давталт


# %%
# Беллманы шинэчлэлийг delta < eps болтол давтана. history-д U(1,1)-ийг хадгална.
def value_iteration(r=-0.04, gamma=1.0, eps=1e-6, max_iter=10000):
    U = {s: 0.0 for s in STATES}
    history = []
    for it in range(1, max_iter + 1):
        U2 = {}
        for s in STATES:
            if s in TERMINALS:
                U2[s] = TERMINALS[s]
            else:
                U2[s] = r + gamma * max(sum(p * U[s2] for p, s2 in trans(s, a)) for a in ACTIONS)
        delta = max(abs(U2[s] - U[s]) for s in STATES)
        U = U2
        history.append(U[(1, 1)])
        if delta < eps:
            break
    return U, it, history


def print_values(U):
    for y in range(H, 0, -1):
        row = []
        for x in range(1, W + 1):
            row.append("  ###" if (x, y) in WALL else f"{U[(x, y)]:5.2f}")
        print(" ".join(row))


U, iters, history = value_iteration()
print("Давталт:", iters, " U(1,1) =", round(U[(1, 1)], 3))
print_values(U)
