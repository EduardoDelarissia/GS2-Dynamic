"""
Mede tempo e operacoes de cada algoritmo para tamanhos crescentes de entrada.
Gera docs/desempenho_rotas.csv, docs/desempenho_vistoria.csv e graficos PNG.

    python desempenho.py
"""
from __future__ import annotations

import csv
import random
import statistics
import time
from pathlib import Path

from rotas import caminhos, vistorias
from rotas.cenarios import grafo_aleatorio
from rotas.vistorias import PontoVistoria

SAIDA = Path(__file__).parent / "docs"
LIMITE_FB_ROTAS = 12        # acima disso o backtracking fica impraticavel
LIMITE_FB_VISTORIA = 18     # 2^18 = 262 mil subconjuntos


def cronometrar(f, *a, repeticoes=3):
    tempos, res = [], None
    for _ in range(repeticoes):
        t0 = time.perf_counter()
        res = f(*a)
        tempos.append((time.perf_counter() - t0) * 1000)
    return statistics.median(tempos), res


def bench_rotas():
    linhas = []
    for n in (5, 8, 10, 12, 20, 50, 100, 200, 500):
        g, niveis = grafo_aleatorio(n, densidade=min(0.3, 6 / n), semente=n)
        gp = g.pesos_com_niveis(niveis)
        o, d = "V0", f"V{n - 1}"
        algs = [caminhos.dijkstra, caminhos.bellman_ford]
        if n <= LIMITE_FB_ROTAS:
            algs.append(caminhos.forca_bruta)
        for alg in algs:
            ms, r = cronometrar(alg, gp, o, d)
            linhas.append({"n_cruzamentos": n, "arestas": g.num_arestas(), "algoritmo": r.algoritmo,
                           "tempo_ms": round(ms, 4), "operacoes": r.operacoes,
                           "custo_min": round(r.custo, 2)})
    return linhas


def bench_vistoria():
    linhas = []
    turno = 240
    for n in (5, 10, 14, 18, 25, 50, 100, 200):
        rnd = random.Random(n)
        pontos = [PontoVistoria(f"P{i}", rnd.randint(5, 45), rnd.randint(1, 40)) for i in range(n)]
        algs = [vistorias.programacao_dinamica, vistorias.guloso]
        if n <= LIMITE_FB_VISTORIA:
            algs.append(vistorias.forca_bruta)
        otimo = None
        for alg in algs:
            ms, pl = cronometrar(alg, pontos, turno)
            if pl.algoritmo == "programacao_dinamica":
                otimo = pl.prioridade
            gap = 100 * (otimo - pl.prioridade) / otimo if otimo else 0.0
            linhas.append({"n_pontos": n, "turno_min": turno, "algoritmo": pl.algoritmo,
                           "tempo_ms": round(ms, 4), "operacoes": pl.operacoes,
                           "prioridade": pl.prioridade, "gap_vs_otimo_pct": round(gap, 2)})
    return linhas


def salvar_csv(linhas, nome):
    with open(SAIDA / nome, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas[0]))
        w.writeheader()
        w.writerows(linhas)


def graficos(rotas, vist):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    cores = {"dijkstra": "#2a78d6", "bellman_ford": "#e08a1e", "forca_bruta": "#c0392b",
             "programacao_dinamica": "#2a78d6", "guloso": "#27a35a"}
    nomes = {"dijkstra": "Dijkstra (guloso + heap)", "bellman_ford": "Bellman-Ford (PD)",
             "forca_bruta": "Força bruta", "programacao_dinamica": "Mochila 0/1 (PD)",
             "guloso": "Guloso (prioridade/min)"}

    def serie(linhas, alg, x, y):
        pts = [(l[x], l[y]) for l in linhas if l["algoritmo"] == alg]
        return [p[0] for p in pts], [p[1] for p in pts]

    fig, ax = plt.subplots(figsize=(8, 4.8))
    for alg in ("forca_bruta", "bellman_ford", "dijkstra"):
        xs, ys = serie(rotas, alg, "n_cruzamentos", "operacoes")
        ax.plot(xs, ys, marker="o", lw=2, color=cores[alg], label=nomes[alg])
    ax.set(xscale="log", yscale="log", xlabel="Cruzamentos no grafo (N)",
           ylabel="Operações elementares (log)",
           title="Rota segura: custo de cada algoritmo conforme o bairro cresce")
    ax.grid(True, which="both", alpha=0.25)
    ax.legend(frameon=False)
    fig.text(0.01, 0.01, "Força bruta medida só até N=12. Todos os algoritmos devolvem o mesmo custo mínimo.",
             fontsize=8, color="#555")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(SAIDA / "grafico_rotas.png", dpi=150)
    plt.close(fig)

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(11, 4.6))
    for alg in ("forca_bruta", "programacao_dinamica", "guloso"):
        xs, ys = serie(vist, alg, "n_pontos", "tempo_ms")
        a1.plot(xs, ys, marker="o", lw=2, color=cores[alg], label=nomes[alg])
    a1.set(yscale="log", xlabel="Pontos de monitoramento (n)", ylabel="Tempo (ms, log)",
           title="Plano de vistoria: tempo de execução")
    a1.grid(True, which="both", alpha=0.25)
    a1.legend(frameon=False)
    xs, ys = serie(vist, "guloso", "n_pontos", "gap_vs_otimo_pct")
    a2.bar([str(x) for x in xs], ys, color=cores["guloso"])
    a2.set(xlabel="Pontos de monitoramento (n)", ylabel="Prioridade perdida vs. ótimo (%)",
           title="Quanto o guloso perde em relação à PD")
    a2.grid(True, axis="y", alpha=0.25)
    fig.text(0.01, 0.01, "Turno de 240 min; prioridades e tempos sorteados (semente = n).",
             fontsize=8, color="#555")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(SAIDA / "grafico_vistoria.png", dpi=150)
    plt.close(fig)


if __name__ == "__main__":
    SAIDA.mkdir(exist_ok=True)
    r, v = bench_rotas(), bench_vistoria()
    salvar_csv(r, "desempenho_rotas.csv")
    salvar_csv(v, "desempenho_vistoria.csv")
    try:
        graficos(r, v)
    except ImportError:
        print("matplotlib nao instalado: graficos nao gerados (CSV salvos).")
    for l in r:
        print(l)
    for l in v:
        print(l)
