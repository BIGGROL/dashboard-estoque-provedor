import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Caminhos
PASTA_DADOS = Path("dados")
PASTA_GRAFICOS = Path("graficos")
PASTA_GRAFICOS.mkdir(exist_ok=True)

arquivo = PASTA_DADOS / "relatorio.csv"

# Lê o CSV exportado do IXC
df = pd.read_csv(arquivo, sep=";", encoding="utf-8-sig")

# Ajusta nomes das colunas
df.columns = (
    df.columns
    .str.replace('"', "", regex=False)
    .str.replace("=", "", regex=False)
    .str.strip()
    .str.lower()
)

# Renomeia colunas
df = df.rename(columns={
    "produto": "produto",
    "situação": "situacao",
    "estoque atual": "estoque_atual",
    "mínimo": "estoque_minimo",
    "máximo": "estoque_maximo"
})

# Limpa textos
df["produto"] = df["produto"].astype(str).str.replace('"', "", regex=False).str.strip()
df["situacao"] = df["situacao"].astype(str).str.replace('"', "", regex=False).str.strip()

# Converte números
for coluna in ["estoque_atual", "estoque_minimo", "estoque_maximo"]:
    df[coluna] = (
        df[coluna]
        .astype(str)
        .str.replace('"', "", regex=False)
        .str.replace("=", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
    )
    df[coluna] = pd.to_numeric(df[coluna], errors="coerce").fillna(0).astype(int)

# Remove ONUs e produtos zerados
df = df[~df["produto"].str.upper().str.contains("ONU")]
df = df[df["estoque_atual"] > 0]

# Cria colunas de análise
df["reposicao_ate_maximo"] = df["estoque_maximo"] - df["estoque_atual"]
df["reposicao_ate_maximo"] = df["reposicao_ate_maximo"].apply(lambda x: max(x, 0))

df["excesso"] = df["estoque_atual"] - df["estoque_maximo"]
df["excesso"] = df["excesso"].apply(lambda x: max(x, 0))

def classificar(row):
    if row["estoque_atual"] < row["estoque_minimo"]:
        return "Crítico"
    elif row["estoque_atual"] > row["estoque_maximo"]:
        return "Excessivo"
    elif row["estoque_atual"] <= row["estoque_minimo"] * 1.2:
        return "Atenção"
    else:
        return "OK"

df["prioridade"] = df.apply(classificar, axis=1)

# Indicadores
total_produtos = len(df)
total_atual = df["estoque_atual"].sum()
produtos_criticos = len(df[df["prioridade"] == "Crítico"])
produtos_excessivos = len(df[df["prioridade"] == "Excessivo"])
reposicao_total = df["reposicao_ate_maximo"].sum()

print("=" * 60)
print("DASHBOARD DE ESTOQUE MÍNIMO E MÁXIMO")
print("=" * 60)
print(f"Produtos monitorados: {total_produtos}")
print(f"Estoque total atual: {total_atual}")
print(f"Produtos críticos: {produtos_criticos}")
print(f"Produtos em excesso: {produtos_excessivos}")
print(f"Reposição necessária até o máximo: {reposicao_total}")
print("=" * 60)

print("\nTabela final:")
print(df[["produto", "situacao", "estoque_atual", "estoque_minimo", "estoque_maximo", "reposicao_ate_maximo", "prioridade"]])

# Gráfico 1 - Produtos por prioridade
plt.figure(figsize=(8, 5))
contagem = df["prioridade"].value_counts()
plt.bar(contagem.index, contagem.values)
plt.title("Quantidade de Produtos por Prioridade")
plt.xlabel("Prioridade")
plt.ylabel("Quantidade")
plt.tight_layout()
plt.savefig(PASTA_GRAFICOS / "produtos_por_prioridade.png", dpi=300)
plt.show()

# Gráfico 2 - Estoque atual x mínimo x máximo
df_ordenado = df.sort_values("estoque_atual", ascending=False)

plt.figure(figsize=(12, 6))
x = range(len(df_ordenado))

plt.bar(x, df_ordenado["estoque_maximo"], label="Máximo")
plt.bar(x, df_ordenado["estoque_atual"], label="Atual")
plt.bar(x, df_ordenado["estoque_minimo"], label="Mínimo")

plt.xticks(x, df_ordenado["produto"], rotation=45, ha="right")
plt.title("Estoque Atual x Mínimo x Máximo")
plt.xlabel("Produto")
plt.ylabel("Quantidade")
plt.legend()
plt.tight_layout()
plt.savefig(PASTA_GRAFICOS / "estoque_atual_minimo_maximo.png", dpi=300)
plt.show()

# Gráfico 3 - Reposição até máximo
df_reposicao = df[df["reposicao_ate_maximo"] > 0].sort_values("reposicao_ate_maximo", ascending=True)

plt.figure(figsize=(10, 6))
plt.barh(df_reposicao["produto"], df_reposicao["reposicao_ate_maximo"])
plt.title("Reposição Necessária até o Estoque Máximo")
plt.xlabel("Quantidade para Comprar")
plt.ylabel("Produto")
plt.tight_layout()
plt.savefig(PASTA_GRAFICOS / "reposicao_ate_maximo.png", dpi=300)
plt.show()

# Salva relatório tratado
df.to_csv("dados/estoque_min_max_tratado.csv", sep=";", index=False, encoding="utf-8-sig")