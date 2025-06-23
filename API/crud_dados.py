from sqlalchemy.exc import SQLAlchemyError
from database import session, Distributor, DistributorData

_VALOR_NAO_ALTERAR = object()

# --- Create / Update ---
def adicionar_dados_distribuidor(distributor_name: str, partNumber: str, pack: int, price: float, stock: int, sku: str = None, quiet: bool = False):
    """
    Adiciona ou ATUALIZA dados de um produto para um distribuidor.
    - Se a combinação de distributor_name, partNumber e pack não existir, cria um novo registro.
    - Se já existir, atualiza o preço, estoque e SKU com os novos valores.

    Args:
        distributor_name (str): Nome do distribuidor.
        partNumber (str): Part number do produto.
        pack (int): Quantidade do pack do produto.
        price (float): Novo preço do produto.
        stock (int): Novo estoque do produto.
        sku (str, optional): Novo SKU do produto.
        quiet (bool): Se True, suprime as mensagens de sucesso.

    Returns:
        DistributorData: O objeto criado ou atualizado. None em caso de erro.
    """
    
    distributor_name = distributor_name.strip()
    partNumber = partNumber.strip()

    distribuidor_existente = session.query(Distributor).filter_by(name=distributor_name).first()
    if not distribuidor_existente:
        if not quiet:
            print(f"Erro: Distribuidor '{distributor_name}' não encontrado.")
        return None

    try:
        dados_existente = session.query(DistributorData).filter_by(
            distributor_name=distributor_name,
            partNumber=partNumber,
            pack=pack
        ).first()

        if dados_existente:
            # --- LÓGICA DE ATUALIZAÇÃO ---
            dados_existente.price = price
            dados_existente.stock = stock
            dados_existente.sku = sku
            # Nenhuma mensagem de "aviso", apenas atualiza.
            session.commit()
            return dados_existente
        else:
            # --- LÓGICA DE CRIAÇÃO ---
            novo_dado = DistributorData(
                distributor_name=distributor_name,
                partNumber=partNumber,
                pack=pack,
                price=price,
                stock=stock,
                sku=sku
            )
            session.add(novo_dado)
            session.commit()
            return novo_dado

    except SQLAlchemyError as e:
        session.rollback()
        if not quiet:
            print(f"Erro SQLAlchemy ao processar dados para {partNumber}: {e}")
        return None
    except Exception as e:
        session.rollback()
        if not quiet:
            print(f"Erro inesperado ao processar dados para {partNumber}: {e}")
        return None

# -- Read --
def visualizar_dados_distribuidor(distributor_name: str, partNumber: str, pack: int):
    """
    Busca e exibe os detalhes de um registro de DistributorData pela sua chave única.

    Args:
        distributor_name (str): Nome do distribuidor.
        partNumber (str): Part number do produto.
        pack (int): Pack do produto.

    Returns:
        DistributorData: O objeto DistributorData encontrado, ou None.
    """
    distributor_name = distributor_name.strip()
    partNumber = partNumber.strip()
    try:
        dados_obj = session.query(DistributorData).filter_by(
            distributor_name=distributor_name,
            partNumber=partNumber,
            pack=pack
        ).first()

        if dados_obj:
            print(str(dados_obj))
            return dados_obj
        else:
            print(f"Dados não encontrados para {distributor_name}, {partNumber}, Pack {pack}.")
            return None
    except SQLAlchemyError as e:
        print(f"Erro SQLAlchemy ao buscar dados: {distributor_name}, {partNumber}, Pack {pack}. Erro: {str(e)}")
        return None
    except Exception as e:
        print(f"Erro inesperado ao buscar dados: {distributor_name}, {partNumber}, Pack {pack}. Erro: {str(e)}")
        return None


# -- Update --
def atualizar_dados_distribuidor(
    distributor_name_original: str,
    partNumber_original: str,
    pack_original: int,
    novo_distributor_name: str = _VALOR_NAO_ALTERAR,
    novo_partNumber: str = _VALOR_NAO_ALTERAR,
    novo_pack: int = _VALOR_NAO_ALTERAR,
    novo_price: float = _VALOR_NAO_ALTERAR,
    novo_stock: int = _VALOR_NAO_ALTERAR,
    novo_sku: str = _VALOR_NAO_ALTERAR
):
    """
    Atualiza campos específicos de um registro DistributorData existente.
    O registro é identificado pela combinação original de distributor_name, partNumber e pack.
    A alteração de distributor_name, partNumber ou pack requer verificação de unicidade.

    Args:
        distributor_name_original (str): Nome original do distribuidor do registro a ser atualizado.
        partNumber_original (str): PartNumber original do registro a ser atualizado.
        pack_original (int): Pack original do registro a ser atualizado.
        novo_distributor_name (str, optional): Novo nome do distribuidor.
        novo_partNumber (str, optional): Novo part number.
        novo_pack (int, optional): Novo pack.
        novo_price (float, optional): Novo preço.
        novo_stock (int, optional): Novo estoque.
        novo_sku (str, optional): Novo SKU.

    Returns:
        bool: True se a atualização for bem-sucedida e algum campo foi alterado,
              False caso contrário.
    """
    distributor_name_original = distributor_name_original.strip()
    partNumber_original = partNumber_original.strip()

    try:
        dados_obj = session.query(DistributorData).filter_by(
            distributor_name=distributor_name_original,
            partNumber=partNumber_original,
            pack=pack_original
        ).first()

        if not dados_obj:
            print(f"Registro de dados não encontrado para {distributor_name_original}, {partNumber_original}, Pack {pack_original}.")
            return False

        id_dados_obj = dados_obj.id # Salva o ID para verificação de conflito
        campos_atualizados = 0
        
        # Valores que compõem a chave única, para verificar se serão alterados
        pending_dist_name = dados_obj.distributor_name
        pending_pn = dados_obj.partNumber
        pending_pack = dados_obj.pack

        if novo_distributor_name is not _VALOR_NAO_ALTERAR:
            novo_dist_name_stripped = novo_distributor_name.strip()
            if novo_dist_name_stripped != pending_dist_name:
                # Verificar se o novo distribuidor existe
                distribuidor_valido = session.query(Distributor).filter_by(name=novo_dist_name_stripped).first()
                if not distribuidor_valido:
                    print(f"Aviso: Novo nome de {novo_dist_name_stripped} não encontrado. O nome do distribuidor não será alterado.")
                else:
                    pending_dist_name = novo_dist_name_stripped
        
        if novo_partNumber is not _VALOR_NAO_ALTERAR:
            novo_pn_stripped = novo_partNumber.strip()
            if novo_pn_stripped != pending_pn:
                pending_pn = novo_pn_stripped

        if novo_pack is not _VALOR_NAO_ALTERAR and novo_pack != pending_pack:
            pending_pack = novo_pack

        # Verificar conflito de UniqueConstraint se algum componente da chave foi alterado
        key_potentially_changed = (pending_dist_name != dados_obj.distributor_name or
                                   pending_pn != dados_obj.partNumber or
                                   pending_pack != dados_obj.pack)

        if key_potentially_changed:
            conflito = session.query(DistributorData).filter(
                DistributorData.distributor_name == pending_dist_name,
                DistributorData.partNumber == pending_pn,
                DistributorData.pack == pending_pack,
                DistributorData.id != id_dados_obj # Exclui o próprio registro da verificação
            ).first()
            if conflito:
                print(f"Erro: A combinação {pending_dist_name}, {pending_pn}, Pack {pending_pack} já existe para outro registro (ID={conflito.id}). As chaves não serão alteradas.")
            else: # Se não há conflito, aplicar as mudanças de chave
                if pending_dist_name != dados_obj.distributor_name:
                    dados_obj.distributor_name = pending_dist_name
                    campos_atualizados +=1
                if pending_pn != dados_obj.partNumber:
                    dados_obj.partNumber = pending_pn
                    campos_atualizados +=1
                if pending_pack != dados_obj.pack:
                    dados_obj.pack = pending_pack
                    campos_atualizados +=1
        
        # Atualizar outros campos
        if novo_price is not _VALOR_NAO_ALTERAR and dados_obj.price != novo_price:
            dados_obj.price = novo_price
            campos_atualizados += 1
        if novo_stock is not _VALOR_NAO_ALTERAR and dados_obj.stock != novo_stock:
            dados_obj.stock = novo_stock
            campos_atualizados += 1
        if novo_sku is not _VALOR_NAO_ALTERAR:
            sku_stripped = novo_sku.strip() if novo_sku is not None else None
            if dados_obj.sku != sku_stripped:
                dados_obj.sku = sku_stripped
                campos_atualizados += 1
        
        if campos_atualizados > 0:
            session.commit()
            return True
        else:
            print(f"Nenhum campo foi especificado para alteração ou os valores são os mesmos para o registro {distributor_name_original}, {partNumber_original}, Pack {pack_original}. Nenhuma atualização realizada.")
            return False

    except SQLAlchemyError as e:
        session.rollback()
        print(f"Erro SQLAlchemy ao atualizar dados {distributor_name_original}, {partNumber_original}, Pack {pack_original}: {str(e)}")
        return False
    except Exception as e:
        session.rollback()
        print(f"Um erro inesperado ocorreu ao atualizar dados {distributor_name_original}, {partNumber_original}, Pack {pack_original}: {str(e)}")
        return False
    

# -- Delete --
def deletar_dados_distribuidor(distributor_name: str, partNumber: str, pack: int):
    """
    Deleta um registro específico de DistributorData pela combinação de
    distributor_name, partNumber e pack.

    Args:
        distributor_name (str): Nome do distribuidor do registro a ser deletado.
        partNumber (str): PartNumber do registro a ser deletado.
        pack (int): Pack do registro a ser deletado.

    Returns:
        bool: True se a deleção for bem-sucedida, False caso contrário.
    """
    distributor_name = distributor_name.strip()
    partNumber = partNumber.strip()

    try:
        dados_obj = session.query(DistributorData).filter_by(
            distributor_name=distributor_name,
            partNumber=partNumber,
            pack=pack
        ).first()

        if not dados_obj:
            print(f"Registro de dados não encontrado para {distributor_name}, {partNumber}, Pack {pack} para deleção.")
            return False

        id_dados_log = dados_obj.id 
        session.delete(dados_obj)
        session.commit()
        print(f"{id_dados_log}, {distributor_name}, {partNumber}, {pack} deletado com sucesso.")
        return True

    except SQLAlchemyError as e:
        session.rollback()
        print(f"Erro SQLAlchemy ao deletar dados {distributor_name}, {partNumber}, {pack}: {str(e)}")
        return False
    except Exception as e:
        session.rollback()
        print(f"Um erro inesperado ocorreu ao deletar dados {distributor_name}, {partNumber}, {pack}: {str(e)}")
        return False

