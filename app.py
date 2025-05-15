import streamlit as st
import pandas as pd
import plotly.express as px
import os

# Título da aplicação
st.set_page_config(page_title="Painel de Vendas - Olist", layout="wide")
st.title("📦 Painel de Vendas - E-commerce Brasileiro (Olist)")

# Mostrar estrutura de arquivos (para depuração)
st.sidebar.header("Debug")
st.sidebar.write("🔍 Conteúdo do diretório:")
st.sidebar.write(os.listdir())

if os.path.exists('csv'):
    st.sidebar.write("📂 Conteúdo da pasta 'csv':")
    st.sidebar.write(os.listdir('csv'))
else:
    st.sidebar.error("❌ Pasta 'csv' não encontrada!")

# Carregando os dados
@st.cache_data
def load_data():
    try:
        orders = pd.read_csv("csv/olist_orders_dataset.csv", parse_dates=["order_purchase_timestamp"])
        customers = pd.read_csv("csv/olist_customers_dataset.csv")
        items = pd.read_csv("csv/olist_order_items_dataset.csv")
        products = pd.read_csv("csv/olist_products_dataset.csv")
        reviews = pd.read_csv("csv/olist_order_reviews_dataset.csv")
        sellers = pd.read_csv("csv/olist_sellers_dataset.csv")
        return orders, customers, items, products, reviews, sellers
    except Exception as e:
        st.error(f"🚨 Erro ao carregar os dados: {e}")
        st.stop()

# Tentativa de carregar os dados
try:
    orders, customers, items, products, reviews, sellers = load_data()
except Exception as e:
    st.error(f"💥 Falha crítica ao carregar os dados: {e}")
    st.stop()

# Pré-processamento
try:
    orders = orders.merge(customers, on="customer_id")
    df = orders.merge(items, on="order_id")
    df = df.merge(products, on="product_id")
    df = df.merge(reviews, on="order_id", how="left")
    df = df.merge(sellers, on="seller_id")

    # Filtros interativos
    st.sidebar.header("Filtros")
    estados = st.sidebar.multiselect(
        "Estado do Cliente",
        options=sorted(df.customer_state.unique()),
        default=df.customer_state.unique()
    )
    categorias = st.sidebar.multiselect(
        "Categoria do Produto",
        options=sorted(df.product_category_name.dropna().unique()),
        default=df.product_category_name.dropna().unique()
    )

    filtro = df[df.customer_state.isin(estados) & df.product_category_name.isin(categorias)]

    # Gráfico 1: Evolução mensal das vendas
    filtro["ano_mes"] = filtro["order_purchase_timestamp"].dt.to_period("M").astype(str)

    vendas_mensais = filtro.groupby("ano_mes").order_id.nunique().reset_index()
    vendas_mensais.columns = ["Mês", "Pedidos"]

    fig1 = px.line(vendas_mensais, x="Mês", y="Pedidos", title="📈 Evolução Mensal dos Pedidos")
    st.plotly_chart(fig1, use_container_width=True)

    # Gráfico 2: Avaliação vs Tempo de Entrega
    filtro["tempo_entrega"] = (
        pd.to_datetime(filtro["order_delivered_customer_date"]) -
        pd.to_datetime(filtro["order_purchase_timestamp"])
    )
    filtro = filtro.dropna(subset=["tempo_entrega", "review_score"])
    filtro["tempo_entrega_dias"] = filtro["tempo_entrega"].dt.days

    fig2 = px.box(filtro, x="review_score", y="tempo_entrega_dias", title="⏱️ Tempo de Entrega vs Avaliação do Cliente")
    st.plotly_chart(fig2, use_container_width=True)

    # Gráfico 3: Top Vendedores por Volume
    vendas_vendedores = filtro.groupby("seller_id").agg({
        "order_id": "nunique",
        "review_score": "mean",
        "tempo_entrega_dias": "mean"
    }).reset_index()
    vendas_vendedores.columns = ["Vendedor", "Pedidos", "Avaliação Média", "Tempo Médio Entrega"]
    top_vendedores = vendas_vendedores.sort_values(by="Pedidos", ascending=False).head(10)

    fig3 = px.bar(top_vendedores, x="Vendedor", y="Pedidos", title="🏆 Top 10 Vendedores por Volume de Pedidos")
    st.plotly_chart(fig3, use_container_width=True)

    # Footer
    st.markdown("---")
    st.markdown("Desenvolvido para o desafio do Programa Trainee da triggo.ai | Dados: Olist - Kaggle")

except Exception as e:
    st.error(f"💥 Erro durante a execução: {e}")
