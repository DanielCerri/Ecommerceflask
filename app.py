from flask import Flask,g,render_template,request,redirect,url_for,flash,session,send_from_directory
from models.database import Database
from models.classproduto import Produto
import os
#import smtplib

app = Flask(__name__)
#O APP.SECRET_KEY É UMA CAMADA DE SERGURANÇA OBRIGATÓRIA DO FLASK
#ELE SERVE PARA ASSINAR A SESSÃO ATUAL DO NAVEGADOR E OS COOKIES DE ARMAZENAMENTO
#ASSIM O NAVEGADOR SABE QUE SE TIVER ALGUMA REQUISIÇÃO COM ESSA CHAVE SECRETA CONTIDA NELA
#É O NOSSO PROPRIO SERVIDOR QUE ESTA SE COMUNICANDO E NÃO ALGUM HACKER TENTANDO
#SIMULAR A SESSÃO! O FLASH E O SESSION DO FLASK SO FUNCIONAM COM O SECRET KEY
app.secret_key="DS1BACKEND"
# UPLOAD_FOLDER=r"F:\daniel\cosmeticos\uploads"


base_dir = os.path.abspath(os.path.dirname(__file__))

# Define o UPLOAD_FOLDER combinando o base_dir com a pasta 'uploads'
UPLOAD_FOLDER = os.path.join(base_dir, 'uploads')

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['DEBUG'] = True



#Rede do senai bloqueia a porta 2525
# def EnviarEmailTeste(msg):
#     # Dados fornecidos pelo painel do Mailtrap
#     usuario = ""
#     senha = ""
    
#     sender = "Private Person <from@example.com>"
#     receiver = f"{session.get('email')}"

#     message = f"""\ {msg}"""

#     with smtplib.SMTP("sandbox.smtp.mailtrap.io", 2525) as server:
#         server.starttls()
#         server.login(usuario, senha)
#         server.sendmail(sender, receiver, message)


#Configurando o metodo magico do flask para automaticamente fechar conexao
# com o banco de dados
@app.teardown_appcontext
def close_connection(exception):
    db_conn = g.pop('db',None)
    if db_conn is not None:
        db_conn.close()
        print("CONEXÃO ENCERRADA COM SUCESSO!!")

banco = Database()


@app.route("/")
def index():
    
    banco.execute_non_query(r"""
    CREATE TABLE IF NOT EXISTS TESTE(
    id INTEGER PRIMARY KEY AUTOINCREMENT,   
    nome  varchar(100)  
    );  
    """)
    
    #criando tabela de produtos
    banco.execute_non_query(r""" 
    CREATE TABLE IF NOT EXISTS Produtos(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome varchar(255),
    preco  REAL(10,2),
    pastaimagem varchar(255),
    nomeimagem varchar(255) 
    );                    
    """)
    
    #Criando tabela de Usuarios
    banco.execute_non_query(r"""
    CREATE TABLE IF NOT EXISTS Usuarios(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email varchar(255),
    senha varchar(500)  
    );                    
    """)
    
    #Criando tabela de itens do carrinho de compras
    banco.execute_non_query(r"""  
    CREATE TABLE IF NOT EXISTS item_carrinho(
    id_item_lista INTEGER PRIMARY KEY AUTOINCREMENT,    
    id_carrinho INTEGER ,
    email varchar(255),
    id_item INTEGER NOT NULL,
    status varchar(20),
    FOREIGN KEY("id_item") references produtos ("id") 
    );""")
    
    
    
    
    return render_template('./loja/login.html')


@app.route("/cadastro")
def cadastro():
    return render_template("./loja/cadastro.html")

@app.route("/cadastrar",methods=["POST"])
def cadastrar():
    #O certo seria criar a classe usuario e instanciar o objetos
    #Porem como a classe é preguiçosa criamos 2 variaveis locais
    email = request.form["email"]
    senha= request.form["senha"]
    
    banco.execute_non_query(r"""
    insert into usuarios(email,senha) values (?,?)""",email,senha)

    flash("CONTA CRIADA COM SUCESSO!")
    return redirect(url_for('index'))

@app.route("/entrar",methods=["POST"])
def entrar():
    email = request.form["email"]
    senha = request.form["senha"]
    
    dados = banco.execute_query(r"""
    SELECT * FROM USUARIOS WHERE email=? and senha =?""",email,senha)

    if dados:
        session['email']=email # Crio a sessão com o email da conta!
        
        #Obtendo o idcarrinho no banco para inserir os itens posteriormente 
        # e armazenando na sessão do usuario!
        
        #Lógica do SELECT:
        #Se for a primeira vez que o usuario entra no site e nao tiver nenhum carrinho retornamos o id 0
        #Se ele ja tiver algum carrinho de compras, retornamos o id desse carrinho
        #Se ele ja tiver algum carrinho porem o status for diferente de "pendente"
        #Ele gera um novo idcarrinho para o usuario fazer uma nova compra
        
        idcarrinho = banco.execute_query(r"""
        SELECT 
        IIF( MAX(id_carrinho) is NULL AND status IS null, 0 , 
        IIF( status="pendente",id_carrinho,MAX(id_carrinho) + 1 )) 
        as idcarrinho from item_carrinho WHERE email=?; """,session.get('email'))
        
        session["idcarrinho"]=idcarrinho[0]["idcarrinho"]
        
        return redirect(url_for("portal"))
    else:
        flash("EMAIL OU SENHA INCORRETOS")
        return redirect(url_for("index"))


@app.route("/portal")
def portal():
    return render_template("portal.html")


@app.route("/cadprod")
def cadprod():
    return render_template('./produtos/cadprod.html')

@app.route("/postprod",methods=["POST"])
def postprod():
    obj = Produto()
    obj.produto = request.form["nome"]
    obj.preco=request.form["preco"]
    obj.imagem=""
    
    #Capturando o arquivo de imagem do produto
    arquivo= request.files["imagem"]
    
    if arquivo.filename!="":
        nomearquivo=f"{arquivo.filename}" 
        obj.imagem=os.path.join(UPLOAD_FOLDER,nomearquivo)
        arquivo.save(obj.imagem)
    
        banco.execute_non_query(r"""
        INSERT INTO Produtos(nome,preco,pastaimagem,nomeimagem) values(?,?,?,?)"""
        ,obj.produto,obj.preco,UPLOAD_FOLDER,nomearquivo)
    
    return redirect(url_for('produtoscadastrados'))


@app.route("/imagem/<id>")
def testeimagem(id):
    
    obj = Produto()
    dados=banco.execute_query(r"""
    SELECT NOMEIMAGEM FROM PRODUTOS WHERE ID = ? """,id)
    obj.imagem=dados[0]["nomeimagem"]
    return send_from_directory(UPLOAD_FOLDER,obj.imagem)
    
    

@app.route("/produtoscadastrados")
def produtoscadastrados():
    
    dados = banco.execute_query(r"""
    SELECT * FROM Produtos;                            
                                """)
    
    
    return render_template('./produtos/produtoscadastrados.html',produtos=dados)


@app.route("/excluir/<int:id>")
def excluirprod(id):
    
    if id !="":
        banco.execute_non_query(r"""
        DELETE FROM PRODUTOS WHERE ID = ? ;                         
                                """,id)
    
    return redirect(url_for('produtoscadastrados'))


@app.route("/alterar/<int:id>")
def alterar(id):
    
    if id !="":
        
        dados= banco.execute_query(r"""
                SELECT * FROM PRODUTOS WHERE ID = ? ; 
                """,id)
        
        return render_template("./produtos/alterarprod.html",prods=dados)


@app.route("/alterarprod",methods=["POST"])
def alterarprod():
    obj = Produto()
    obj.id=request.form['id']
    obj.produto=request.form['nome']
    obj.preco=request.form['preco']
    
    banco.execute_non_query(r"""
    UPDATE PRODUTOS SET NOME=?,PRECO=? WHERE ID=?;
    """,obj.produto,obj.preco,obj.id )
    
    return redirect(url_for('produtoscadastrados'))
    
    
#------------------------------Parte da Loja - Clientes-----------------------------

#Campos da tabela produto : id,nome,preco
@app.route("/loja")
def loja():
    
    #Verificando se tem email armazenado na session 
    #Se tiver ele entra na loja , se não direciona o usuario para o login
    if session.get("email"):
        dados = banco.execute_query(r"""SELECT * FROM PRODUTOS;""")
        return  render_template("./loja/loja.html",produtos=dados)
    else:
        flash("Voce precisa estar logado para comprar!")
        return redirect(url_for("index"))

@app.route("/logout")
def logout():
    #Removendo o email autenticado da sessão e redirecionando o usuario para o login
    #session.pop()-> remove o item da sessão , exemplo(session.pop("email") remove o email)
    #session.clear()-> remove todos os itens da sessão, se tivesse session["email"] session["nome"] session["cpf"] iria excluir tudo!
    session.pop("email")
    return redirect(url_for('index'))

    
@app.route("/carrinho/<int:iditem>")
def carrinho(iditem):
    
    banco.execute_non_query(r"""
    INSERT INTO ITEM_CARRINHO(id_carrinho,email,id_item,status) values (?,?,?,?)""",
    session.get("idcarrinho"),session.get("email"),iditem,"pendente")
    
    flash("Produto adicionado no carrinho!")
    
    return redirect(url_for("loja"))    


@app.route("/pagamento")
def pagamento():
    #Logica para buscar os itens da tabela ITEM_CARRINHO e exibir na tela de pagamento
    
    dados = banco.execute_query(r"""
    SELECT * FROM item_carrinho AS ic INNER JOIN Produtos p 
    ON ic.id_item = p.id where id_carrinho=? and status="pendente" and email=? ;""",
    session.get("idcarrinho"),session.get('email'))
    
    
    return render_template("./loja/pagamento.html",carrinhop = dados)


@app.route("/removeritem/<int:iditemlista>")
def removeritem(iditemlista):
	
    banco.execute_non_query(r"""
    DELETE FROM ITEM_CARRINHO WHERE ID_CARRINHO = ? AND ID_ITEM_LISTA=? ;""",
    session.get("idcarrinho"),iditemlista)
    
 
    return redirect(url_for('pagamento'))


@app.route("/finalizarcompra")
def finalizarcompra():
    
    banco.execute_non_query(r"""
    UPDATE ITEM_CARRINHO SET STATUS="PAGO" WHERE
    EMAIL = ? AND ID_CARRINHO=? """,session.get('email'),session.get('idcarrinho'))
    
    flash("COMPRA EFETUADA COM SUCESO!")
    
    
    return redirect(url_for('loja'))
    
