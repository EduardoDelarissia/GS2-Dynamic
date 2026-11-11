# AlertaCidade · Dynamic Programming

> Global Solution FIAP 2026.2 · CitizenTech · Engenharia de Software
> Módulo Python de **rotas seguras durante alagamentos** e **plano de vistoria dos agentes comunitários**.

## Integrantes

| RM | Nome |
|---|---|
| `<PREENCHER>` | `<PREENCHER>` |
| `<PREENCHER>` | `<PREENCHER>` |
| `<PREENCHER>` | `<PREENCHER>` |

Equipe: `<PREENCHER>` · Cidade/bairro: `<PREENCHER>`

## Problema

Quando a água sobe, o morador precisa saber **por onde sair** e **para qual abrigo ir**. O caminho mais curto com a rua seca pode passar justamente pela baixada alagada. Enquanto isso, o agente comunitário tem um turno limitado e precisa decidir **quais pontos de risco vistoriar primeiro**.

O AlertaCidade já mede o nível de água em pontos de monitoramento (API Java + Oracle). Este módulo usa essas leituras para:

1. **Rota segura**: menor tempo de caminhada entre dois cruzamentos, evitando trechos em estado CRÍTICO e penalizando os trechos em ATENÇÃO.
2. **Abrigo mais próximo**: abrigo alcançável no menor tempo a partir de onde o cidadão está.
3. **Plano de vistoria**: quais pontos o agente visita em um turno de *T* minutos para cobrir a maior prioridade possível.

## Modelagem

**Grafo de ruas** (não direcionado, ponderado), em lista de adjacência `dict[str, list[Trecho]]`:

- vértice = cruzamento (ex.: `C14 – Conjunto Habitacional`);
- aresta = trecho de rua, com peso = tempo de caminhada com a rua seca (min);
- alguns trechos estão ligados a um **ponto de monitoramento** (`PT-01`…`PT-05`).

O nível lido em cada ponto é classificado com a **mesma regra da API Java** (cotas de demonstração):

| Nível | Estado | Efeito no trecho |
|---|---|---|
| < 50 cm | NORMAL | custo × 1,0 |
| 50 – 89 cm | ATENÇÃO | custo × 1,8 (deslocamento mais lento) |
| ≥ 90 cm | CRÍTICO | trecho removido (intransitável) |

**Vistoria (mochila 0/1)**: cada ponto *i* tem tempo `t_i` (ida + inspeção) e prioridade `p_i = peso_do_estado × (1 + moradores_expostos/100)`, com peso 1 / 5 / 10 para NORMAL / ATENÇÃO / CRÍTICO.

## Algoritmos

| Problema | Força bruta (baseline) | Programação dinâmica | Guloso |
|---|---|---|---|
| Rota segura | backtracking em todos os caminhos simples, O(V!) | **Bellman-Ford**, `dp[k][v]` = menor custo até *v* com ≤ *k* trechos, O(V·E) | **Dijkstra** com heap, O((V+E) log V) |
| Vistoria | todos os 2ⁿ subconjuntos, O(2ⁿ·n) | **Mochila 0/1**, `dp[i][c] = max(dp[i-1][c], dp[i-1][c-tᵢ] + pᵢ)`, O(n·T) | razão prioridade/minuto, O(n log n) |

Nas rotas, as três abordagens devolvem sempre o mesmo custo (testado em 25 grafos aleatórios); Dijkstra é o usado em produção por ser o mais rápido. Na vistoria, **o guloso pode errar**, e a PD garante o ótimo. Detalhes e provas de corretude em [`docs/complexidade.md`](docs/complexidade.md).

## Resultado no bairro de demonstração

Do Conjunto Habitacional (C14) até a Escola Municipal (C02):

| Cenário | Pontos críticos | Rota | Tempo |
|---|---|---|---|
| Seco | nenhum | C14 → Av. do Córrego (B) → Av. do Córrego (A) → Praça → Escola | 13,0 min |
| Chuva moderada | nenhum (PT-01 e PT-03 em atenção) | mesma rota, mais lenta | 16,2 min |
| Chuva forte | PT-01, PT-02, PT-05 | C14 → Rua Alta → Rua das Palmeiras → Mercado → Praça → Escola | 20,0 min |

Com chuva forte, o abrigo mais rápido passa a ser o **Ginásio** (15 min, pela Rua Alta).

Plano de vistoria com chuva forte e turno de 60 min:

| Algoritmo | Pontos | Prioridade |
|---|---|---|
| Programação dinâmica | PT-01, PT-04, PT-05 | **67** |
| Força bruta | PT-01, PT-04, PT-05 | 67 |
| Guloso | PT-01, PT-02, PT-04 | 51 (24% a menos, deixa a margem do córrego sem vistoria) |

## Desempenho

`python desempenho.py` gera os CSVs e os gráficos em `docs/`.

![Rotas](docs/grafico_rotas.png)

- A força bruta passa de 49 operações (N=8) para 7.573 (N=12) e fica impraticável logo depois.
- Dijkstra faz cerca de 12× menos operações que Bellman-Ford com N=500.

![Vistoria](docs/grafico_vistoria.png)

- Força bruta: 213 ms com 18 pontos (2¹⁸ subconjuntos). A PD resolve 200 pontos em ~4 ms.
- O guloso é ~100× mais rápido que a PD, mas perde até 2,4% da prioridade nos testes aleatórios (e 24% no cenário do bairro).

## Como executar

Requer Python 3.10+. Sem dependências para o módulo; `pytest` e `matplotlib` para testes e gráficos.

```bash
pip install -r requirements.txt

python -m rotas demo                                              # todos os cenários
python -m rotas rota    --origem C14 --destino C02 --cenario chuva_forte
python -m rotas abrigo  --origem C14 --cenario chuva_moderada
python -m rotas vistoria --turno 60 --cenario chuva_forte

python -m pytest -q          # 74 testes
python desempenho.py         # CSVs + gráficos em docs/
```

### Usando os níveis reais da API Java

Com a API do AlertaCidade rodando, informe a URL e o id de cada ponto na API. O módulo lê `GET /api/pontos/{id}/status` e, se a API estiver fora do ar, volta para o cenário local:

```bash
python -m rotas rota --origem C14 --destino C02 --api http://localhost:8080 --ids PT-01=1,PT-02=2,PT-03=3
```

### Trocando o bairro

Edite `data/bairro_demo.json` (cruzamentos, trechos, abrigos, pontos e cenários) ou passe outro arquivo com `--dados meu_bairro.json`.

## Estrutura

```
dynamic-programming/
├── rotas/
│   ├── grafo.py        # Grafo, Trecho, classificação e ponderação por nível
│   ├── caminhos.py     # força bruta, Bellman-Ford (PD), Dijkstra, abrigo mais próximo
│   ├── vistorias.py    # mochila 0/1 (PD), guloso, força bruta
│   ├── cenarios.py     # carga do JSON e gerador de grafos aleatórios
│   ├── api.py          # leitura opcional da API Java
│   └── __main__.py     # linha de comando
├── data/bairro_demo.json
├── tests/test_rotas.py
├── desempenho.py
├── docs/               # complexidade.md, CSVs e gráficos
└── IA_USO.md
```

## Limitações

- Bairro, tempos de caminhada e níveis são **fictícios/simulados**. As cotas de 50 e 90 cm são de demonstração, não limites oficiais.
- Ruas de mão dupla, e um único ponto de monitoramento por trecho.
- Na vistoria, o tempo de cada ponto já inclui o deslocamento estimado (não é resolvido um roteiro entre os pontos).
- Protótipo acadêmico: em emergência real, siga a Defesa Civil (199).

## ODS

11 (Cidades e comunidades sustentáveis) · 13 (Ação contra a mudança global do clima) · 9 (Indústria, inovação e infraestrutura)
