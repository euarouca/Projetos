from sqlalchemy.exc import SQLAlchemyError
from database import session, Distributor, DistributorData 

_VALOR_NAO_ALTERAR = object()

# --- Create ---
def adicionar_distribuidor(name: str, prime: bool = False):
    name = name.strip()

    distribuidor_existente = session.query(Distributor).filter_by(name=name).first()
    if distribuidor_existente:
        print(f'Aviso: Distribuidor com nome "{name}" já existe.')
        return distribuidor_existente

    novo_distribuidor = Distributor(name=name, prime=prime)
    try:
        session.add(novo_distribuidor)
        session.commit()
        return novo_distribuidor
    except SQLAlchemyError as e:
        session.rollback()
        print(f'Erro SQLAlchemy ao adicionar distribuidor {name}. Erro: {str(e)}')
        return None
    except Exception as e:
        session.rollback()
        print(f"Um erro inesperado ocorreu ao adicionar distribuidor {name}. Erro: {str(e)}")
        return None


# -- Read --
def visualizar_distribuidor(name: str):
    name = name.strip()
    try:
        distribuidor = session.query(Distributor).filter_by(name=name).first()
        if distribuidor:
            print(str(distribuidor)) # Utiliza o __str__ da classe Distributor
            return distribuidor
        else:
            print(f"Distribuidor com nome {name} não encontrado no banco de dados.")
            return None

    except SQLAlchemyError as e:
        print(f"Erro SQLAlchemy ao buscar distribuidor {name}: {str(e)}")
        return None
    except Exception as e:
        print(f"Um erro inesperado ocorreu ao buscar distribuidor {name}: {str(e)}")
        return None

# -- Update --
def atualizar_distribuidor(
    name_original: str,
    novo_name: str = _VALOR_NAO_ALTERAR,
    novo_prime: bool = _VALOR_NAO_ALTERAR
):

    name_original = name_original.strip()
    try:
        distribuidor = session.query(Distributor).filter_by(name=name_original).first()

        if not distribuidor:
            print(f"Distribuidor com nome {name_original} não encontrado para atualização.")
            return False

        campos_atualizados = 0

        if novo_name is not _VALOR_NAO_ALTERAR and novo_name.strip() != distribuidor.name:
            novo_name_stripped = novo_name.strip()
            # Verifica se o novo nome já existe para outro distribuidor
            conflito = session.query(Distributor).filter(
                Distributor.name == novo_name_stripped,
                Distributor.id != distribuidor.id
            ).first()
            if conflito:
                print(f"Erro: Já existe um distribuidor com o nome '{novo_name_stripped}' (ID={conflito.id}). Atualização de nome cancelada.")
            else:
                distribuidor.name = novo_name_stripped
                campos_atualizados += 1
        
        if novo_prime is not _VALOR_NAO_ALTERAR and novo_prime != distribuidor.prime:
            distribuidor.prime = novo_prime
            campos_atualizados += 1

        if campos_atualizados > 0:
            session.commit()
            print(f"Distribuidor ID={distribuidor.id} (Original: '{name_original}') atualizado com sucesso. {campos_atualizados} campo(s) modificado(s).")
            print(f"Novos dados: Nome='{distribuidor.name}', Prime={distribuidor.prime}")
            return True
        else:
            print(f"Nenhum campo foi especificado para alteração ou os valores são os mesmos para o distribuidor '{name_original}'. Nenhuma atualização realizada.")
            return False

    except SQLAlchemyError as e:
        session.rollback()
        print(f"Erro SQLAlchemy ao atualizar distribuidor {name_original}: {str(e)}")
        return False
    except Exception as e:
        session.rollback()
        print(f"Um erro inesperado ocorreu ao atualizar distribuidor {name_original}: {str(e)}")
        return False

# -- Delete --
def deletar_distribuidor(name: str):
    name = name.strip()

    try:
        distribuidor = session.query(Distributor).filter_by(name=name).first()
        if not distribuidor:
            print(f"Distribuidor com nome {name} não encontrado para deleção.")
            return False

        # Contar dados associados em DistributorData para informar o usuário
        dados_associados_count = session.query(DistributorData).filter_by(distributor_name=distribuidor.name).count()

        print(f"\n--- Confirmação de Deleção ---")
        print(f"Distribuidor a ser deletado: {distribuidor.name}")

        if dados_associados_count > 0:
            print(f"Este distribuidor possui {dados_associados_count} registro(s) de dados de produto associados.")
            print("Estes registros de dados também serão DELETADOS automaticamente.")
        else:
            print("Este distribuidor não possui dados de produto associados.")

        confirmacao = input(f"Você tem certeza que deseja deletar o distribuidor {name} e todos os seus dados de produto associados? (s/N): ").strip().lower()

        if confirmacao != 's':
            print("Deleção cancelada pelo usuário.")
            return False

        dist_id_deletado = distribuidor.id
        session.delete(distribuidor)
        session.commit()
        print(f"{name} e seus dados de produto associados foram deletados com sucesso.")
        return True

    except SQLAlchemyError as e:
        session.rollback()
        print(f"Erro SQLAlchemy ao deletar distribuidor {name}: {str(e)}")
        return False
    except Exception as e:
        session.rollback()
        print(f"Um erro inesperado ocorreu ao deletar distribuidor {name}: {str(e)}")
        return False

