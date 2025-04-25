import pandas as pd
import streamlit as st
import requests
import plotly.express as px

st.set_page_config(layout= 'wide')

def formata_numero(valor, prefixo = ''):
    for unidade in ['', 'mil']:
        if valor < 1000:
            return f'{prefixo} {valor:.2f} {unidade}'
        valor /= 1000
    return f'{prefixo} {valor:.2f} milhões'

st.title('Dashboard Vendas :shopping_trolley:')

url = 'https://labdados.com/produtos'

regioes = ['Brasil', 'Centro-Oeste', 'Nordeste', 'Norte', 'Sudeste', 'Sul']
st.sidebar.title('Filtros')
regiao = st.sidebar.selectbox('Regiao', regioes)
if regiao == 'Brasil':
    regiao = ''

todos_anos = st.sidebar.checkbox('Dados de todo o periodo', value = True)
if todos_anos:
    ano = ''
else:
    ano = st.sidebar.slider('Ano', 2020, 2023)     

query_string = {'regiao': regiao.lower(), 'ano': ano}

response = requests.get(url, params=query_string)


dados = pd.DataFrame.from_dict(response.json())
dados['Data da Compra'] = pd.to_datetime(dados['Data da Compra'], format = '%d/%m/%Y')
filtro_vendedores = st.sidebar.multiselect('Vendedores',dados['Vendedor'].unique())

if filtro_vendedores:
    dados = dados[dados['Vendedor'].isin(filtro_vendedores)]
    
        
#tabelas
receitas_estados = dados.groupby(['Local da compra'])[['Preço']].sum()
receitas_estados = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra', 'lat', 'lon']].merge(receitas_estados, left_on='Local da compra', right_index= True).sort_values('Preço', ascending= False)
receita_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].sum().reset_index()
receita_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
receita_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()
receita_categorias = dados.groupby('Categoria do Produto')[['Preço']].sum().sort_values('Preço', ascending=False)

#graficos
fig_mapa_receita = px.scatter_geo(receitas_estados,
                                  lat= 'lat',
                                  lon= 'lon',
                                  scope= 'south america',
                                  size= 'Preço',
                                  template= 'seaborn',
                                  hover_name= 'Local da compra',
                                  hover_data= {'lat': False, 'lon': False},
                                  title= 'Receita por estados')

fig_receita_mensal = px.line(receita_mensal,
                             x = 'Mes', y = 'Preço',
                             markers= True, range_y= (0, receita_mensal.max()),
                             color= 'Ano', line_dash= 'Ano', title = 'Receita mensal')
fig_receita_mensal.update_layout(yaxis_title = 'Receita')

fig_receita_estados = px.bar(receitas_estados.head(),
                                            x = 'Local da compra',
                                            y = 'Preço',
                                            text_auto = True,
                                            title = 'Top estados')
fig_mapa_receita.update_layout(yaxis_title = 'Receita')

fig_receita_categorias = px.bar(receita_categorias, text_auto= True, title = 'receitas por estado')
fig_receita_categorias.update_layout(yaxis_title = 'receita')

#visualização
aba1, aba2, aba3 = st.tabs(['Receita', 'Quantidade de vendas', 'Vendedores'])

#tabela vendedor
vendedores = pd.DataFrame(dados.groupby('Vendedor')['Preço'].agg(['sum', 'count']))

#tabela qtd_vendas
vendas_estado = dados.groupby('Local da compra')['Preço'].count()
vendas_estado = dados.drop_duplicates(subset = 'Local da compra')[['Local da compra', 'lat', 'lon']].merge(vendas_estado, left_on='Local da compra', right_index= True).sort_values('Preço', ascending= False)
vendas_mensal = dados.set_index('Data da Compra').groupby(pd.Grouper(freq='M'))['Preço'].sum().reset_index()
vendas_mensal['Ano'] = receita_mensal['Data da Compra'].dt.year
vendas_mensal['Mes'] = receita_mensal['Data da Compra'].dt.month_name()
vendas_categoria = dados.groupby('Categoria do Produto')['Preço'].count().sort_values(ascending= False)

with aba1:
    coluna1, coluna2 = st.columns(2)
    with coluna1: 
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        st.plotly_chart(fig_mapa_receita, use_container_width= True)
        st.plotly_chart(fig_receita_estados, use_container_width= True)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        st.plotly_chart(fig_receita_mensal, use_container_width= True)
        st.plotly_chart(fig_receita_categorias, use_container_width= True)


with aba2:
    coluna1, coluna2 = st.columns(2)
    with coluna1: 
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        fig_vendas_estado = px.scatter_geo(vendas_estado, lat = 'lat', lon = 'lon', scope = 'south america', size = 'Preço', hover_data = {'lat': False, 'lon': False},
                                           template= 'seaborn', hover_name= 'Local da compra')
        st.plotly_chart(fig_vendas_estado, use_container_width= True)
        
        fig_top_estados = px.bar(vendas_estado.head(5), x = 'Local da compra', y = 'Preço', title = 'Top 5 estados', color = 'Local da compra', text_auto=True)
        fig_top_estados.update_layout(yaxis_title = 'vendas')
        st.plotly_chart(fig_top_estados, use_container_width= True)
        
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        fig_vendas_mensal = px.line(vendas_mensal, x = 'Mes', y = 'Preço', markers= True, range_y= (0, vendas_mensal.max()),color = 'Ano', 
              line_dash = 'Ano',)
        st.plotly_chart(fig_vendas_mensal, use_container_width= True)

        fig_vendas_categoria = px.bar(vendas_categoria,text_auto= True, title = 'Vendas por categoria', hover_data= {'variable': False})
        st.plotly_chart(fig_vendas_categoria)


with aba3:
    qtd_vendedores = st.number_input('Quantidade de vendedores', 2 , 10, 5)
    coluna1, coluna2 = st.columns(2)
    with coluna1: 
        st.metric('Receita', formata_numero(dados['Preço'].sum(), 'R$'))
        fig_receita_vendedores = px.bar(vendedores[['sum']].sort_values('sum', ascending= False).head(qtd_vendedores),
                                        x = 'sum', y = vendedores[['sum']].sort_values('sum', ascending= False).head(qtd_vendedores).index,
                                        text_auto= True, title = f'Top {qtd_vendedores} vendedores (receita)')
        st.plotly_chart(fig_receita_vendedores)
    with coluna2:
        st.metric('Quantidade de vendas', formata_numero(dados.shape[0]))
        fig_vendas_vendedores = px.bar(vendedores[['count']].sort_values('count', ascending= False).head(qtd_vendedores),
                                        x = 'count', y = vendedores[['count']].sort_values('count', ascending= False).head(qtd_vendedores).index,
                                        text_auto= True, title = f'Top {qtd_vendedores} vendedores (vendas)')
        st.plotly_chart(fig_vendas_vendedores)


st.dataframe(dados)