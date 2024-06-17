from flask import Flask, render_template, session, url_for, redirect, request, Response, flash
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
import os
from dotenv import load_dotenv
import pandas as pd

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


print(os.getenv('OPENAI_API_KEY'))
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))


def perguntar(messages):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",  # gpt-4o
        response_format={"type": "text"},
        messages=messages
    )
    return response.choices[0].message.content
    # return "david melhor supremo adc irelia-king"


@app.route('/', methods=['POST', 'GET'])
def chatgpt():
    if request.method == 'POST':
        lista = []
        for campeao in Campeoes.query.all():
            lista.append({
                'id': campeao.id,
                'nome': campeao.nome,
                'lane': campeao.lane,
                'dificuldade': campeao.dificuldade,
                'descricao': campeao.descricao,
                'categoria': campeao.categoria,
                'tipoCombate': campeao.tipoCombate
            })

        vusr = f'''
            Dificuldade do campeão: "{request.form['1']}",
            Lane do campeão: "{request.form['2']}",
            Categoria do campeão: "{request.form['3']}",
            Tipo de combate do campeão "{request.form['4']}",
        '''

        vstm = f'''
            Você é um verificador de similaridade, dado a base abaixo, determine o id de um campeão mais similar a afirmação do usuário.

            1\ Se a afirmação do usuário não for encontrada na base, retorne -1.
            2\ Retorne apenas os ids dos campeões mais similares em um vetor, sem nenhum outro texto, assim como no modelo de resposta abaixo.
            3\ Seja extremamente preciso com a comparação dos campos indicados, retorne apenas os que são condizentes com a informação do usuário.
            4\ Retorne apenas os que tem a similaridade maior que 75%.

            Modelo de resposta: [id1, id2, id3, ...].

            Base de dados: {lista}


            Afirmações do usuário: 
        '''

        msgs = [
            {"role": "system", "content": "Você é um analista verificador de similaridade"},
            {"role": "system", "content": vstm},
            {"role": "user", "content": vusr}
        ]
        resposta = perguntar(msgs)

        ids = resposta.replace('[', '').replace(']', '').split(',')

        def champs(x): return Campeoes.query.filter_by(id=x).first()

        return render_template("questao.html", resposta=resposta, campeoes=[champs(int(x)) for x in ids])
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

if __name__ == "__main__":
    app.run()
