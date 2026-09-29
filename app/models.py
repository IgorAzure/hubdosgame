from app import db

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    steam_id = db.Column(db.String(50), unique = True, nullable = False)
    nome = db.Column(db.String(100), nullable = False)
    foto = db.Column(db.String(255))
    jogos = db.relationship('Jogo', backref='dono', lazy = True)

class Jogo(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    titulo = db.Column(db.String(100), nullable = False)
    genero = db.Column(db.String(50), nullable = False)
    status = db.Column(db.String(20), default = 'Wishlist')
    #migrate
    steam_appid = db.Column(db.Integer, nullable = True)
    #stranger danger
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable = True)
    
    tempo_historia = db.Column(db.String(20), nullable=True)
    tempo_extra = db.Column(db.String(20), nullable=True)
    tempo_completo = db.Column(db.String(20), nullable=True)
    tempo_solo = db.Column(db.String(20), nullable=True)
    tempo_coop = db.Column(db.String(20), nullable=True)
    tempo_vs = db.Column(db.String(20), nullable=True)