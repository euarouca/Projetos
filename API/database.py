from sqlalchemy import create_engine, Column, String, Integer, Float, ForeignKey, UniqueConstraint, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base, relationship 
import os
import textwrap


# --- Configuração do Banco de Dados ---
# Define o caminho do banco de dados no mesmo diretório do script
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'maguire.db')
db_connection_string = f'sqlite:///{db_path}'
db = create_engine(db_connection_string) 
 
Session = sessionmaker(bind=db)
session = Session()

Base = declarative_base()

# --- Definição das Classes ORM ---
class Product(Base):
    __tablename__ = 'produtos'
    # Garante que a combinação de partNumber e Pack seja única para cada produto.
    __table_args__ = (UniqueConstraint('partNumber', 'pack', name='uix_partnumber_pack'),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    brand = Column(String)
    partNumber = Column(String, index=True, nullable=False) 
    pack = Column(Integer, nullable=False) 
    
    fbms = relationship("FBM", back_populates="product")

    def __init__(self, partNumber, pack, brand):
        self.brand = brand
        self.partNumber = partNumber
        self.pack = pack

    def __repr__(self):
        return f"<Product(id={self.id}, partNumber='{self.partNumber}', pack={self.pack})>"

    def __str__(self):
        details = f"""
        ------------------------------
        Produto ID: {self.id if self.id else "Não Salvo"}
        ------------------------------
        Marca: {self.brand if self.brand else "N/A"}
        Part Number: {self.partNumber}
        Pack: {self.pack}
        ------------------------------
        """
        return textwrap.dedent(details).strip()

class FBM(Base):
    __tablename__ = 'fbm'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('produtos.id'), nullable=False)
    asin = Column(String, index=True, unique=True, nullable=False) # asin único e não nulo
    last_price = Column(Float) # preço da última atualização
    current_price = Column(Float) # preço atual 
    supplier = Column(String) # nome do fornecedor
    stock = Column(Integer) # estoque do fornecedor escolhido
    prime_stock = Column(Integer) # estoque do melhores fornecedores
    all_stock = Column(Integer) # estoque de todos os fornecedores somados
    gap_stock = Column(Integer) # diferença da última atualização de ALL_STOCK para essa
    promotion = Column(String) # está em promoção ?
    
    product = relationship("Product", back_populates="fbms")
    
    def __init__(self, product_id, asin, last_price=None, current_price=None, supplier=None, stock=None, prime_stock=None, all_stock=None, gap_stock=None, promotion=None):
        self.product_id = product_id # Added product_id to constructor
        self.asin = asin
        self.last_price = last_price
        self.current_price = current_price
        self.supplier = supplier
        self.stock = stock
        self.prime_stock = prime_stock
        self.all_stock = all_stock
        self.gap_stock = gap_stock
        self.promotion = promotion

    def __repr__(self):
        return f"<FBM(id={self.id}, asin='{self.asin}')>"

    def __str__(self):
        product_info = f" (Produto ID: {self.product.id}, PartNumber: {self.product.partNumber}, Pack: {self.product.pack})" if self.product else ""
        details = f"""
        ====================================
        ASIN: {self.asin if self.asin else "N/A"}{product_info}

        Preços:
          Preço Atual:             $ {self.current_price if self.current_price is not None else "N/A"}
          Último Preço Registrado: $ {self.last_price if self.last_price is not None else "N/A"}

        Estoque:
          Fornecedor Escolhido:    {self.stock if self.stock is not None else "N/A"}
          Melhores Fornecedores:   {self.prime_stock if self.prime_stock is not None else "N/A"}
          Todos Fornecedores:      {self.all_stock if self.all_stock is not None else "N/A"}
          Diferença de Estoque:    {self.gap_stock if self.gap_stock is not None else "N/A"}

        Promoção:                  {self.promotion if self.promotion else "N/A"}
        Produto Associado ID:      {self.product_id if self.product_id is not None else "N/A"}
        ====================================
        """
        return textwrap.dedent(details).strip()

class Distributor(Base):
    __tablename__ = 'distribuidores'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, index=True, unique=True, nullable=False) # Nome do distribuidor é único e não nulo
    prime = Column(Boolean, default=False, nullable=False) # pertence aos melhores distribuidores

    def __init__(self, name, prime=False):
        self.name = name
        self.prime = prime

    def __repr__(self):
        return f"<Distributor(id={self.id}, name='{self.name}', prime={self.prime})>" 

    def __str__(self):
        prime_status = "Sim" if self.prime else "Não"
        details = f"""
        ------------------------------
        Distribuidor (ID: {self.id if self.id else 'Não Salvo'})
        ------------------------------
        Nome: {self.name}
        Prime: {prime_status}
        ------------------------------
        """
        return textwrap.dedent(details).strip()
    
class DistributorData(Base):
    __tablename__ = 'dados_distribuidor'
    __table_args__ = (UniqueConstraint('distributor_name', 'partNumber', 'pack', name='uix_dist_partnumber_pack'),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    distributor_name = Column(String, ForeignKey('distribuidores.name', ondelete='CASCADE', onupdate='CASCADE'), index=True, nullable=False)
    sku = Column(String)
    partNumber = Column(String, nullable=False)
    pack = Column(Integer, nullable=False)
    price = Column(Float)
    stock = Column(Integer)

    distributor_relationship = relationship("Distributor", backref="data_entries")

    def __init__(self, distributor_name: str, partNumber: str, pack: int, price: float, stock: int, sku: str = None):
        self.distributor_name = distributor_name
        self.partNumber = partNumber
        self.sku = sku
        self.pack = pack
        self.price = price
        self.stock = stock

    def __repr__(self):
        return (f"<DistributorData(id={self.id}, "
                f"distributor_name='{self.distributor_name}', "
                f"partNumber='{self.partNumber}', pack={self.pack})>")

    def __str__(self):
        dist_display_name = self.distributor_name
        dist_prime_status = "N/A"
        if self.distributor_relationship:
            dist_display_name = self.distributor_relationship.name
            dist_prime_status = "Sim" if self.distributor_relationship.prime else "Não"


        details = f"""
        --------------------------------------
        Dados do Distribuidor (ID: {self.id if self.id else 'Não Salvo'})
        --------------------------------------
        Distribuidor: {dist_display_name} (Prime: {dist_prime_status})
        Part Number:  {self.partNumber}
        Pack:         {self.pack}
        SKU:          {self.sku if self.sku else "N/A"}
        Preço: R$     {self.price if self.price is not None else "N/A"}
        Estoque:      {self.stock if self.stock is not None else "N/A"}
        --------------------------------------
        """
        return textwrap.dedent(details).strip()

if __name__ == "__main__":
    print(f"Usando banco de dados em: {db_connection_string}")
    Base.metadata.create_all(db)
    print("Tabelas criadas (ou já existentes).")