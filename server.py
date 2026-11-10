from zoneinfo import ZoneInfo
from flask import Flask, jsonify, request, send_from_directory
from flask_socketio import SocketIO, emit
import sqlite3, datetime, uuid, os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'atenco-2026'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
DB = 'alertas.db'

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    return c

def init():
    c = db()
    c.execute('''CREATE TABLE IF NOT EXISTS usuarias (
        id INTEGER PRIMARY KEY AUTOINCREMENT, folio TEXT UNIQUE, folio_cad TEXT,
        nombres TEXT, apellidos TEXT, mac TEXT, edad INTEGER, celular TEXT, otro TEXT,
        hijos INTEGER, notas TEXT, discapacidad TEXT, foto TEXT,
        inicio_medida TEXT, duracion TEXT, fecha_entrega TEXT, fecha_fin TEXT,
        num_carpeta TEXT, imputado TEXT, parentesco TEXT, caracteristicas TEXT,
        calle TEXT, numero TEXT, entre_calles TEXT, referencia TEXT,
        localidad TEXT, municipio TEXT, estado TEXT, cp TEXT,
        adscripcion TEXT, autoridad TEXT, tipo_delito TEXT, status TEXT DEFAULT 'Activo'
    )''')
    c.execute('''CREATE TABLE IF NOT EXISTS alertas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, folio TEXT, lat REAL, lng REAL,
        precision REAL, fecha TEXT, tipo TEXT, mensaje TEXT, estado TEXT DEFAULT 'ACTIVA'
    )''')
    c.commit()
    if c.execute("SELECT count(*) FROM usuarias").fetchone()[0]==0:
        c.execute("INSERT INTO usuarias (folio,folio_cad,nombres,apellidos,mac,edad,celular,otro,hijos,notas,discapacidad,inicio_medida,duracion,fecha_entrega,fecha_fin,num_carpeta,imputado,parentesco,caracteristicas,calle,numero,entre_calles,referencia,localidad,municipio,estado,cp,adscripcion,autoridad,tipo_delito,foto) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        ('582-1877','None','ARACELY','JIMENEZ VALENCIA','C30000400DE9',44,'5569681373','7224501111',0,'AHORA no puedo hablar','NINGUNA','2026-06-02','60 DIAS','2026-06-03','2026-08-02','TOL/CGT/CMS/880/145321/26/06','BRUNO VALENCIA HERNANDEZ','TIO MATERNO','ESTURA APROX 1.75, COMPLEXION DELGADO, TES MORENO, CABELLO NEGRO, UTILIZA GORRA','EMILIANO ZAPATA','111','IGNACIO ALLENDE Y MIGUEL HIDALGO','FRENTE DE TALLER DE BICICLETAS','BO. GUADALUPE','SAN MATEO ATENCO','ESTADO DE MEXICO','52107','CIUDAD MUJERES','CLAUDIA ARIDIANA VIRIDIANA APREZA VALENZUELA','LESIONES','https://i.pravatar.cc/300?img=47'))
        c.execute("INSERT INTO usuarias (folio,nombres,apellidos,celular,edad,calle,numero,municipio,estado,cp) VALUES ('888028','ARLENY','MONTES DE OCA','7220000001',32,'HIDALGO','45','SAN MATEO ATENCO','ESTADO DE MEXICO','52107')")
        c.execute("INSERT INTO usuarias (folio,nombres,apellidos,celular,edad,calle,numero,municipio,estado,cp) VALUES ('571173','MARIA DE LOURDES','ESCAMILLA RODRIGUEZ','7220000002',51,'JUAREZ','12','SAN MATEO ATENCO','ESTADO DE MEXICO','52107')")
    c.commit(); c.close()
init()

# SIN JINJA - sirve el HTML tal cual, por eso ya no da error de TemplateSyntaxError
@app.route('/')
def celular(): return send_from_directory('templates', 'celular.html')
@app.route('/dashboard')
def dashboard(): return send_from_directory('templates', 'dashboard.html')
@app.route('/registro')
def registro(): return send_from_directory('templates', 'registro.html')
@app.route('/static/<path:p>')
def stat(p): return send_from_directory('static', p)

@app.route('/api/login', methods=['POST'])
def login():
    d = request.json
    c = db()
    u = c.execute("SELECT * FROM usuarias WHERE folio=? OR celular=?", (d.get('folio'), d.get('folio'))).fetchone()
    c.close()
    if u: return jsonify({'ok':True, 'usuaria':dict(u)})
    return jsonify({'ok':False, 'error':'Folio no encontrado'}), 404

@app.route('/api/usuarias')
def usuarias():
    c=db(); rows=c.execute("SELECT * FROM usuarias ORDER BY id DESC").fetchall(); c.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/registro', methods=['POST'])
def crear_usuaria():
    d=request.json
    folio = d.get('folio') or f"{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}"
    c=db()
    try:
        c.execute("INSERT INTO usuarias (folio,folio_cad,nombres,apellidos,mac,edad,celular,otro,hijos,notas,discapacidad,inicio_medida,duracion,fecha_entrega,fecha_fin,num_carpeta,imputado,parentesco,caracteristicas,calle,numero,entre_calles,referencia,localidad,municipio,estado,cp,adscripcion,autoridad,tipo_delito,foto) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (folio, d.get('folio_cad','None'), d.get('nombres'), d.get('apellidos'), d.get('mac'), d.get('edad'), d.get('celular'), d.get('otro'), d.get('hijos'), d.get('notas'), d.get('discapacidad','NINGUNA'), d.get('inicio_medida'), d.get('duracion'), d.get('fecha_entrega'), d.get('fecha_fin'), d.get('num_carpeta'), d.get('imputado'), d.get('parentesco'), d.get('caracteristicas'), d.get('calle'), d.get('numero'), d.get('entre_calles'), d.get('referencia'), d.get('localidad'), d.get('municipio','SAN MATEO ATENCO'), d.get('estado','ESTADO DE MEXICO'), d.get('cp'), d.get('adscripcion'), d.get('autoridad'), d.get('tipo_delito'), d.get('foto','https://i.pravatar.cc/300?img=32')))
        c.commit()
    except Exception as e: return jsonify({'ok':False,'error':str(e)}),400
    c.close(); return jsonify({'ok':True,'folio':folio})

@app.route('/api/alertas')
def alertas():
    c=db()
    rows=c.execute("""SELECT a.*, u.nombres, u.apellidos, u.folio_cad, u.celular, u.mac, u.edad, u.otro, u.hijos, u.notas, u.discapacidad, u.inicio_medida, u.duracion, u.fecha_entrega, u.fecha_fin, u.num_carpeta, u.imputado, u.parentesco, u.caracteristicas, u.calle, u.numero, u.entre_calles, u.referencia, u.localidad, u.municipio, u.estado, u.cp, u.adscripcion, u.autoridad, u.tipo_delito, u.foto, u.status
    FROM alertas a LEFT JOIN usuarias u ON a.folio=u.folio ORDER BY a.id DESC LIMIT 50""").fetchall()
    c.close(); return jsonify([dict(r) for r in rows])

@socketio.on('panico')
def on_panico(data):
    fecha=datetime.datetime.now(ZoneInfo("America/Mexico_City")).strftime("%d-%m-%Y %H:%M:%S")
    c=db(); cur=c.cursor()
    cur.execute("INSERT INTO alertas (folio,lat,lng,precision,fecha,tipo,mensaje) VALUES (?,?,?,?,?,?,?)",(data.get('folio'),data.get('lat'),data.get('lng'),data.get('precision',0),fecha,data.get('tipo','PANICO'),data.get('mensaje','')))
    nid=cur.lastrowid; c.commit()
    row=c.execute("""SELECT a.*, u.* FROM alertas a LEFT JOIN usuarias u ON a.folio=u.folio WHERE a.id=?""",(nid,)).fetchone()
    c.close()
    payload=dict(row) if row else {**data,'fecha':fecha,'id':nid}
    payload['id']=nid; payload['fecha']=fecha
    print(f"PANICO {fecha} Folio {data.get('folio')} {data.get('lat')},{data.get('lng')}")
    emit('nueva_alerta', payload, broadcast=True)

@socketio.on('ubicacion_vivo')
def on_ubi(data): emit('ubicacion_update', data, broadcast=True)

@socketio.on('atender')
def on_atender(data):
    c=db(); c.execute("UPDATE alertas SET estado='ATENDIDA' WHERE id=?",(data.get('id'),)); c.commit(); c.close()
    emit('alerta_atendida', data, broadcast=True)

if __name__=='__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
