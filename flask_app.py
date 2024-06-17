from flask import Flask, render_template, session, url_for, redirect, request, Response, flash
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
import os
from dotenv import load_dotenv
import pandas as pd
from abc import ABC, abstractmethod

load_dotenv(override=True)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///minhabase.sqlite3'
db = SQLAlchemy(app)
app.app_context().push()
app.secret_key = '123456'
# UPLOAD_FOLDER = "/home/AnaCarolina/mysite/imagens"
UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'imagens')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


class Campeoes(db.Model):
    __tablename__ = "campeoes"

    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String, unique=True)
    lane = db.Column(db.String)
    dificuldade = db.Column(db.String)
    descricao = db.Column(db.Text)
    categoria = db.Column(db.String)
    tipoCombate = db.Column(db.String)
    imagem_url = db.Column(db.String)

    def __init__(self, nome, lane, dificuldade, descricao, categoria, tipoCombate, imageUrl):
        self.nome = nome
        self.lane = lane
        self.dificuldade = dificuldade
        self.descricao = descricao
        self.categoria = categoria
        self.tipoCombate = tipoCombate
        self.imagem_url = imageUrl

# Classe que implementa os padrões Singleton e Iterator
class GerenciadorCampeoes():
    __instance = None

    def __new__(cls):
       if GerenciadorCampeoes.__instance is None:
          GerenciadorCampeoes.__instance = super().__new__(cls)
       return GerenciadorCampeoes.__instance
    
    def __init__(self):
        if not hasattr(self, 'iniciado'):
            self.__campeoes = {}
            self.__ids = []
            self.indice = 0
            GerenciadorCampeoes.__instance = self
            self.iniciado = True
    
    def addCampeao(self, campeao):
        self.__ids.append(campeao.id)
        self.__campeoes[campeao.id] = campeao
        
    def getCampeaoById(self, id):
        return self.__campeoes[id]
        
    def __iter__ (self):
        return self    

    def __next__(self):
        if self.indice < len(self.__campeoes):
            campeao = self.__campeoes[self.__ids[self.indice]]
            self.indice += 1
            return campeao
        else:
            self.indice = 0
            raise StopIteration

class CampeaoFlyweight:
    atributos_comuns = {}

    @classmethod
    def get_atributo_comum(cls, lane, dificuldade, categoria, tipoCombate):
        key = (lane, dificuldade, categoria, tipoCombate)
        if key not in cls.atributos_comuns:
            cls.atributos_comuns[key] = (lane, dificuldade, categoria, tipoCombate)
        return cls.atributos_comuns[key]

class Campeao():
    def __init__(self, id, nome, lane, dificuldade, descricao, categoria, tipoCombate, imageUrl):
        self.id = id
        self.nome = nome
        self.atributos_compartilhados = CampeaoFlyweight.get_atributo_comum(lane, dificuldade, categoria, tipoCombate)
        self.descricao = descricao
        self.imagem_url = imageUrl
        
    def getInfo(self):
        dicio = dict()
        dicio["id"] = self.id
        dicio["nome"] = self.nome
        dicio["descricao"] = self.descricao
        dicio["lane"] = self.atributos_compartilhados[0]
        dicio["dificuldade"] = self.atributos_compartilhados[1]
        dicio["categoria"] = self.atributos_compartilhados[2]
        dicio["tipoCombate"] = self.atributos_compartilhados[3]
        dicio["imagem_url"] = self.imagem_url
        return dicio
    
def inicializarGerenciador():
    gerenciadorCampeoes = GerenciadorCampeoes()
        
    for campeao in Campeoes.query.all():
        gerenciadorCampeoes.addCampeao(Campeao(campeao.id, campeao.nome, campeao.lane, campeao.dificuldade, campeao.descricao, campeao.categoria, campeao.tipoCombate, campeao.imagem_url))
        
print(os.getenv('OPENAI_API_KEY'))
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def perguntar(messages):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        response_format={"type": "text"},
        messages=messages
    )
    return response.choices[0].message.content
    # return "david melhor supremo adc irelia-king"


@app.route('/', methods=['POST', 'GET'])
def chatgpt():
    if request.method == 'POST':
        gerenciadorCampeoes = GerenciadorCampeoes()
        
        vusr = f'''
            Dificuldade do campeão: "{request.form['1']}",
            Lane do campeão: "{request.form['2']}",
            Categoria do campeão: "{request.form['3']}",
            Tipo de combate do campeão "{request.form['4']}",
        '''

        vstm = f'''
            Você é um verificador de similaridade, dado a base abaixo, determine os ids mais similares a afirmação do usuário.

            1\ A base de dados segue o seguinte formato: [(id1, nome1, dificuldade1, lane1, categoria1, tipoCombate1), (id2, nome2, dificuldade2, lane2, categoria2, tipoCombate2), ...]
            2\ Retorne apenas os ids dos três campeões mais similares em um vetor, sem nenhum outro texto, assim como no modelo de resposta abaixo.
            3\ O vetor deve estar ordenado decrescentemente do id do campeão mais provável até o menos provável. 
            4\ Seja extremamente preciso com a comparação dos campos indicados, retorne apenas os que são condizentes com a informação do usuário. 

            Modelo de resposta: [id1, id2, id3, ...].

            Base de dados: {[(campeao.getInfo()['id'], campeao.getInfo()['nome'], campeao.getInfo()['dificuldade'], campeao.getInfo()['lane'], campeao.getInfo()['categoria'] ,campeao.getInfo()['tipoCombate']) for campeao in gerenciadorCampeoes]}

            Afirmações do usuário: 
        '''
        print(vstm)
        
        msgs = [
            {"role": "system", "content": vstm},
            {"role": "user", "content": vusr}
        ]
        resposta = perguntar(msgs)

        ids = resposta.replace('[', '').replace(']', '').split(',')

        def champs(x): return gerenciadorCampeoes.getCampeaoById(id=x)

        return render_template("questao.html", resposta=resposta, campeoes=[champs(int(x)).getInfo() for x in ids])
    return render_template("questao.html")


@app.route('/adm', methods=['POST', 'GET'])
def adm():
    if 'username' in session:
        campeoes = Campeoes.query.all()
        return render_template("admin.html", campeoes=campeoes)
    else:
        return '''
        <form action="{}" method="POST">
            <p><input type=text name=username placeholder="Nome">
            <p><input type=text name=senha placeholder="Senha">
            <p><input type=submit value=Login>
        <form>
        '''.format(url_for("login"))


@app.route('/adicionarCampeao', methods=['POST'])
def adicionarCampeao():
    nome = request.form["nome"]
    lane = request.form["lane"]
    dificuldade = request.form["dificuldade"]
    descricao = request.form["descricao"]
    categoria = request.form["categoria"]
    tipoCombate = request.form["tipoCombate"]
    imagem = request.files["imagem"]
    savePath = os.path.join(UPLOAD_FOLDER, imagem.filename)
    imagem.save(savePath)
    campeao = Campeoes(nome, lane, dificuldade,
                       descricao, categoria, tipoCombate, f'/static/imagens/{imagem.filename}')
    db.session.add(campeao)
    db.session.commit()

    return redirect(url_for('adm'))


@app.route('/apagarCampeao', methods=['POST'])
def apagarCampeao():
    campeaoId = request.form["id"]
    Campeoes.query.filter_by(id=campeaoId).delete()
    db.session.commit()
    return redirect(url_for('adm'))


@app.route('/login', methods=['POST'])
def login():
    if (request.method == 'POST') and (request.form['username'] == "Toka" and request.form['senha'] == "1234"):
        session['username'] = request.form['username']

    return redirect(url_for('adm'))


@app.route('/logout', methods=["POST", "GET"])
def logout():
    session.pop('username', None)
    return redirect(url_for('adm'))


@app.route('/index')
def index():
    return render_template("index.html")


with app.app_context():
    db.create_all()
    db.session.commit()
    inicializarGerenciador()

if __name__ == "__main__":
    app.run()
