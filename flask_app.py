from flask import Flask, render_template, session, url_for, redirect, request, Response, flash
from flask_sqlalchemy import SQLAlchemy
from openai import OpenAI
# from dotenv import load_dotenv
import os

# load_dotenv()

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
    tipoCombate = db.Column(db.String)
    imagem_url = db.Column(db.String)

    def __init__(self, nome, lane, dificuldade, descricao, tipoCombate, imageUrl):
        self.nome = nome
        self.lane = lane
        self.dificuldade = dificuldade
        self.descricao = descricao
        self.tipoCombate = tipoCombate
        self.imagem_url = imageUrl


client = OpenAI(api_key='CHAVE')


def perguntar(prompt):
    response = client.chat.completions.create(
        model="gpt-3.5-turbo-0125",
        response_format={"type": "text"},
        messages=[
            {"role": "system", "content": "Responda flertando"},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


@app.route('/10010begin7679676-67-97-114-111-108', methods=['POST', 'GET'])
def chatgpt():
    if request.method == 'POST':
        prompt = request.form['questao']
        resposta = perguntar(prompt)
        return render_template("questao.html", resposta=resposta)
    return render_template("questao.html")


@app.route('/10010privatesession7679676-67-97-114-111-108', methods=['POST', 'GET'])
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
    tipoCombate = request.form["tipoCombate"]
    imagem = request.files["imagem"]
    savePath = os.path.join(UPLOAD_FOLDER, imagem.filename)
    imagem.save(savePath)
    campeao = Campeoes(nome, lane, dificuldade,
                       descricao, tipoCombate, f'/static/imagens/{imagem.filename}')
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
    if (request.method == 'POST') and (request.form['username'] == "Toka" and request.form['senha'] == "87105108108"):
        session['username'] = request.form['username']

    return redirect(url_for('adm'))


@app.route('/logout', methods=["POST", "GET"])
def logout():
    session.pop('username', None)
    return redirect(url_for('adm'))


@app.route('/final')
def index():
    return render_template("index.html")


with app.app_context():
    db.create_all()
    db.session.commit()

if __name__ == "__main__":
    app.run()
