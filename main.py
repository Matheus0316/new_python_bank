"""
Desafio DIO
"""
import pprint
from random import randint
from datetime import datetime
import pymongo as pym
from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Float
from sqlalchemy import ForeignKey
from sqlalchemy import create_engine
from sqlalchemy import select
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import Session


Base = declarative_base()

class ClienteBd(Base):
    """
    Essa classe apresenta a representação do cliente no banco de dados
    """
    __tablename__ = 'CLIENTE'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    nome = Column(String(60))
    cpf = Column(String(11))
    endereco = Column(String(30))

    def __repr__(self):
        return f"cliente (id={self.id}, nome={self.nome}, cpf={self.cpf}, endereco={self.endereco})"

class ContaBd(Base):
    """
    Essa classe apresenta a representação da conta no banco de dados
    """
    __tablename__ = 'CONTA'

    id = Column(Integer, primary_key=True, autoincrement=True, unique=True)
    tipo = Column(String(8))
    agencia = Column(String(4))
    numero = Column(String(9), unique=True)
    id_cliente = Column(Integer, ForeignKey('CLIENTE.id'), nullable=False)
    saldo = Column(Float)

engine = create_engine("sqlite:///banco.bd")

Base.metadata.create_all(engine)


client = pym.MongoClient("mongodb+srv://Pymongo:1234@cluster0.yeddhku.mongodb.net/?retryWrites=true&w=majority")
db = client["bancoNoSql"]
collection = db.extrato


class Cliente():
    """
    Classe cliente
    """
    def __init__(self, id, nome, cpf, endereco, contas = []):
        self._id = id
        self._nome = nome
        self._cpf = cpf
        self._endereco = endereco
        self._contas = contas


    @property
    def id(self):
        """retorna o id

        Returns:
            string: id
        """
        return self._id

    @property
    def nome(self):
        """retorna o nome

        Returns:
            string: nome
        """
        return self._nome

    @nome.setter
    def nome(self, nome):
        self._nome = nome

        with Session(engine) as session:

            stmt = select(ClienteBd).where(ClienteBd.cpf.in_([self._id]))

            for cliente in session.scalars(stmt):
                cliente.nome = nome
                session.close()

    @property
    def cpf(self):
        """retorna o cpf

        Returns:
            string: cpf
        """
        return self._cpf

    @property
    def endereco(self):
        """retorna o endereco

        Returns:
            string: endereco
        """
        return self._endereco

    @endereco.setter
    def endereco(self, endereco):
        self._endereco = endereco

        with Session(engine) as session:

            stmt = select(ClienteBd).where(ClienteBd.cpf.in_([self._id]))

            for cliente in session.scalars(stmt):
                cliente.endereco = endereco
                session.close()

    @property
    def contas(self):
        """retorna o contas

        Returns:
            string: contas
        """
        return self._contas

    def vincular_contas(self, contas):
        """função responsavel por vincular as contas com o seu respectivo dono

        Args:
            cliente (Cliente): cliente
            contas (list(Conta)): lista de clientes
        """
        try:
            for conta in contas:
                if self._id == conta.id_cliente:
                    cliente.contas.append(conta)
        except:
            if self._id == contas.id_cliente:
                    cliente.contas.append(contas)

    def excluir_cliente(self):
        """função responsavel por excluir um cliente junto de suas contas
        """
        for conta in self._contas:
            conta.excluir_conta()

        with Session(engine) as session:
            cliente = session.query(ClienteBd).filter_by(id = self.id).one()
            session.delete(cliente)
            session.commit()
            session.close()





    def __repr__(self):
        return f"""Id: {self._id}
Nome: {self._nome}
cpf: {self._cpf}
Endereço: {self._endereco}
Numero de contas: {len(self._contas)}"""



class Conta():
    """
    classe conta
    """
    def __init__(self, id, tipo, agencia, numero, id_cliente, saldo = 0.0):
        self._id = id
        self._tipo = tipo
        self._agencia = agencia
        self._numero = numero
        self._id_cliente = id_cliente
        self._saldo = saldo

    @property
    def id(self):
        """retorna o id

        Returns:
            string: id
        """
        return self._id

    @property
    def tipo(self):
        """retorna o tipo

        Returns:
            string: tipo
        """
        return self._tipo

    @property
    def agencia(self):
        """retorna o agencia

        Returns:
            string: agencia
        """
        return self._agencia

    @property
    def numero(self):
        """retorna o numero

        Returns:
            string: numero
        """
        return self._numero

    @property
    def id_cliente(self):
        """retorna o id_cliente

        Returns:
            string: id_cliente
        """
        return self._id_cliente

    @property
    def saldo(self):
        """retorna o saldo

        Returns:
            string: saldo
        """
        return self._saldo

    def depositar(self, valor):
        """Altera o saldo de forma positiva

        Args:
            valor (float): valor do deposito
        """
        self._saldo += valor

        with Session(engine) as session:
            conta = session.query(ContaBd).filter_by(id = self.id).one()
            conta.saldo = self._saldo
            session.commit()
            session.close()

        post = {
            "idCliente": self._id_cliente,
            "tipoConta": self._tipo,
            "numeroConta": self._numero,
            "transação": "Deposito",
            "valor": valor,
            "data": datetime.utcnow()
        }

        collection.insert_one(post)

    def sacar(self, valor):
        """Altera o saldo de forma negativa

        Args:
            valor (float): valor do deposito
        """
        self._saldo -= valor
        with Session(engine) as session:
            conta = session.query(ContaBd).filter_by(id = self.id).one()
            conta.saldo = self._saldo
            session.commit()
            session.close()

        post = {
            "idCliente": self._id_cliente,
            "tipoConta": self._tipo,
            "numeroConta": self._numero,
            "transação": "Saque",
            "valor": valor,
            "data": datetime.utcnow()
        }

        collection.insert_one(post)

    def extrato(self):
        """Função responsavel por exibir as transações feitas por uma conta

        Returns:
            list: lista de transições
        """
        transacoes = []
        for post in collection.find({"numeroConta": self._numero}):
            transacoes.append(post)

        return transacoes

    def excluir_conta(self):
        """ Função responsavel por deletar as contas cadastradas no banco de dados relacional
            e seus respectivos extratos cadastrados no banco não relacional
        """
        resultado = collection.delete_many({"numeroConta": self._numero})
        print(f"{resultado.deleted_count} documentos foram excluídos.")

        with Session(engine) as session:
            conta = session.query(ContaBd).filter_by(id = self.id).one()
            session.delete(conta)
            session.commit()
            session.close()


    def __repr__(self):
        return f"""\nId: {self._id}
Tipo: {self._tipo}
Agencia: {self._agencia}
Numero: {self._numero}
Saldo: {self._saldo}"""




def criar_cliente(nome, cpf, endereco):
    """função para criar um cliente

    Args:
        nome (string): nome do cliente
        cpf (string): cpf do cliente
        endereco (string): endereco do cliente
    """
    with Session(engine) as session:
        cliente = ClienteBd(
            nome = nome,
            cpf = cpf,
            endereco = endereco
        )

        session.add(cliente)
        session.commit()

        stmt = select(ClienteBd).where(ClienteBd.cpf.in_([cpf]))
        for cliente in session.scalars(stmt):
            session.close()
            print("Cliente criado com sucesso")

def get_cliente(cpf):
    """Função para buscar um cliente no bnco de dados pelo cpf

    Args:
        cpf (string): cpf do cliente

    Returns:
        Cliente: cliente presente no banco de dados com cpf correspondente
    """
    with Session(engine) as session:
        stmt = select(ClienteBd)
        for cliente in session.scalars(stmt):
            if cliente.cpf == cpf:
                session.close()
                return Cliente(cliente.id, cliente.nome, cliente.cpf, cliente.endereco, get_contas(cliente.id))
        while True:
            cpf = input("Erro: Não existe um cliente com esse cpf. Digite um cpf cadastrado (Digite 'Q' para cancelar a ação): ").upper()
            if cpf == 'Q':
                return 0
            return get_cliente(cpf)

def criar_conta(tipo, agencia, numero, id_cliente):
    """Função para criar contas

    Args:
        tipo (string): tipo de conta
        agencia (string): agencia da conta
        numero (sting): numero da conta
        id_cliente (string):
    """
    with Session(engine) as session:
        conta = ContaBd(
            tipo=tipo,
            agencia=agencia,
            numero=numero,
            id_cliente=id_cliente,
            saldo=0.0
        )
        session.add(conta)
        session.commit()
        session.close()

def get_conta(numero_conta):
    """Função para buscar uma conta no banco de dados pelo numero

    Args:
        numero (string): numero da conta

    Returns:
        Conta: conta presente no banco de dados com numero correspondente
    """
    with Session(engine) as session:
        stmt = select(ContaBd)
        for conta in session.scalars(stmt):
            if conta.numero == numero_conta:
                return Conta(conta.id, conta.tipo, conta.agencia, conta.numero, conta.id_cliente, conta.saldo)
        print("Erro: Não existe uma conta com esse numero")
        return 0

def get_contas(id_cliente):
    """Função para buscar todas as contas no banco de dados

        Returns:
            list(Conta): contas presentes no banco de dados
    """
    contas = []
    with Session(engine) as session:
        stmt = select(ContaBd)
        for conta_bd in session.scalars(stmt):
            if id_cliente == conta_bd.id_cliente:
                contas.append(Conta(conta_bd.id, conta_bd.tipo, conta_bd.agencia, conta_bd.numero, conta_bd.id_cliente, conta_bd.saldo))
        return contas

def gerar_numero_conta():
    """A função deve criar um numero de 9 dígitos e verificar se ele já está no banco de dados

    Returns:
        String: numero da conta
    """
    digitos = [str(randint(0, 9)) for c in range(9)]

    numero_digitos = ''.join(digitos)


    with Session(engine) as session:
        stmt = select(ContaBd)
        for conta in session.scalars(stmt):
            if numero_digitos == conta.numero:
                return gerar_numero_conta()
        return numero_digitos

MENU = """
Escolha a operação:
CC = Criar cliente
NC = Nova conta
D = Deposito
S = Saque
E = Extrato
EX = Excluir cliente
Q = sair
    """

AGENCIA = '0001'
while True:

    print(MENU)
    escolha = input('').upper()
    if escolha == 'CC':
        nome = input('Informe o nome do cliente: ')
        cpf_cliente = input('Informe o cpf do cliente: ')
        while len(cpf_cliente) != 11:
            cpf_cliente = input('CPF inválido. Informe um cpf válido: ')
        endereco = input('Informe o endereco do cliente: ')
        criar_cliente(nome, cpf_cliente, endereco)

    elif escolha == 'NC':
        cpf_cliente = input('Informe o cpf do dono da conta: ')

        while len(cpf_cliente) != 11:
            cpf_cliente = input("CPF inválido. Informe um cpf válido (Digite 'Q' para cancelar a ação): ").upper()
            if cpf_cliente == 'Q':
                break

        cliente = get_cliente(cpf_cliente)

        if cliente == 0:
            break

        tipo = input('Informe o tipo da conta: ').upper()

        while tipo != "POUPANCA" and tipo != "CORRENTE":
            tipo = input('Tipo inválido. Informe um tipo válido').upper()

        numero = gerar_numero_conta()

        criar_conta(tipo, AGENCIA, numero, cliente.id)
        cliente.vincular_contas(get_conta(numero))
        print(f'Nova conta criada com sucesso. Lista de contas do(a) {cliente.nome}: ')
        print(cliente.contas)

    elif escolha == "D":
        cpf_cliente = input('Informe o cpf do dono da conta: ')
        while len(cpf_cliente) != 11:
            cpf_cliente = input('CPF inválido. Informe um cpf válido: ')

        cliente = get_cliente(cpf_cliente)

        escolha_conta = input(f"""informe o numero de uma das contas conta: {cliente.contas}:
""")
        for conta in cliente.contas:
            if conta.numero == escolha_conta:
                valor = int(input('Quanto você deseja depositar ? '))
                conta.depositar(valor)

    elif escolha == "S":
        cpf_cliente = input('Informe o cpf do dono da conta: ')
        while len(cpf_cliente) != 11:
            cpf_cliente = input('CPF inválido. Informe um cpf válido: ')

        cliente = get_cliente(cpf_cliente)

        escolha_conta = input(f"""informe o numero de uma das contas conta: {cliente.contas}:
""")
        for conta in cliente.contas:
            if conta.numero == escolha_conta:
                valor = int(input('Quanto você deseja sacar ? '))
                conta.sacar(valor)

    elif escolha == "EC":
        cpf_cliente = input('Informe o cpf do dono da conta: ')
        while len(cpf_cliente) != 11:
            cpf_cliente = input('CPF inválido. Informe um cpf válido: ')

        cliente = get_cliente(cpf_cliente)
        escolha_conta = input(f"""informe o numero de uma das contas conta: {cliente.contas}:
""")
        conta = get_conta(escolha_conta)

        print("=-=-=-=-=- Extrato =-=-=-=-=-")
        pprint.pprint(conta.extrato())
        print(f"O saldo atual é: R${conta.saldo}")

    elif escolha == "EX":
        cpf_cliente = input('Informe o cpf do dono da conta: ')
        while len(cpf_cliente) != 11:
            cpf_cliente = input('CPF inválido. Informe um cpf válido: ')
        cliente = get_cliente(cpf_cliente)

        cliente.excluir_cliente()
        print("Cliente excluido com sucesso")

    elif escolha == "Q":
        break

    else:
        print("Opção inválida")
