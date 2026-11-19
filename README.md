# 🚨 AlertaCidade · Dynamic Programming

> **Global Solution FIAP 2026.2 · CitizenTech · Engenharia de Software**  
> Módulo Python de **rotas seguras durante alagamentos** e **planejamento de vistorias de agentes comunitários**.

## 📋 Ficha CitizenTech — base comum da equipe

| Campo | Informação |
|---|---|
| **Nome da CitizenTech** | AlertaCidade |
| **Cidade e bairro** | Bela Vista |
| **Cidadão beneficiado** | Moradores de áreas sujeitas a alagamentos, especialmente quem precisa alcançar um abrigo; agentes comunitários responsáveis por vistorias |
| **Problema, em uma frase** | Durante alagamentos, moradores precisam encontrar rotas seguras e agentes precisam priorizar vistorias com tempo limitado. |
| **Como funciona** | Leituras de nível de água classificam trechos como normais, em atenção ou críticos; algoritmos calculam rotas, abrigos alcançáveis e prioridades de vistoria. |
| **O que cada parte faz** | **Java + Oracle:** cadastro e consulta de monitoramento e alertas. **Python / Dynamic Programming:** cálculo de rotas e seleção de vistorias. **Render:** hospedagem do backend Java. |
| **Link do repositório** | [GitHub — AlertaCidade](https://github.com/EduardoDelarissia/alertacidade) |
| **Indicador de impacto** | Tempo estimado de deslocamento até abrigo e prioridade total atendida por turno de vistoria, comparando cenários simulados. |
| **ODS conectados** | **ODS 11** — Cidades e comunidades sustentáveis; **ODS 13** — Ação contra a mudança global do clima; **ODS 9** — Indústria, inovação e infraestrutura. |

> **Nota:** cidade/bairro reais ainda precisam ser definidos. Os indicadores acima são métricas do protótipo, não resultados de implantação em campo.

## 👥 Integrantes

| RM | Nome |
|---|---|
| 563468 | Eduardo Antonio Delarissia |

**Equipe:** a completar, caso haja outros integrantes.  
**Cidade/bairro do projeto:** a definir.

## 🌐 Integração com o AlertaCidade

O módulo de Dynamic Programming complementa a API Java com Spring Boot e banco Oracle FIAP. A integração **Java ↔ Oracle** já foi demonstrada com requisição POST, resposta HTTP `201 Created` e consulta SQL do alerta ID 16. A leitura de níveis da API pelo **módulo Python** é opcional e deve ser validada separadamente, com os endpoints e identificadores efetivamente disponíveis.

- **Backend publicado no Render:** https://alertacidade.onrender.com
- **Consulta de alertas:** https://alertacidade.onrender.com/api/alertas
- **Documentação Swagger (quando habilitada):** https://alertacidade.onrender.com/swagger-ui.html

> O endereço raiz do backend pode retornar `404`, pois não há necessariamente uma rota `/`. Para testar, use um endpoint existente, como `/api/alertas`. A instância gratuita do Render pode demorar para responder após um período de inatividade.

## ❗ Problema

Quando a água sobe, o morador precisa saber **por onde sair** e **para qual abrigo ir**. O caminho mais curto com a rua seca pode passar justamente pela baixada alagada. Enquanto isso, o agente comunitário tem um turno limitado e precisa decidir **quais pontos de risco vistoriar primeiro**.

O AlertaCidade já registra dados de monitoramento e alertas (API Java + Oracle). Este módulo usa níveis de água fornecidos por cenários simulados ou, opcionalmente, por uma API compatível para:

1. **Rota segura:** menor tempo de caminhada entre dois cruzamentos, evitando trechos em estado CRÍTICO e penalizando trechos em ATENÇÃO.
2. **Abrigo mais próximo:** abrigo alcançável no menor tempo a partir da posição do cidadão.
3. **Plano de vistoria:** seleção de pontos a visitar em um turno de *T* minutos para maximizar a prioridade atendida.

## 🧩 Modelagem

**Grafo de ruas** (não direcionado, ponderado), representado como lista de adjacência `dict[str, list[Trecho]]`:

- **Vértice:** cruzamento (ex.: `C14 – Conjunto Habitacional`).
- **Aresta:** trecho de rua, com peso igual ao tempo de caminhada com a rua seca, em minutos.
- Alguns trechos estão ligados a um **ponto de monitoramento** (`PT-01` a `PT-05`).

O nível de água é classificado com as seguintes **cotas de demonstração do módulo**:

| Nível | Estado | Efeito no trecho |
|---|---|---|
| < 50 cm | NORMAL | custo × 1,0 |
| 50–89 cm | ATENÇÃO | custo × 1,8 (deslocamento mais lento) |
| ≥ 90 cm | CRÍTICO | trecho removido (intransitável) |

> Essas cotas são simuladas. A equivalência com regras e limites efetivamente implementados na API Java deve ser conferida no código antes de afirmar que ambos usam a mesma classificação.

**Vistoria (mochila 0/1):** cada ponto *i* tem tempo `t_i` (ida + inspeção) e prioridade `p_i = peso_do_estado × (1 + moradores_expostos/100)`, com pesos 1, 5 e 10 para NORMAL, ATENÇÃO e CRÍTICO.

## 🧠 Algoritmos

| Problema | Força bruta (baseline) | Programação dinâmica | Guloso |
|---|---|---|---|
| Rota segura | Backtracking em caminhos simples; custo exponencial/fatorial no pior caso | **Bellman-Ford**, `dp[k][v]` = menor custo até *v* com até *k* trechos, `O(V·E)` | **Dijkstra** com heap, `O((V+E) log V)` |
| Vistoria | Todos os `2ⁿ` subconjuntos, `O(2ⁿ·n)` | **Mochila 0/1**, `dp[i][c] = max(dp[i-1][c], dp[i-1][c-tᵢ] + pᵢ)`, `O(n·T)` | Razão prioridade/minuto, `O(n log n)` |

Nos testes descritos no projeto, as três abordagens de rota retornaram o mesmo custo em 25 grafos aleatórios; Dijkstra é a alternativa preferida para custos não negativos. Na vistoria, **o guloso pode não alcançar o ótimo**, enquanto a programação dinâmica encontra a solução ótima para o modelo de mochila definido.

Detalhes e provas de corretude: [`docs/complexidade.md`](docs/complexidade.md).

## 🏘️ Resultado no bairro de demonstração

Do Conjunto Habitacional (`C14`) até a Escola Municipal (`C02`):

| Cenário | Pontos críticos | Rota | Tempo |
|---|---|---|---|
| Seco | Nenhum | C14 → Av. do Córrego (B) → Av. do Córrego (A) → Praça → Escola | 13,0 min |
| Chuva moderada | Nenhum (PT-01 e PT-03 em atenção) | Mesma rota, mais lenta | 16,2 min |
| Chuva forte | PT-01, PT-02, PT-05 | C14 → Rua Alta → Rua das Palmeiras → Mercado → Praça → Escola | 20,0 min |

Com chuva forte, o abrigo mais rápido passa a ser o **Ginásio** (15 min, pela Rua Alta).

**Plano de vistoria com chuva forte e turno de 60 min:**

| Algoritmo | Pontos | Prioridade |
|---|---|---|
| Programação dinâmica | PT-01, PT-04, PT-05 | **67** |
| Força bruta | PT-01, PT-04, PT-05 | 67 |
| Guloso | PT-01, PT-02, PT-04 | 51 (aprox. 24% a menos) |

Esses resultados correspondem ao **cenário fictício de demonstração**, não a uma rota certificada para uso em emergências reais.

## 📈 Desempenho

`python desempenho.py` gera CSVs e gráficos em `docs/`.

![Gráfico de rotas](docs/grafico_rotas.png)

- A força bruta passa de 49 operações (`N=8`) para 7.573 (`N=12`) nos experimentos descritos.
- Dijkstra executa cerca de 12× menos operações que Bellman-Ford com `N=500`, no benchmark informado.

![Gráfico de vistoria](docs/grafico_vistoria.png)

- Força bruta: 213 ms com 18 pontos (`2¹⁸` subconjuntos); PD: aproximadamente 4 ms com 200 pontos, nas condições do teste informado.
- O guloso é aproximadamente 100× mais rápido que a PD, mas pode perder qualidade: até 2,4% nos testes aleatórios citados e cerca de 24% no cenário demonstrativo.

> Tempos e contagens são resultados reportados no projeto; podem variar conforme hardware, ambiente e dados utilizados.

## ▶️ Como executar

**Requisitos:** Python 3.10+. O módulo principal não exige dependências externas; `pytest` e `matplotlib` são usados nos testes e gráficos.

```bash
pip install -r requirements.txt

python -m rotas demo
python -m rotas rota --origem C14 --destino C02 --cenario chuva_forte
python -m rotas abrigo --origem C14 --cenario chuva_moderada
python -m rotas vistoria --turno 60 --cenario chuva_forte

python -m pytest -q
python desempenho.py
```

O projeto relata **74 testes**; execute o comando acima para verificar o resultado no seu ambiente.

### Usando níveis da API Java

Quando a API disponibilizar a rota esperada `GET /api/pontos/{id}/status`, informe a URL e o ID de cada ponto. Se a API estiver indisponível, o módulo foi projetado para retornar ao cenário local.

```bash
python -m rotas rota --origem C14 --destino C02 --api http://localhost:8080 --ids PT-01=1,PT-02=2,PT-03=3
```

Para apontar ao deploy, substitua `http://localhost:8080` por `https://alertacidade.onrender.com`, **desde que o endpoint de status e os IDs sejam compatíveis**. A existência dessa rota específica não foi comprovada pelos testes de `/api/alertas`.

### Trocando o bairro

Edite `data/bairro_demo.json` (cruzamentos, trechos, abrigos, pontos e cenários) ou use outro arquivo com `--dados meu_bairro.json`.

## 📁 Estrutura

```text
dynamic-programming/
├── rotas/
│   ├── grafo.py        # Grafo, Trecho, classificação e ponderação por nível
│   ├── caminhos.py     # Força bruta, Bellman-Ford, Dijkstra e abrigos
│   ├── vistorias.py    # Mochila 0/1, guloso e força bruta
│   ├── cenarios.py     # Carga do JSON e grafos aleatórios
│   ├── api.py          # Leitura opcional da API Java
│   └── __main__.py     # Linha de comando
├── data/bairro_demo.json
├── tests/test_rotas.py
├── desempenho.py
├── docs/               # complexidade.md, CSVs e gráficos
└── IA_USO.md
```

## ⚠️ Limitações e segurança

- Bairro, tempos de caminhada e níveis são **fictícios/simulados**; as cotas de 50 e 90 cm não são limites oficiais de segurança.
- O grafo representa ruas de mão dupla e admite um único ponto de monitoramento por trecho.
- Na vistoria, o tempo de cada ponto já inclui deslocamento estimado; não é otimizado o roteiro completo entre pontos.
- A integração Python com o endpoint de status do backend requer validação específica.
- Não publicar credenciais do Oracle ou arquivos `.env` com segredos no repositório.
- **Protótipo acadêmico:** não utilizar rotas simuladas como orientação real de evacuação. Em emergência, siga a Defesa Civil (199).

## 🌱 ODS relacionados

- **ODS 11:** Cidades e comunidades sustentáveis.
- **ODS 13:** Ação contra a mudança global do clima.
- **ODS 9:** Indústria, inovação e infraestrutura.

## 🎓 Informações acadêmicas

**Instituição:** FIAP — Faculdade de Informática e Administração Paulista  
**Projeto:** AlertaCidade  
**Disciplina:** Dynamic Programming  
**Global Solution:** 2º semestre de 2026  
**Tema:** CitizenTech  
**Integrante:** Eduardo Antonio Delarissia — **RM 563468**

---

**AlertaCidade — Tecnologia para cidades mais seguras.**
