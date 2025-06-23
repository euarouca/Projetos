from sqlalchemy.exc import SQLAlchemyError
from database import session, FBM, Product 
# Um objeto especial para indicar que um campo não deve ser alterado na atualização
_VALOR_NAO_ALTERAR = object()

# --- Create ---
def adicionar_asin(
    product_id: int, # Obrigatório, para associar ao produto
    asin: str,
    last_price: float = None,
    current_price: float = None,
    supplier: str = None,
    stock: int = None,
    prime_stock: int = None,
    all_stock: int = None,
    gap_stock: int = None,
    promotion: str = None,
):
    """
    Adiciona um novo ASIN (FBM) ao banco de dados, associado a um produto existente.

    Args:
        product_id (int): O ID do produto (da tabela 'produtos') ao qual este ASIN está associado.
        asin (str): O ASIN do produto (deve ser único).
        last_price (float, optional): Preço da última atualização.
        current_price (float, optional): Preço atual.
        supplier (str, optional): Nome do fornecedor.
        stock (int, optional): Estoque do fornecedor escolhido.
        prime_stock (int, optional): Estoque dos melhores fornecedores.
        all_stock (int, optional): Estoque de todos os fornecedores somados.
        gap_stock (int, optional): Diferença da última atualização de ALL_STOCK para essa.
        promotion (str, optional): Indica se está em promoção.

    Returns:
        FBM: O objeto FBM criado e salvo, ou o objeto existente se o ASIN já existir.
             Retorna None em caso de erro ou se o product_id não for válido.
    """
    asin = asin.strip()

    # Verificar se o product_id fornecido existe na tabela de produtos
    produto_associado = session.query(Product).filter_by(id=product_id).first()
    if not produto_associado:
        print(f"Erro: Produto com ID={product_id} não encontrado. Não é possível adicionar ASIN '{asin}'.")
        return None

    # Verificar se o ASIN já foi adicionado
    asin_existente = session.query(FBM).filter_by(asin=asin).first()
    if asin_existente:
        # print(f'Aviso: ASIN "{asin}" já existe (ID={asin_existente.id}, associado ao Produto ID={asin_existente.product_id}).')
        return asin_existente

    # Adicionando ao banco de dados
    novo_fbm = FBM(
        product_id=product_id,
        asin=asin,
        last_price=last_price,
        current_price=current_price,
        supplier=supplier,
        stock=stock,
        prime_stock=prime_stock,
        all_stock=all_stock,
        gap_stock=gap_stock,
        promotion=promotion
    )

    try:
        session.add(novo_fbm)
        session.commit()
        return novo_fbm
    except SQLAlchemyError as e:
        session.rollback()
        print(f'Erro SQLAlchemy ao adicionar FBM para ASIN="{asin}", Produto ID={product_id}: {str(e)}')
        return None
    except Exception as e:
        session.rollback()
        print(f"Um erro inesperado ocorreu ao adicionar FBM para ASIN '{asin}', Produto ID={product_id}: {str(e)}")
        return None

# -- Read --
def visualizar_asin(asin: str):
    """
    Busca e exibe os detalhes de um ASIN (FBM) específico.

    Args:
        asin (str): O ASIN a ser visualizado.

    Returns:
        FBM: O objeto FBM encontrado, ou None se não for encontrado ou em caso de erro.
    """
    asin = asin.strip()
    try:
        fbm_obj = session.query(FBM).filter_by(asin=asin).first()

        if fbm_obj:
            print(str(fbm_obj)) # Utiliza o __str__ da classe FBM para printar
            return fbm_obj
        else:
            print(f"ASIN {asin} não encontrado no banco de dados.")
            return None

    except SQLAlchemyError as e:
        print(f"Erro SQLAlchemy ao buscar ASIN {asin}: {str(e)}")
        return None
    except Exception as e:
        print(f"Um erro inesperado ocorreu ao buscar ASIN {asin}: {str(e)}")
        return None

# -- Update --
def atualizar_fbm_campos_especificos(
    asin_para_atualizar: str, 
    novo_asin_valor: str = _VALOR_NAO_ALTERAR, 
    product_id: int = _VALOR_NAO_ALTERAR,
    last_price: float = _VALOR_NAO_ALTERAR,
    current_price: float = _VALOR_NAO_ALTERAR,
    supplier: str = _VALOR_NAO_ALTERAR,
    stock: int = _VALOR_NAO_ALTERAR,
    prime_stock: int = _VALOR_NAO_ALTERAR,
    all_stock: int = _VALOR_NAO_ALTERAR,
    gap_stock: int = _VALOR_NAO_ALTERAR,
    promotion: str = _VALOR_NAO_ALTERAR
):
    """
    Atualiza campos específicos de um registro FBM existente.
    O registro é identificado pelo `asin_para_atualizar`. O próprio ASIN pode ser alterado
    para `novo_asin_valor` se não houver conflito.

    Args:
        asin_para_atualizar (str): O ASIN atual do registro FBM a ser modificado.
        novo_asin_valor (str, optional): O novo valor para o ASIN do registro.
        product_id (int, optional): O novo ID do produto associado.
        # ... outros campos ...
    Returns:
        bool: True se a atualização for bem-sucedida e algum campo foi alterado,
              False caso contrário (registro não encontrado, erro, ou nenhuma alteração feita).
    """
    
    asin_para_atualizar = asin_para_atualizar.strip()
    if not asin_para_atualizar:
        print("Erro: O ASIN para identificar o registro a ser atualizado não pode ser vazio.")
        return False
        
    try:
        fbm_obj = session.query(FBM).filter_by(asin=asin_para_atualizar).first()
        if not fbm_obj:
            print(f"ASIN '{asin_para_atualizar}' não encontrado para atualização.")
            return False

        campos_atualizados = 0
        asin_original_para_log = fbm_obj.asin # Para logs, caso o ASIN seja alterado

        # Tentar atualizar o ASIN primeiro, se solicitado
        if novo_asin_valor is not _VALOR_NAO_ALTERAR:
            novo_asin_stripped = novo_asin_valor.strip()
            if not novo_asin_stripped:
                print(f"Aviso: Novo valor para ASIN não pode ser vazio. O ASIN do registro '{asin_original_para_log}' não será alterado.")
            elif novo_asin_stripped != fbm_obj.asin: # Somente se for diferente do ASIN atual
                # Verificar se o novo ASIN já existe para outro registro
                conflito_obj = session.query(FBM).filter(FBM.asin == novo_asin_stripped).first()
                if conflito_obj and conflito_obj.id != fbm_obj.id:
                    print(f"Erro: O ASIN '{novo_asin_stripped}' já está em uso por outro registro (ID={conflito_obj.id}). O ASIN do registro '{asin_original_para_log}' não será alterado.")
                else:
                    print(f"ASIN do registro ID={fbm_obj.id} será alterado de '{fbm_obj.asin}' para '{novo_asin_stripped}'.")
                    fbm_obj.asin = novo_asin_stripped
                    campos_atualizados += 1
        
        # Atualizar product_id
        if product_id is not _VALOR_NAO_ALTERAR and fbm_obj.product_id != product_id:
            produto_associado = session.query(Product).filter_by(id=product_id).first()
            if not produto_associado:
                print(f"Aviso: Produto com ID={product_id} não encontrado. O product_id para ASIN '{fbm_obj.asin}' (original: '{asin_original_para_log}') não será alterado.")
            else:
                fbm_obj.product_id = product_id
                campos_atualizados += 1
        
        #  Atualização dos outros campos
        if last_price is not _VALOR_NAO_ALTERAR and fbm_obj.last_price != last_price:
            fbm_obj.last_price = last_price
            campos_atualizados += 1
        if current_price is not _VALOR_NAO_ALTERAR and fbm_obj.current_price != current_price:
            fbm_obj.current_price = current_price
            campos_atualizados += 1
        if supplier is not _VALOR_NAO_ALTERAR:
            supplier_stripped = supplier.strip() if supplier is not None else None
            if fbm_obj.supplier != supplier_stripped:
                fbm_obj.supplier = supplier_stripped
                campos_atualizados += 1
        if stock is not _VALOR_NAO_ALTERAR and fbm_obj.stock != stock:
            fbm_obj.stock = stock
            campos_atualizados += 1
        if prime_stock is not _VALOR_NAO_ALTERAR and fbm_obj.prime_stock != prime_stock:
            fbm_obj.prime_stock = prime_stock
            campos_atualizados += 1
        if all_stock is not _VALOR_NAO_ALTERAR and fbm_obj.all_stock != all_stock:
            fbm_obj.all_stock = all_stock
            campos_atualizados += 1
        if gap_stock is not _VALOR_NAO_ALTERAR and fbm_obj.gap_stock != gap_stock:
            fbm_obj.gap_stock = gap_stock
            campos_atualizados += 1
        if promotion is not _VALOR_NAO_ALTERAR:
            promotion_stripped = promotion.strip() if promotion is not None else None
            if fbm_obj.promotion != promotion_stripped:
                fbm_obj.promotion = promotion_stripped
                campos_atualizados += 1

        if campos_atualizados > 0:
            session.commit()
            return True
        else:
            print(f"Nenhum campo foi especificado para alteração ou os valores são os mesmos para o ASIN '{asin_original_para_log}'. Nenhuma atualização realizada.")
            return False

    except SQLAlchemyError as e:
        session.rollback()
        print(f"Erro SQLAlchemy ao atualizar FBM para ASIN (original): {asin_para_atualizar}: {str(e)}")
        return False
    except Exception as e:
        session.rollback()
        print(f"Um erro inesperado ocorreu ao atualizar FBM para ASIN (original): {asin_para_atualizar}: {str(e)}")
        return False

# -- Delete --
def deletar_fbm_por_asin(asin: str):
    """
    Deleta um registro FBM do banco de dados com base no ASIN.

    Args:
        asin (str): O ASIN do registro FBM a ser deletado.

    Returns:
        bool: True se a deleção for bem-sucedida, False caso contrário.
    """
    asin = asin.strip()
    if not asin:
        print("Erro: ASIN para deleção não pode ser vazio.")
        return False
    try:
        fbm_obj = session.query(FBM).filter_by(asin=asin).first()

        if fbm_obj:
            fbm_id_deletado = fbm_obj.id 
            session.delete(fbm_obj)
            session.commit()
            print(f"ASIN '{asin}' (ID={fbm_id_deletado}) deletado com sucesso.")
            return True
        else:
            print(f"ASIN '{asin}' não encontrado para deleção.")
            return False

    except SQLAlchemyError as e:
        session.rollback()
        print(f"Erro SQLAlchemy ao deletar FBM para ASIN '{asin}': {str(e)}")
        return False
    except Exception as e:
        session.rollback()
        print(f"Um erro inesperado ocorreu ao deletar FBM para ASIN '{asin}': {str(e)}")
        return False