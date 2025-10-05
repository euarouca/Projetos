# crud_asin.py

from sqlalchemy.exc import SQLAlchemyError
from database import session, FBM, Product 

_VALOR_NAO_ALTERAR = object()

# --- Create ---
def adicionar_asin(
    product_id: int,
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
    Adiciona um novo ASIN (FBM), associado a um produto existente.
    Retorna uma tupla: (objeto FBM, booleano indicando se foi criado).
    """
    asin = asin.strip()

    produto_associado = session.query(Product).filter_by(id=product_id).first()
    if not produto_associado:
        print(f"Erro: Produto com ID={product_id} não encontrado. Não é possível adicionar ASIN '{asin}'.")
        return None, False

    asin_existente = session.query(FBM).filter_by(asin=asin).first()
    if asin_existente:
        # Se o ASIN já existe, retorna o objeto e False (não foi criado agora)
        return asin_existente, False

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
        # Se foi criado com sucesso, retorna o objeto e True
        return novo_fbm, True
    except SQLAlchemyError as e:
        session.rollback()
        print(f'Erro SQLAlchemy ao adicionar FBM para ASIN="{asin}": {str(e)}')
        return None, False
    except Exception as e:
        session.rollback()
        print(f"Um erro inesperado ocorreu ao adicionar FBM para ASIN '{asin}': {str(e)}")
        return None, False

# --- O restante do arquivo crud_asin.py (visualizar, atualizar, deletar) pode continuar o mesmo ---

# -- Read --
def visualizar_asin(asin: str):
    asin = asin.strip()
    try:
        fbm_obj = session.query(FBM).filter_by(asin=asin).first()

        if fbm_obj:
            print(str(fbm_obj))
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
        asin_original_para_log = fbm_obj.asin

        if novo_asin_valor is not _VALOR_NAO_ALTERAR:
            novo_asin_stripped = novo_asin_valor.strip()
            if not novo_asin_stripped:
                print(f"Aviso: Novo valor para ASIN não pode ser vazio. O ASIN do registro '{asin_original_para_log}' não será alterado.")
            elif novo_asin_stripped != fbm_obj.asin:
                conflito_obj = session.query(FBM).filter(FBM.asin == novo_asin_stripped).first()
                if conflito_obj and conflito_obj.id != fbm_obj.id:
                    print(f"Erro: O ASIN '{novo_asin_stripped}' já está em uso por outro registro (ID={conflito_obj.id}). O ASIN do registro '{asin_original_para_log}' não será alterado.")
                else:
                    print(f"ASIN do registro ID={fbm_obj.id} será alterado de '{fbm_obj.asin}' para '{novo_asin_stripped}'.")
                    fbm_obj.asin = novo_asin_stripped
                    campos_atualizados += 1
        
        if product_id is not _VALOR_NAO_ALTERAR and fbm_obj.product_id != product_id:
            produto_associado = session.query(Product).filter_by(id=product_id).first()
            if not produto_associado:
                print(f"Aviso: Produto com ID={product_id} não encontrado. O product_id para ASIN '{fbm_obj.asin}' (original: '{asin_original_para_log}') não será alterado.")
            else:
                fbm_obj.product_id = product_id
                campos_atualizados += 1
        
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