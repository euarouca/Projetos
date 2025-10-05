# interface.py

import streamlit as st
import os
import io
import contextlib

# Importando todos os módulos do seu projeto
import crud_produtos
import crud_distribuidores
import crud_dados
import crud_asin
import processamento
import exportador
import entrada_dados
import sheets_process # Novo módulo de processo do Sheets
from database import session, Product, Distributor, DistributorData, FBM

# --- UTILS PARA A INTERFACE ---

st.set_page_config(layout="wide")

@contextlib.contextmanager
def st_capture(output_func):
    """Um gerenciador de contexto para capturar prints e exibi-los no Streamlit."""
    with io.StringIO() as stdout, contextlib.redirect_stdout(stdout):
        yield
        output_func(stdout.getvalue())

# --- BARRA LATERAL DE NAVEGAÇÃO ---

st.sidebar.title("Menu de Navegação")
pagina = st.sidebar.radio(
    "Selecione a funcionalidade:",
    (
        "Adicionar ASIN",
        "Importar ASINs em Lote (CSV)",
        "Gerenciar Produtos",
        "Gerenciar Distribuidores",
        "Gerenciar Dados de Distribuidores",
        "Processamento e Exportação",
        "Atualizar Google Sheets", # NOVA OPÇÃO
    ),
)

# --- PÁGINA PRINCIPAL ---

if pagina == "Adicionar ASIN":
    st.title("Adicionar ASIN a um Produto")
    st.write("Esta tela permite associar um novo ASIN a um produto. Se o produto (Part Number + Pack) não existir, ele será cadastrado automaticamente.")

    with st.form("adicionar_asin_form"):
        partNumber_input = st.text_input("Part Number do Produto:")
        pack_input = st.number_input("Pack do Produto:", min_value=1, step=1)
        asin_input = st.text_input("ASIN a ser adicionado:")
        
        submitted = st.form_submit_button("Adicionar ASIN")

        if submitted:
            if not all([partNumber_input, pack_input, asin_input]):
                st.error("Todos os campos são obrigatórios.")
            else:
                with st.spinner("Verificando e processando..."):
                    produto_id_final = None
                    produto_existente = session.query(Product).filter_by(
                        partNumber=partNumber_input.strip(), pack=pack_input
                    ).first()
                    if produto_existente:
                        st.info(f"Produto encontrado (ID={produto_existente.id}).")
                        produto_id_final = produto_existente.id
                    else:
                        st.info(f"Produto '{partNumber_input}' (Pack: {pack_input}) não encontrado. Cadastrando automaticamente...")
                        with st_capture(st.code):
                            novo_produto = crud_produtos.adicionar_produto(
                                partNumber=partNumber_input.strip(),
                                pack=pack_input,
                                brand=None,
                                quiet=False
                            )
                        if novo_produto and novo_produto.id:
                            produto_id_final = novo_produto.id
                            st.success(f"Novo produto cadastrado com sucesso (ID={produto_id_final}).")
                        else:
                            st.error("Ocorreu um erro ao tentar cadastrar o novo produto.")
                    if produto_id_final:
                        st.info(f"Associando o ASIN '{asin_input}' ao produto ID {produto_id_final}...")
                        with st_capture(st.code):
                             fbm_obj, foi_criado = crud_asin.adicionar_asin(
                                product_id=produto_id_final, asin=asin_input.strip()
                            )
                             if foi_criado is False and fbm_obj is not None:
                                 print(f"Aviso: O ASIN '{fbm_obj.asin}' já existia no banco de dados.")
                        st.success("Operação finalizada!")

elif pagina == "Importar ASINs em Lote (CSV)":
    st.title("Importar ASINs em Lote via CSV")
    st.write("Envie um arquivo CSV com as colunas `asin`, `partNumber` e `pack` para adicionar ou associar múltiplos ASINs de uma só vez.")
    st.info("Se um produto (`partNumber` + `pack`) não for encontrado, ele será criado automaticamente.")
    uploaded_file = st.file_uploader("Escolha um arquivo CSV", type="csv")
    if uploaded_file is not None:
        st.write("Arquivo recebido. Clique no botão abaixo para iniciar o processamento.")
        if st.button("Processar Arquivo"):
            with st.spinner("Processando arquivo... Isso pode levar alguns minutos."):
                with st_capture(st.code):
                    sucessos, falhas, produtos_criados, ja_existiam = entrada_dados.processar_csv_asins(uploaded_file)
            st.success(f"Processamento finalizado!")
            col1, col2, col3 = st.columns(3)
            col1.metric(label="Novos Produtos Criados", value=produtos_criados)
            col2.metric(label="Novos ASINs Associados", value=sucessos)
            col3.metric(label="ASINs Já Existentes", value=ja_existiam)
            if falhas > 0:
                st.error(f"**{falhas} linhas falharam ou foram ignoradas.**")
                st.warning(f"Verifique o log de processamento acima para detalhes sobre as falhas.")

elif pagina == "Gerenciar Produtos":
    st.title("Gerenciador de Produtos")
    with st.expander("Adicionar Novo Produto"):
        with st.form("add_produto_form"):
            pn = st.text_input("Part Number", key="add_pn")
            pack = st.number_input("Pack", min_value=1, step=1, key="add_pack")
            brand = st.text_input("Marca", key="add_brand")
            if st.form_submit_button("Adicionar Produto"):
                with st_capture(st.code):
                    crud_produtos.adicionar_produto(pn, pack, brand.upper())
                st.success("Produto adicionado com sucesso (ou já existia).")
    with st.expander("Visualizar / Deletar Produtos"):
        st.subheader("Buscar Produto Específico")
        pn_search = st.text_input("Part Number para buscar")
        pack_search = st.number_input("Pack para buscar", min_value=1, step=1, key="search_pack")
        if st.button("Buscar"):
            with st_capture(st.info):
                crud_produtos.visualizar_produto(pn_search, pack_search)
        st.subheader("Listar Todos os Produtos")
        if st.button("Carregar Lista de Produtos"):
            produtos = session.query(Product).all()
            st.dataframe(produtos)

elif pagina == "Gerenciar Distribuidores":
    st.title("Gerenciador de Distribuidores")
    with st.expander("Adicionar Novo Distribuidor"):
        with st.form("add_dist_form"):
            nome_dist = st.text_input("Nome do Distribuidor")
            prime = st.checkbox("É um distribuidor 'Prime'?")
            if st.form_submit_button("Adicionar Distribuidor"):
                with st_capture(st.code):
                    crud_distribuidores.adicionar_distribuidor(nome_dist, prime)
                st.success("Operação concluída.")
    with st.expander("Visualizar / Deletar Distribuidores"):
        st.subheader("Buscar Distribuidor")
        nome_dist_search = st.text_input("Nome do distribuidor para buscar")
        if st.button("Buscar Distribuidor"):
            with st_capture(st.info):
                crud_distribuidores.visualizar_distribuidor(nome_dist_search)
        st.subheader("Listar Todos os Distribuidores")
        if st.button("Carregar Lista de Distribuidores"):
            distribuidores = session.query(Distributor).all()
            st.dataframe(distribuidores)

elif pagina == "Gerenciar Dados de Distribuidores":
    st.title("Gerenciador de Dados de Distribuidores")
    st.write("Adicione ou atualize os preços e estoques de um produto para um distribuidor específico.")
    with st.expander("Adicionar ou Atualizar Dados"):
         with st.form("add_dados_dist_form"):
            dist_name = st.text_input("Nome do Distribuidor")
            pn = st.text_input("Part Number")
            pack = st.number_input("Pack", min_value=1, step=1)
            price = st.number_input("Preço (R$)")
            stock = st.number_input("Estoque", min_value=0, step=1)
            sku = st.text_input("SKU (opcional)")
            if st.form_submit_button("Salvar Dados"):
                with st_capture(st.code):
                    crud_dados.adicionar_dados_distribuidor(dist_name, pn, pack, price, stock, sku)
                st.success("Operação concluída.")
    with st.expander("Visualizar Todos os Dados"):
         if st.button("Carregar Todos os Dados de Distribuidores"):
            dados = session.query(DistributorData).all()
            st.dataframe(dados, height=500)

elif pagina == "Processamento e Exportação":
    st.title("Processamento em Lote e Exportação")
    st.header("1. Importar Preços/Estoque de Distribuidores (CSV)")
    st.info("Esta operação lê todos os arquivos CSV de uma pasta pré-definida e atualiza os preços e estoques no banco de dados.")
    caminho_importacao = '/Users/lucasmello/Projetos/API/planilhas'
    st.write(f"**Pasta de importação:** `{caminho_importacao}`")
    if st.button("Iniciar Importação"):
        with st.spinner("Processando arquivos... Isso pode levar alguns minutos."):
            with st_capture(st.code):
                entrada_dados.processar_pasta_distribuidores(caminho_importacao)
        st.success("Importação finalizada!")
    st.header("2. Atualizar Todos os Registros FBM (Análise de Ofertas)")
    st.info("Esta operação varre todos os ASINs, analisa as melhores ofertas de preço/estoque e atualiza os dados na tabela FBM.")
    if st.button("Iniciar Atualização de FBM"):
        with st.spinner("Analisando ofertas e atualizando ASINs..."):
            with st_capture(st.code):
                processamento.atualizar_todos_os_fbm()
        st.success("Atualização de FBM finalizada!")
    st.header("3. Exportar Produtos para CSV")
    st.info("Cria arquivos CSV contendo a lista de todos os produtos cadastrados, separados em lotes de 1000.")
    caminho_exportacao = '/Users/lucasmello/Projetos/API/planilhas_exportadas'
    st.write(f"**Pasta de exportação:** `{caminho_exportacao}`")
    if st.button("Iniciar Exportação"):
        with st.spinner("Gerando arquivos CSV..."):
            with st_capture(st.code):
                exportador.exportar_produtos_em_lote(caminho_exportacao)
        st.success("Exportação finalizada!")

elif pagina == "Atualizar Google Sheets":
    st.title("Atualizar Planilha Google Sheets")
    st.info("Esta função busca os dados mais recentes da tabela FBM do banco de dados local e os envia para a sua planilha no Google Drive.")
    st.warning("Atenção: Esta operação irá limpar a aba 'FBM' da sua planilha e reescrevê-la com os dados atuais.")
    
    if st.button("Iniciar Atualização da Planilha"):
        with st.spinner("Conectando e atualizando a planilha... Isso pode demorar."):
            with st_capture(st.code):
                sheets_process.atualizar_planilha_fbm()
        st.success("Planilha atualizada!")