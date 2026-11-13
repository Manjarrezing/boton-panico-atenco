from zoneinfo import ZoneInfo
from flask import Flask, jsonify, request, send_from_directory, render_template, session, redirect
from flask_socketio import SocketIO, emit
import datetime, uuid, os
import psycopg2
import psycopg2.extras
import io, base64 os
from flask import send_file
from openpyxl import Workbook
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter

app = Flask(__name__)
app.config['SECRET_KEY'] = 'atenco-2026'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")
USUARIOS = {
    'Ing.Manjarrez': 'Atenco2026',
    'Usuario': 'Atenco2026',
    'Monitorista1': 'Atenco2026',
    'Monitorista2': 'Atenco2026'
}

DATABASE_URL = os.environ.get("DATABASE_URL")

def db():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

def cur(conn):
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

def init():
    conn = db(); c = cur(conn)
    c.execute("""CREATE TABLE IF NOT EXISTS usuarias (
        id SERIAL PRIMARY KEY, folio TEXT UNIQUE, folio_cad TEXT,
        nombres TEXT, apellidos TEXT, mac TEXT, edad INTEGER, celular TEXT, otro TEXT,
        hijos INTEGER, notas TEXT, discapacidad TEXT, foto TEXT,
        inicio_medida TEXT, duracion TEXT, fecha_entrega TEXT, fecha_fin TEXT,
        num_carpeta TEXT, imputado TEXT, parentesco TEXT, caracteristicas TEXT,
        calle TEXT, numero TEXT, entre_calles TEXT, referencia TEXT,
        localidad TEXT, municipio TEXT, estado TEXT, cp TEXT,
        adscripcion TEXT, autoridad TEXT, tipo_delito TEXT, status TEXT DEFAULT 'Activo'
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS alertas (
        id SERIAL PRIMARY KEY, folio TEXT, lat REAL, lng REAL,
        precision REAL, fecha TEXT, tipo TEXT, mensaje TEXT, estado TEXT DEFAULT 'ACTIVA'
    )""")
    conn.commit()
    c.execute("SELECT count(*) as total FROM usuarias")
    total = c.fetchone()['total']
    if total == 0:
        c.execute("INSERT INTO usuarias (folio,folio_cad,nombres,apellidos,mac,edad,celular,otro,hijos,notas,discapacidad,inicio_medida,duracion,fecha_entrega,fecha_fin) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", ('582-1877','None','ARACELY','JIMENEZ VALENCIA','C30000400DES',44,'5563681373','7224501111',0,'AHORA no puedo hablar','NINGUNA','2026-06-02','60 DIAS','2026-06-03','2026-08-02'))
        c.execute("INSERT INTO usuarias (folio,nombres,apellidos,celular,edad,calle,numero,municipio,estado,cp) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", ('888028','ARLENY','MONTES DE OCA','7220000001',32,'','','','',''))
        c.execute("INSERT INTO usuarias (folio,nombres,apellidos,celular,edad,calle,numero,municipio,estado,cp) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", ('571173','MARIA DE LOURDES','ESCAMILLA RODRIGUEZ','7220000002',0,'','','','',''))
        conn.commit()
    conn.close()

init()

@app.route('/')
def celular(): return send_from_directory('templates', 'celular.html')
@app.route('/login', methods=['GET','POST'])
def login_admin():
    if request.method == 'POST':
        u = request.form.get('usuario','')
        p = request.form.get('password','')
        if u in USUARIOS and USUARIOS[u] == p:
            session['admin'] = u
            return redirect('/dashboard')
        return '<h2 style="text-align:center;margin-top:50px;font-family:sans-serif">❌ Usuario o contraseña incorrecta<br><br><a href="/login">Intentar otra vez</a></h2>'
    return '''<div style="max-width:350px;margin:80px auto;font-family:sans-serif;text-align:center;border:1px solid #ddd;padding:25px;border-radius:12px">
    <h2>🚨 CENTRAL PANICO 🚨<br>XONACATLAN</h2><p>Inicia sesion para entrar</p>
    <form method="POST"><input name="usuario" placeholder="Usuario" style="width:100%;padding:12px;margin:5px 0;border-radius:8px;border:1px solid #ccc"><br>
    <input name="password" type="password" placeholder="Contraseña" style="width:100%;padding:12px;margin:5px 0;border-radius:8px;border:1px solid #ccc"><br>
    <button style="width:100%;padding:12px;background:#cc0000;color:white;border:0;border-radius:8px;font-weight:bold;font-size:16px;margin-top:10px">ENTRAR</button></form></div>'''

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')
@app.route('/api/quien_soy')
def quien_soy():
    return jsonify({'usuario': session.get('admin', '')})
@app.route('/buscar')
def buscar():
    return send_from_directory('templates', 'buscar.html')
@app.route('/api/buscar')
def api_buscar():
    folio = request.args.get('folio','').strip()
    if not folio:
        return jsonify({'ok': False, 'error': 'Escribe un folio'})
    conn=db(); c=cur(conn)
    c.execute("SELECT * FROM usuarias WHERE UPPER(folio)=UPPER(%s) OR celular=%s", (folio, folio))
    u = c.fetchone()
    conn.close()
    if u:
        return jsonify({'ok': True, 'usuaria': dict(u)})
    return jsonify({'ok': False, 'error': 'Folio no encontrado'}), 404

@app.route('/dashboard')
def dashboard():
    if 'admin' not in session:
        return redirect('/login')
    return send_from_directory('templates', 'dashboard.html')
@app.route('/registro')
def registro(): return send_from_directory('templates', 'registro.html')
@app.route('/static/<path:p>')
def stat(p): return send_from_directory('static', p)

@app.route('/api/login', methods=['POST'])
def login():
    d = request.json
    conn=db(); c=cur(conn)
    c.execute("SELECT * FROM usuarias WHERE folio=%s OR celular=%s", (d.get('folio'), d.get('folio')))
    u = c.fetchone()
    conn.close()
    if u: return jsonify({'ok':True, 'usuaria':dict(u)})
    return jsonify({'ok':False, 'error':'Folio no encontrado'}), 404

@app.route('/api/usuarias')
def usuarias():
    conn=db(); c=cur(conn)
    c.execute("SELECT * FROM usuarias ORDER BY id DESC")
    rows=c.fetchall(); conn.close()
    return jsonify([dict(r) for r in rows])

@app.route('/api/registro', methods=['POST'])
def crear_usuaria():
    d=request.json
    folio = d.get('folio') or f"{uuid.uuid4().hex[:4].upper()}-{uuid.uuid4().hex[:4].upper()}"
    conn=db(); c=cur(conn)
    try:
        c.execute("INSERT INTO usuarias (folio,folio_cad,nombres,apellidos,mac,edad,celular,otro,hijos,notas,discapacidad,inicio_medida,duracion,fecha_entrega,fecha_fin,num_carpeta,imputado,parentesco,caracteristicas,calle,numero,entre_calles,referencia,localidad,municipio,estado,cp,adscripcion,autoridad,tipo_delito,foto) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
        (folio, d.get('folio_cad','None'), d.get('nombres'), d.get('apellidos'), d.get('mac'), d.get('edad'), d.get('celular'), d.get('otro'), d.get('hijos'), d.get('notas'), d.get('discapacidad'), d.get('inicio_medida'), d.get('duracion'), d.get('fecha_entrega'), d.get('fecha_fin'), d.get('num_carpeta'), d.get('imputado'), d.get('parentesco'), d.get('caracteristicas'), d.get('calle'), d.get('numero'), d.get('entre_calles'), d.get('referencia'), d.get('localidad'), d.get('municipio'), d.get('estado'), d.get('cp'), d.get('adscripcion'), d.get('autoridad'), d.get('tipo_delito'), d.get('foto') or d.get('foto_base64') or d.get('foto_url')))
        conn.commit()
    except Exception as e: conn.close(); return jsonify({'ok':False,'error':str(e)}),400
    conn.close(); return jsonify({'ok':True,'folio':folio})

@app.route('/api/alertas')
def alertas():
    conn=db(); c=cur(conn)
    c.execute("""SELECT a.*, u.nombres, u.apellidos, u.folio_cad, u.celular, u.mac, u.edad, u.otro, u.hijos, u.notas, u.discapacidad, u.inicio_medida, u.duracion, u.fecha_entrega, u.fecha_fin, u.num_carpeta, u.imputado, u.parentesco, u.caracteristicas, u.calle, u.numero, u.entre_calles, u.referencia, u.localidad, u.municipio, u.estado, u.cp, u.adscripcion, u.autoridad, u.tipo_delito
    FROM alertas a LEFT JOIN usuarias u ON a.folio=u.folio ORDER BY a.id DESC LIMIT 50""")
    rows=c.fetchall(); conn.close()
    return jsonify([dict(r) for r in rows])

@socketio.on('panico')
def on_panico(data):
    fecha=datetime.datetime.now(ZoneInfo("America/Mexico_City")).strftime("%Y-%m-%d %H:%M:%S")
    conn=db(); c=cur(conn)
    c.execute("INSERT INTO alertas (folio,lat,lng,precision,fecha,tipo,mensaje) VALUES (%s,%s,%s,%s,%s,%s,%s) RETURNING id", (data.get('folio'),data.get('lat'),data.get('lng'),data.get('precision'),fecha,data.get('tipo'),data.get('mensaje')))
    nid=c.fetchone()['id']; conn.commit()
    c.execute("SELECT a.*, u.* FROM alertas a LEFT JOIN usuarias u ON a.folio=u.folio WHERE a.id=%s", (nid,))
    row=c.fetchone()
    conn.close()
    payload=dict(row) if row else {**data,'fecha':fecha,'id':nid}
    payload['id']=nid; payload['fecha']=fecha
    print(f"PANICO {fecha} Folio {data.get('folio')} {data.get('lat')},{data.get('lng')}")
    emit('nueva_alerta', payload, broadcast=True)

@socketio.on('ubicacion_vivo')
def on_ubi(data): emit('ubicacion_update', data, broadcast=True)

@socketio.on('atender')
def on_atender(data):
    conn=db(); c=cur(conn)
    c.execute("UPDATE alertas SET estado='ATENDIDA' WHERE id=%s", (data.get('id'),))
    conn.commit(); conn.close()
    emit('alerta_atendida', data, broadcast=True)
@app.route('/api/actualizar', methods=['POST'])
def api_actualizar():
    try:
        d = request.get_json()
        # Si edad o hijos vienen vacios, mandarlos como None y no como ""
        for k in ['edad','hijos']:
            if d.get(k) == '' or d.get(k) is None:
                d[k] = None
            else:
                try:
                    d[k] = int(float(str(d[k]).strip()))
                except:
                    d[k] = None
        conn = db(); c = cur(conn)
        # Crear columnas si no existen
        cols = ['nombres','apellidos','mac','edad','nac','celular','otro','hijos','calle','numero','entrecalles','referencia','localidad','cp','carpeta','imputado','adscripcion','autoridad','tipo_delito','parentesco','permanencia','caracteristicas','discapacidad','inicio_medida','duracion','fecha_entrega','fecha_fin','notas','foto']
        for col in cols:
            try:
                c.execute(f"ALTER TABLE usuarias ADD COLUMN IF NOT EXISTS {col} TEXT")
            except Exception:
                conn.rollback()
        conn.commit()
        if d.get('foto'):
            c.execute("""UPDATE usuarias SET nombres=%s, apellidos=%s, mac=%s, edad=%s, nac=%s, celular=%s, otro=%s, hijos=%s, calle=%s, numero=%s, entrecalles=%s, referencia=%s, localidad=%s, cp=%s, carpeta=%s, imputado=%s, adscripcion=%s, autoridad=%s, tipo_delito=%s, parentesco=%s, permanencia=%s, caracteristicas=%s, discapacidad=%s, inicio_medida=%s, duracion=%s, fecha_entrega=%s, fecha_fin=%s, notas=%s, foto=%s WHERE folio=%s""",
            (d.get('nombres'), d.get('apellidos'), d.get('mac'), d.get('edad'), d.get('nac'), d.get('celular'), d.get('otro'), d.get('hijos'), d.get('calle'), d.get('numero'), d.get('entrecalles'), d.get('referencia'), d.get('localidad'), d.get('cp'), d.get('carpeta'), d.get('imputado'), d.get('adscripcion'), d.get('autoridad'), d.get('tipo_delito'), d.get('parentesco'), d.get('permanencia'), d.get('caracteristicas'), d.get('discapacidad'), d.get('inicio'), d.get('duracion'), d.get('fecha_entrega'), d.get('fecha_fin'), d.get('notas'), d.get('foto'), d.get('folio')))
        else:
            c.execute("""UPDATE usuarias SET nombres=%s, apellidos=%s, mac=%s, edad=%s, nac=%s, celular=%s, otro=%s, hijos=%s, calle=%s, numero=%s, entrecalles=%s, referencia=%s, localidad=%s, cp=%s, carpeta=%s, imputado=%s, adscripcion=%s, autoridad=%s, tipo_delito=%s, parentesco=%s, permanencia=%s, caracteristicas=%s, discapacidad=%s, inicio_medida=%s, duracion=%s, fecha_entrega=%s, fecha_fin=%s, notas=%s WHERE folio=%s""",
            (d.get('nombres'), d.get('apellidos'), d.get('mac'), d.get('edad'), d.get('nac'), d.get('celular'), d.get('otro'), d.get('hijos'), d.get('calle'), d.get('numero'), d.get('entrecalles'), d.get('referencia'), d.get('localidad'), d.get('cp'), d.get('carpeta'), d.get('imputado'), d.get('adscripcion'), d.get('autoridad'), d.get('tipo_delito'), d.get('parentesco'), d.get('permanencia'), d.get('caracteristicas'), d.get('discapacidad'), d.get('inicio'), d.get('duracion'), d.get('fecha_entrega'), d.get('fecha_fin'), d.get('notas'), d.get('folio')))
        conn.commit(); conn.close()
        return jsonify({"ok": True, "mensaje": "Actualizado"})
    except Exception as e:
        return jsonify({"ok": False, "mensaje": "Error: " + str(e)}), 500
@app.route('/export_excel')
def export_excel():
    if not session:
        return redirect('/login')
    conn = db(); c = cur(conn)
    c.execute("SELECT * FROM usuarias ORDER BY id DESC")
    rows = c.fetchall()
    # Si tu cur no regresa dict, convertir a dict
    cols = [d[0] for d in c.description] if c.description else []
    data = []
    for r in rows:
        if isinstance(r, dict):
            data.append(r)
        else:
            data.append(dict(zip(cols, r)))
    c.close(); conn.close()

    wb = Workbook()
    ws = wb.active
    ws.title = "Encuestas"
    if not data:
        ws['A1'] = "Sin registros"
        output = io.BytesIO(); wb.save(output); output.seek(0)
        return send_file(output, as_attachment=True, download_name="encuestas.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    headers = list(data[0].keys())
    foto_col = None
    for cc in ['foto','imagen','photo','foto_base64']:
        if cc in headers:
            foto_col = cc; headers.remove(cc); break
    headers.append('Foto')
    ws.append(headers)
    for i, h in enumerate(headers, 1):
        ws.column_dimensions[get_column_letter(i)].width = 22
    ws.column_dimensions[get_column_letter(len(headers))].width = 25

    for r_idx, row in enumerate(data, start=2):
        ws.row_dimensions[r_idx].height = 110
        for c_idx, h in enumerate(headers, 1):
            if h == 'Foto':
                continue
            val = row.get(h, '')
            if isinstance(val, (datetime.datetime, datetime.date)):
                val = val.strftime('%d/%m/%Y %H:%M')
            ws.cell(row=r_idx, column=c_idx, value=str(val) if val is not None else '')
               if foto_col:
            foto_data = row.get(foto_col, '')
            img_bytes = None
            try:
                # Caso 1: ya viene en bytes
                if isinstance(foto_data, (bytes, bytearray)):
                    img_bytes = bytes(foto_data)
                # Caso 2: es un link http
                elif isinstance(foto_data, str) and foto_data.startswith('http'):
                    import urllib.request
                    with urllib.request.urlopen(foto_data, timeout=10) as r:
                        img_bytes = r.read()
                # Caso 3: es un archivo /uploads/... o una ruta
                elif isinstance(foto_data, str) and ('/' in foto_data or '\\' in foto_data) and len(foto_data) < 500 and 'data:image' not in foto_data:
                    ruta = foto_data.lstrip('/').replace('uploads/', 'uploads/')
                    if os.path.exists(ruta):
                        with open(ruta, 'rb') as f:
                            img_bytes = f.read()
                    elif os.path.exists(os.path.join('static', ruta)):
                        with open(os.path.join('static', ruta), 'rb') as f:
                            img_bytes = f.read()
                # Caso 4: es base64
                elif isinstance(foto_data, str) and len(foto_data) > 100:
                    if ',' in foto_data:
                        foto_data = foto_data.split(',', 1)[1]
                    img_bytes = base64.b64decode(foto_data)

                if img_bytes:
                    img = XLImage(io.BytesIO(img_bytes))
                    img.width = 140; img.height = 105
                    ws.add_image(img, f"{get_column_letter(len(headers))}{r_idx}")
            except Exception as e:
                print("Error foto fila", r_idx, e)
                pass
    output = io.BytesIO(); wb.save(output); output.seek(0)
    return send_file(output, as_attachment=True, download_name="encuestas_atenco.xlsx", mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000)
