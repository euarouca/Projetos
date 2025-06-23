import os
import entrada_dados 
import crud_produtos
import crud_distribuidores
import crud_dados
import crud_asin
from database import Base, db
import processamento

# Constante para indicar que um campo não deve ser alterado
_VALOR_NAO_ALTERAR = object()

def limpar_tela():
    """Limpa a tela do console."""
    os.system('cls' if os.name == 'nt' else 'clear')

def obter_input_int(mensagem):
    """Obtém um input do usuário e garante que seja um inteiro."""
    while True:
        valor = input(mensagem)
        if not valor:
            return None
        try:
            return int(valor)
        except ValueError:
            print("Entrada inválida. Por favor, insira um número inteiro.")

def obter_input_float(mensagem):
    """Obtém um input do usuário e garante que seja um float."""
    while True:
        valor = input(mensagem)
        if not valor:
            return None
        try:
            return float(valor.replace(',', '.'))
        except ValueError:
            print("Entrada inválida. Por favor, insira um número (ex: 10.99).")

def obter_input_bool(mensagem):
    """Obtém um input do usuário e garante que seja um booleano (s/n)."""
    while True:
        valor = input(mensagem).strip().lower()
        if valor == 's':
            return True
        elif valor == 'n':
            return False
        print("Entrada inválida. Por favor, responda com 's' ou 'n'.")

# --- Menus de Gerenciamento (CRUD) ---

def menu_gerenciar_produtos():
    """Menu para gerenciar o CRUD de Produtos."""
    while True:
        limpar_tela()
        print("\n--- Gerenciar Produtos ---")
        print("1. Adicionar Produto")
        print("2. Visualizar Produto")
        print("3. Atualizar Produto")
        print("4. Deletar Produto")
        print("0. Voltar ao Menu Principal")
        escolha = input("Escolha uma opção: ")

        if escolha == '1':
            pn = input("Part Number: ").strip()
            pack = obter_input_int("Pack: ")
            brand = input("Marca: ").strip().upper()
            if pn and pack is not None and brand:
                crud_produtos.adicionar_produto(pn, pack, brand)
            else:
                print("Todos os campos são obrigatórios.")
        elif escolha == '2':
            pn = input("Part Number do produto a visualizar: ").strip()
            pack = obter_input_int("Pack do produto (padrão 1): ")
            if pn:
                crud_produtos.visualizar_produto(pn, pack if pack is not None else 1)
        elif escolha == '3':
            pn_orig = input("Part Number original: ").strip()
            pack_orig = obter_input_int("Pack original: ")
            if not pn_orig or pack_orig is None:
                print("Part Number e Pack originais são obrigatórios.")
                continue
            
            print("\nEntre com os novos dados (deixe em branco para não alterar):")
            novo_pn = input(f"Novo Part Number: ").strip()
            novo_pack_str = input(f"Novo Pack: ")
            nova_brand = input("Nova Marca: ").strip().upper()
            
            crud_produtos.atualizar_produto(
                partNumber_original=pn_orig,
                pack_original=pack_orig,
                novo_partNumber=novo_pn if novo_pn else _VALOR_NAO_ALTERAR,
                novo_pack=int(novo_pack_str) if novo_pack_str else _VALOR_NAO_ALTERAR,
                nova_brand=nova_brand if nova_brand else _VALOR_NAO_ALTERAR
            )
        elif escolha == '4':
            pn = input("Part Number do produto a deletar: ").strip()
            pack = obter_input_int("Pack do produto a deletar: ")
            if pn and pack is not None:
                crud_produtos.deletar_produto(pn, pack)
        elif escolha == '0':
            break
        else:
            print("Opção inválida!")
        
        input("\nPressione Enter para continuar...")


def menu_gerenciar_distribuidores():
    """Menu para gerenciar o CRUD de Distribuidores."""
    while True:
        limpar_tela()
        print("\n--- Gerenciar Distribuidores ---")
        print("1. Adicionar Distribuidor")
        print("2. Visualizar Distribuidor")
        print("3. Atualizar Distribuidor")
        print("4. Deletar Distribuidor")
        print("0. Voltar ao Menu Principal")
        escolha = input("Escolha uma opção: ")

        if escolha == '1':
            nome = input("Nome do Distribuidor: ").strip()
            prime = obter_input_bool("É Prime? (s/n): ")
            if nome:
                crud_distribuidores.adicionar_distribuidor(nome, prime)
        elif escolha == '2':
            nome = input("Nome do distribuidor a visualizar: ").strip()
            if nome:
                crud_distribuidores.visualizar_distribuidor(nome)
        elif escolha == '3':
            nome_orig = input("Nome original do distribuidor: ").strip()
            if not nome_orig:
                print("O nome original é obrigatório.")
                continue
            
            print("\nEntre com os novos dados (deixe em branco para não alterar):")
            novo_nome = input(f"Novo nome (atual: {nome_orig}): ").strip()
            novo_prime_str = input("É Prime agora? (s/n, deixe em branco para não alterar): ").lower()
            
            novo_prime = _VALOR_NAO_ALTERAR
            if novo_prime_str == 's':
                novo_prime = True
            elif novo_prime_str == 'n':
                novo_prime = False

            crud_distribuidores.atualizar_distribuidor(
                name_original=nome_orig,
                novo_name=novo_nome if novo_nome else _VALOR_NAO_ALTERAR,
                novo_prime=novo_prime
            )
        elif escolha == '4':
            nome = input("Nome do distribuidor a deletar: ").strip()
            if nome:
                crud_distribuidores.deletar_distribuidor(nome)
        elif escolha == '0':
            break
        else:
            print("Opção inválida!")
        
        input("\nPressione Enter para continuar...")

def menu_gerenciar_dados_distribuidor():
    """Menu para gerenciar o CRUD de Dados do Distribuidor."""
    while True:
        limpar_tela()
        print("\n--- Gerenciar Dados de Distribuidores ---")
        print("1. Adicionar Dados de Distribuidor")
        print("2. Visualizar Dados por PartNumber/Pack")
        print("3. Visualizar Dados por ID")
        print("4. Atualizar Dados de Distribuidor")
        print("5. Deletar Dados de Distribuidor")
        print("0. Voltar ao Menu Principal")
        escolha = input("Escolha uma opção: ")

        if escolha == '1':
            dist_name = input("Nome do Distribuidor: ").strip()
            pn = input("Part Number: ").strip()
            pack = obter_input_int("Pack: ")
            price = obter_input_float("Preço: ")
            stock = obter_input_int("Estoque: ")
            sku = input("SKU (opcional): ").strip()
            if dist_name and pn and pack is not None and price is not None and stock is not None:
                crud_dados.adicionar_dados_distribuidor(dist_name, pn, pack, price, stock, sku)
        elif escolha == '2':
            pn = input("Part Number a pesquisar: ").strip()
            pack = obter_input_int("Pack a pesquisar: ")
            if pn and pack is not None:
                crud_dados.visualizar_dados_por_partnumber_pack(pn, pack)
        elif escolha == '3':
            id_dados = obter_input_int("ID do registro de dados a visualizar: ")
            if id_dados is not None:
                crud_dados.visualizar_dados_distribuidor_por_id(id_dados)
        elif escolha == '4':
            print("Identifique o registro a ser atualizado:")
            dist_orig = input("Nome original do Distribuidor: ").strip()
            pn_orig = input("Part Number original: ").strip()
            pack_orig = obter_input_int("Pack original: ")
            if not dist_orig or not pn_orig or pack_orig is None:
                print("Todos os campos de identificação são obrigatórios.")
                continue
            print("\nEntre com os novos dados (deixe em branco para não alterar):")
            novo_price = obter_input_float("Novo Preço: ")
            novo_stock = obter_input_int("Novo Estoque: ")
            novo_sku = input("Novo SKU: ").strip()
            crud_dados.atualizar_dados_distribuidor(
                distributor_name_original=dist_orig,
                partNumber_original=pn_orig,
                pack_original=pack_orig,
                novo_price=novo_price if novo_price is not None else _VALOR_NAO_ALTERAR,
                novo_stock=novo_stock if novo_stock is not None else _VALOR_NAO_ALTERAR,
                novo_sku=novo_sku if novo_sku else _VALOR_NAO_ALTERAR
            )
        elif escolha == '5':
            print("Identifique o registro a ser deletado:")
            dist_name = input("Nome do Distribuidor: ").strip()
            pn = input("Part Number: ").strip()
            pack = obter_input_int("Pack: ")
            if dist_name and pn and pack is not None:
                crud_dados.deletar_dados_distribuidor(dist_name, pn, pack)
        elif escolha == '0':
            break
        else:
            print("Opção inválida!")
        
        input("\nPressione Enter para continuar...")


def menu_gerenciar_asins():
    """Menu para gerenciar o CRUD de ASINs (FBM)."""
    while True:
        limpar_tela()
        print("\n--- Gerenciar ASINs (FBM) ---")
        print("1. Adicionar ASIN")
        print("2. Visualizar ASIN")
        print("3. Atualizar ASIN")
        print("4. Deletar ASIN")
        print("0. Voltar ao Menu Principal")
        escolha = input("Escolha uma opção: ")

        if escolha == '1':
            product_id = obter_input_int("ID do Produto a associar: ")
            asin = input("ASIN: ").strip()
            if product_id is not None and asin:
                current_price = obter_input_float("Preço Atual (opcional): ")
                stock = obter_input_int("Estoque (opcional): ")
                supplier = input("Fornecedor (opcional): ").strip()
                crud_asin.adicionar_asin(product_id, asin, current_price=current_price, stock=stock, supplier=supplier)
        elif escolha == '2':
            asin = input("ASIN a visualizar: ").strip()
            if asin:
                crud_asin.visualizar_asin(asin)
        elif escolha == '3':
            asin_orig = input("ASIN do registro a atualizar: ").strip()
            if not asin_orig:
                print("O ASIN original é obrigatório.")
                continue
            
            print("\nEntre com os novos dados (deixe em branco para não alterar):")
            novo_asin = input(f"Novo ASIN: ").strip()
            novo_prod_id = obter_input_int("Novo ID de Produto associado: ")
            novo_price = obter_input_float("Novo Preço Atual: ")
            novo_stock = obter_input_int("Novo Estoque: ")
            novo_supplier = input("Novo Fornecedor: ").strip()

            crud_asin.atualizar_fbm_campos_especificos(
                asin_para_atualizar=asin_orig,
                novo_asin_valor=novo_asin if novo_asin else _VALOR_NAO_ALTERAR,
                product_id=novo_prod_id if novo_prod_id is not None else _VALOR_NAO_ALTERAR,
                current_price=novo_price if novo_price is not None else _VALOR_NAO_ALTERAR,
                stock=novo_stock if novo_stock is not None else _VALOR_NAO_ALTERAR,
                supplier=novo_supplier if novo_supplier else _VALOR_NAO_ALTERAR
            )
        elif escolha == '4':
            asin = input("ASIN a deletar: ").strip()
            if asin:
                crud_asin.deletar_fbm_por_asin(asin)
        elif escolha == '0':
            break
        else:
            print("Opção inválida!")
        
        input("\nPressione Enter para continuar...")

# --- Menus de Processamento de Arquivos ---

def menu_processar_pasta_distribuidores():
    """Menu para processar uma pasta de CSVs com dados unificados."""
    limpar_tela()
    print("--- Processar Pasta de CSVs de Distribuidores (Formato Unificado) ---")
    caminho_pasta = '/Users/lucasmello/Projetos/API/planilhas'
    if os.path.isdir(caminho_pasta):
        # A chamada agora é para a nova função unificada
        entrada_dados.processar_pasta_unificada(caminho_pasta)
    else:
        print("Caminho inválido ou não é uma pasta.")
    input("\nPressione Enter para continuar...")
    
    
def menu_atualizar_todos_fbm():
    """Menu para disparar a atualização de todos os registros FBM."""
    limpar_tela()
    print("--- Atualização em Lote de Todos os Registros FBM ---")
    print("Este processo irá analisar as ofertas de todos os produtos com ASIN")
    print("e atualizar seus preços, estoques e status de promoção.")

    confirmar = input("\nDeseja continuar? (s/n): ").strip().lower()

    if confirmar == 's':
        processamento.atualizar_todos_os_fbm()
    else:
        print("Operação cancelada.")

    input("\nPressione Enter para continuar...")

# --- Loop Principal ---
if __name__ == "__main__":
    print("Inicializando e verificando o banco de dados...")
    Base.metadata.create_all(db)
    print("Sistema pronto.")
    input("Pressione Enter para continuar...")
    

    while True:
        limpar_tela()
        print("\n--- MENU PRINCIPAL ---")
        print("\n--- Gerenciamento (CRUD) ---")
        print("1. Gerenciar Produtos")
        print("2. Gerenciar Distribuidores")
        print("3. Gerenciar Dados de Distribuidores")
        print("4. Gerenciar ASINs (FBM)")
        print("\n--- Processamento de Arquivos ---") # Título da Seção Atualizado
        print("5. Processar Pasta de CSVs de Distribuidores (Unificado)")
        print("6. Atualizar Todos os Registros FBM (Análise de Ofertas)") 
        print("\n---------------------------------")
        print("0. Sair")
        
        escolha = input("\nEscolha uma opção: ")
        
        if escolha == '1':
            menu_gerenciar_produtos()
        elif escolha == '2':
            menu_gerenciar_distribuidores()
        elif escolha == '3':
            menu_gerenciar_dados_distribuidor()
        elif escolha == '4':
            menu_gerenciar_asins()
        elif escolha == '5':
            menu_processar_pasta_distribuidores() 
        elif escolha == '6': 
            menu_atualizar_todos_fbm()
        elif escolha == '0':
            print("Saindo do programa.")
            break
        else:
            print("Opção inválida! Tente novamente.")
        
        print("\nRetornando ao menu principal...")
        input("Pressione Enter para continuar...")