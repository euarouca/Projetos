from sqlalchemy.exc import SQLAlchemyError
from database import session, Product, FBM

_VALOR_NAO_ALTERAR = object()

# --- Create ---
def adicionar_produto(partNumber: str, pack: int, brand: str, quiet: bool = False):
    """
    Adiciona um novo produto se ele não existir. Não faz nada se já existir.
    """
    partNumber = partNumber.strip()
    
    produto_existente = session.query(Product).filter_by(partNumber=partNumber, pack=pack).first()
    if produto_existente:
        if not quiet: # Suprime a mensagem se 'quiet' for True
            print(f'Aviso: Produto = {partNumber}, Pack = {pack} já existe ID = {produto_existente.id}')
        return produto_existente
    
    novo_produto = Product(partNumber, pack, brand)
    
    try:
        session.add(novo_produto)
        session.commit()
        return novo_produto
    except SQLAlchemyError as e:
        session.rollback()
        if not quiet:
            print(f'Erro ao adicionar produto Produto = {partNumber} Pack = {pack}: {str(e)}')
        return None
    except Exception as e:
        session.rollback()
        if not quiet:
            print(f"Um erro inesperado ocorreu ao adicionar Produto = {partNumber} Pack = {pack}: {str(e)}")
        return None    

# -- Read --
def visualizar_produto(partNumber: str, pack=1):
    partNumber = partNumber.strip()
    try:
        query = session.query(Product).filter_by(partNumber=partNumber, pack=pack).first()
        if query:
            print(str(query)) #Utiliza o __str__ para printar
            return query
        else:
            print(f"Produto {partNumber} Pack {pack} não encontrado no banco de dados.")
            return None
            
    except SQLAlchemyError as e:
        print(f"Erro ao buscar Produto {partNumber}: {str(e)}")
        return None
    except Exception as e:
        print(f"Um erro inesperado ocorreu ao buscar Produto {partNumber}: {str(e)}")
        return None

# -- Update -- 
def atualizar_produto(
    partNumber_original: str,
    pack_original: int,
    novo_partNumber: str = _VALOR_NAO_ALTERAR,
    novo_pack: int = _VALOR_NAO_ALTERAR,
    nova_brand: str = _VALOR_NAO_ALTERAR
):
    partNumber_original = partNumber_original.strip()
    try:
        produto = session.query(Product).filter_by(partNumber=partNumber_original, pack=pack_original).first()
        if not produto:
            print(f"Produto PartNumber={partNumber_original}, Pack={pack_original} não encontrado para atualização.")
            return False

        campos_atualizados = 0

        # Prepara os novos valores, mantendo os originais se não forem alterados
        pn_final = produto.partNumber
        pack_final = produto.pack

        if novo_partNumber is not _VALOR_NAO_ALTERAR and novo_partNumber.strip() != produto.partNumber:
            pn_final = novo_partNumber.strip()
            campos_atualizados += 1
        if novo_pack is not _VALOR_NAO_ALTERAR and novo_pack != produto.pack:
            pack_final = novo_pack
            campos_atualizados += 1

        # Verifica se a nova combinação de partNumber e pack já existe (e não é o próprio produto)
        if (pn_final != produto.partNumber or pack_final != produto.pack):
            conflito = session.query(Product).filter(
                Product.partNumber == pn_final,
                Product.pack == pack_final,
                Product.id != produto.id # Exclui o próprio produto da verificação de conflito
            ).first()
            if conflito:
                print(f"Erro: Já existe um produto com PartNumber={pn_final} e Pack={pack_final} (ID={conflito.id}). Atualização cancelada.")
                return False

        # Aplica as alterações se não houver conflito ou se não foram alterados partNumber/pack
        if novo_partNumber is not _VALOR_NAO_ALTERAR and novo_partNumber.strip() != produto.partNumber:
             produto.partNumber = novo_partNumber.strip()
        if novo_pack is not _VALOR_NAO_ALTERAR and novo_pack != produto.pack:
            produto.pack = novo_pack
        if nova_brand is not _VALOR_NAO_ALTERAR and nova_brand.strip().upper() != produto.brand:
            produto.brand = nova_brand.strip().upper()
            campos_atualizados += 1 

        if campos_atualizados > 0:
            session.commit()
            print(f"Produto ID={produto.id} (Original: PN={partNumber_original}, Pack={pack_original}) atualizado com sucesso. {campos_atualizados} campo(s) modificado(s).")
            print(f"Novos dados: PartNumber={produto.partNumber}, Pack={produto.pack}, Marca={produto.brand}")
            return True
        else:
            print(f"Nenhum campo foi especificado para alteração ou os valores são os mesmos para o produto PartNumber={partNumber_original}, Pack={pack_original}. Nenhuma atualização realizada.")
            return False

    except SQLAlchemyError as e:
        session.rollback()
        print(f"Erro SQLAlchemy ao atualizar produto PartNumber={partNumber_original}, Pack={pack_original}: {str(e)}")
        return False
    except Exception as e:
        session.rollback()
        print(f"Um erro inesperado ocorreu ao atualizar produto PartNumber={partNumber_original}, Pack={pack_original}: {str(e)}")
        return False

# -- Delete --
def deletar_produto(partNumber: str, pack: int):
    partNumber = partNumber.strip()
    try:
        produto = session.query(Product).filter_by(partNumber=partNumber, pack=pack).first()

        if not produto:
            print(f"Produto PartNumber={partNumber}, Pack={pack} não encontrado para deleção.")
            return False

        asins_associados = session.query(FBM).filter_by(product_id=produto.id).all()

        print(f"\n--- Confirmação de Deleção ---")
        print(f"Produto a ser deletado: ID={produto.id}, PartNumber={produto.partNumber}, Pack={produto.pack}, Marca={produto.brand}")

        if asins_associados:
            print(f"Este produto possui {len(asins_associados)} ASIN(s) (FBMs) associados:")
            for fbm_item in asins_associados:
                print(f"  - ASIN: {fbm_item.asin}")
            print("Estes ASINs também serão DELETADOS.")
        else:
            print("Este produto não possui ASINs (FBMs) associados.")

        confirmacao = input("Você tem certeza que deseja deletar este produto e seus ASINs associados? (s/N): ").strip().lower()

        if confirmacao != 's':
            print("Deleção cancelada pelo usuário.")
            return False

        # Deletar ASINs (FBMs) associados primeiro
        if asins_associados:
            for fbm_item in asins_associados:
                session.delete(fbm_item)
            session.flush() # Garante que as deleções de FBM ocorram antes da deleção do produto
            print(f"{len(asins_associados)} ASIN(s) associado(s) foram deletados.")

        # Deletar o produto
        product_id_deletado = produto.id # Salva o ID para a mensagem de log
        session.delete(produto)
        session.commit()
        print(f"Produto PartNumber={partNumber}, Pack={pack} (ID={product_id_deletado}) e seus ASINs associados foram deletados com sucesso.")
        return True

    except SQLAlchemyError as e:
        session.rollback()
        print(f"Erro SQLAlchemy ao deletar produto PartNumber={partNumber}, Pack={pack}: {str(e)}")
        return False
    except Exception as e:
        session.rollback()
        print(f"Um erro inesperado ocorreu ao deletar produto PartNumber={partNumber}, Pack={pack}: {str(e)}")
        return False