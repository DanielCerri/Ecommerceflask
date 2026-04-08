import sqlite3
from flask import g

class Database():
    
    def __init__(self):
        #Definindo o caminho do banco 
        self.caminhoBanco=r"F:\daniel\cosmeticos\models\banco.db"
    
    def get_conn(self):
        #Abre a conexao apenas se ela não existir 
        #similiar o Open() do C#
        if "db" not in g:
            g.db = sqlite3.connect(self.caminhoBanco)
            #Configurando para acessar as colunas da tabela pelo nome
            #Similar ao reader["coluna"] do C#
            g.db.row_factory=sqlite3.Row 
        return g.db 
    
    #Funcao para executar (UPDATE,DELETE,INSERT,ETC..)
    def execute_non_query(self,sql,*params):
        conn = self.get_conn()
        cursor = conn.cursor() 
        cursor.execute(sql,params)
        conn.commit()
        
        
    #Função para execuatar query (consulta comando SELECT)
    def execute_query(self,sql,*params):
        conn = self.get_conn()
        cursor= conn.cursor()
        cursor.execute(sql,params)
        return cursor.fetchall()
        
        