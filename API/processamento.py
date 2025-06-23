from sqlalchemy.orm import joinedload
from database import session, FBM, Product, DistributorData, Distributor
from crud_asin import atualizar_fbm_campos_especificos


def todos_dados_para_asin(asin: str):
    """
    Busca todos os dados relacionados a um produto a partir de seu ASIN.
    """
    asin = asin.strip()
    fbm_entry = session.query(FBM).options(joinedload(FBM.product)).filter(FBM.asin == asin).first()
    if not fbm_entry or not fbm_entry.product:
        return None
    distributor_entries = session.query(DistributorData).options(
        joinedload(DistributorData.distributor_relationship)
    ).filter(
        DistributorData.partNumber == fbm_entry.product.partNumber,
        DistributorData.pack == fbm_entry.product.pack
    ).all()
    return {
        "fbm_data": fbm_entry,
        "product_data": fbm_entry.product,
        "distributor_data": distributor_entries
    }


def verificar_promocao(dados_distribuidores: list[DistributorData]) -> str:
    """
    Verifica se o menor preço pode ser considerado uma promoção.
    """
    precos = [oferta.price for oferta in dados_distribuidores if oferta.price is not None]
    if len(precos) < 3:
        return ''
    menor_preco = min(precos)
    soma_dos_outros_precos = sum(precos) - menor_preco
    if (len(precos) - 1) == 0:
        return ''
    media_dos_outros_precos = soma_dos_outros_precos / (len(precos) - 1)
    limite_promocao = media_dos_outros_precos * 0.6
    if menor_preco <= limite_promocao:
        return 'ok'
    else:
        return ''


def analisar_melhor_oferta(dados_distribuidores: list[DistributorData]) -> dict:
    """
    Analisa uma lista de ofertas para encontrar a melhor opção com base nas regras de negócio.
    """
    if not dados_distribuidores:
        return {}
    estoque_total, estoque_prime = 0, 0
    melhor_oferta_geral, oferta_digikey_mouser, oferta_rs_allied = None, None, None
    for oferta in dados_distribuidores:
        if oferta.price is None or oferta.stock is None: continue
        estoque_total += oferta.stock
        if oferta.distributor_relationship and oferta.distributor_relationship.prime:
            estoque_prime += oferta.stock
        if melhor_oferta_geral is None or oferta.price < melhor_oferta_geral.price:
            melhor_oferta_geral = oferta
        if oferta.distributor_name in ('DigiKey', 'Mouser'):
            if oferta_digikey_mouser is None or oferta.price < oferta_digikey_mouser.price:
                oferta_digikey_mouser = oferta
        if oferta.distributor_name == 'RS (Formerly Allied Electronics)':
            oferta_rs_allied = oferta
    if melhor_oferta_geral is None: return {}
    melhor_oferta_top_tres = None
    if oferta_rs_allied and oferta_digikey_mouser:
        gap_top_tres = oferta_digikey_mouser.price - oferta_rs_allied.price
        if abs(gap_top_tres) < 5:
            melhor_oferta_top_tres = oferta_digikey_mouser if oferta_digikey_mouser.price < oferta_rs_allied.price else oferta_rs_allied
        else:
            melhor_oferta_top_tres = oferta_rs_allied if oferta_rs_allied.price < oferta_digikey_mouser.price else oferta_digikey_mouser
    elif oferta_digikey_mouser: melhor_oferta_top_tres = oferta_digikey_mouser
    elif oferta_rs_allied: melhor_oferta_top_tres = oferta_rs_allied
    oferta_final = melhor_oferta_geral
    if melhor_oferta_top_tres:
        preco_top_tres = melhor_oferta_top_tres.price
        preco_geral = melhor_oferta_geral.price
        gap_preco = preco_top_tres - preco_geral
        if (preco_top_tres <= preco_geral * 1.13) or (gap_preco >= 0 and gap_preco <= 20):
            oferta_final = melhor_oferta_top_tres
    return {'price': oferta_final.price, 'supplier': oferta_final.distributor_name, 'stock': oferta_final.stock, 'all_stock': estoque_total, 'prime_stock': estoque_prime}


def processar_e_atualizar_fbm(asin: str) -> bool:
    """
    Orquestra o processo completo de análise e atualização para um único ASIN.
    """
    dados_completos = todos_dados_para_asin(asin)

    if not dados_completos:
        print(f"AVISO: Nenhum registro FBM encontrado para o ASIN {asin}.")
        return False
        
    fbm_original = dados_completos["fbm_data"]
    lista_de_ofertas_bruta = dados_completos.get("distributor_data", [])

    antigo_current_price = fbm_original.current_price
    antigo_all_stock = fbm_original.all_stock or 0

    # Filtra a lista para desconsiderar ofertas com estoque zerado ou nulo
    ofertas_em_estoque = [
        oferta for oferta in lista_de_ofertas_bruta if oferta.stock and oferta.stock > 0
    ]

    # Lógica para quando não há nenhuma oferta com estoque
    if not ofertas_em_estoque:
        print(f"AVISO: Nenhuma oferta COM ESTOQUE foi encontrada para o ASIN {asin}. Atualizando registro para sem estoque.")
        
        # Chama a atualização para zerar os campos e definir o fornecedor como 'nenhum'
        sucesso = atualizar_fbm_campos_especificos(
            asin_para_atualizar=asin,
            last_price=antigo_current_price,
            current_price=0.0,        # Preço atual definido como 0.0
            supplier='nenhum',         # Fornecedor definido como 'nenhum'
            stock=0,                   # Estoque do fornecedor zerado
            prime_stock=0,             # Estoque prime zerado
            all_stock=0,               # Estoque total zerado
            gap_stock=0 - antigo_all_stock, # Calcula o gap com base no estoque antigo
            promotion=''               # Garante que não fique como promoção
        )
        return sucesso

    # --- Se houver estoque, o processo continua normalmente ---
    melhor_oferta = analisar_melhor_oferta(ofertas_em_estoque)
    status_promocao = verificar_promocao(ofertas_em_estoque)

    if not melhor_oferta:
        print(f"AVISO: Nenhuma oferta válida foi determinada pela análise para o ASIN {asin}. A atualização será ignorada.")
        return False

    novo_preco = melhor_oferta['price']
    novo_fornecedor = melhor_oferta['supplier']
    novo_estoque_fornecedor = melhor_oferta['stock']
    novo_all_stock = melhor_oferta['all_stock']
    novo_prime_stock = melhor_oferta['prime_stock']
    
    gap_stock = novo_all_stock - antigo_all_stock
    
    sucesso = atualizar_fbm_campos_especificos(
        asin_para_atualizar=asin,
        last_price=antigo_current_price,
        current_price=novo_preco,
        supplier=novo_fornecedor,
        stock=novo_estoque_fornecedor,
        prime_stock=novo_prime_stock,
        all_stock=novo_all_stock,
        gap_stock=gap_stock,
        promotion=status_promocao
    )
        
    return sucesso


def atualizar_todos_os_fbm():
    """
    Busca todos os ASINs no banco de dados e executa o processo de análise e
    atualização para cada um deles em lote.
    """
    print("Iniciando a atualização em lote de todos os registros FBM...")
    try:
        resultados = session.query(FBM.asin).all()
        asins_a_processar = [item[0] for item in resultados]
        if not asins_a_processar:
            print("Nenhum ASIN encontrado no banco de dados para processar.")
            return
        total = len(asins_a_processar)
        print(f"Encontrados {total} ASINs para processar.")
        sucessos, falhas = 0, 0
        for i, asin in enumerate(asins_a_processar, 1):
            # print(f"\n({i}/{total}) Processando ASIN: {asin}")
            try:
                if processar_e_atualizar_fbm(asin):
                    sucessos += 1
                    # print(f"--> SUCESSO na atualização do ASIN {asin}.")
                else:
                    falhas += 1
                    print(f"--> FALHA ou nenhuma alteração necessária para o ASIN {asin}.")
            except Exception as e:
                falhas += 1
                print(f"--> ERRO CRÍTICO ao processar ASIN {asin}: {e}")
        print("\n" + "="*40)
        print("--- RESUMO DA ATUALIZAÇÃO EM LOTE ---")
        print(f"Total de ASINs processados: {total}")
        print(f"  - Sucessos: {sucessos}")
        print(f"  - Falhas/Ignorados: {falhas}")
        print("="*40)
    except Exception as e:
        print(f"\nOcorreu um erro ao buscar a lista de ASINs: {e}")