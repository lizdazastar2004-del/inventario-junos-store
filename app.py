from flask import Flask, render_template, request, jsonify, send_file
import json
import os
import csv
import io
import shutil
from datetime import datetime

app = Flask(__name__)

DATA_FILE = os.path.join(os.path.dirname(__file__), "inventario.json")
BACKUP_DIR = os.path.join(os.path.dirname(__file__), "backups")

os.makedirs(BACKUP_DIR, exist_ok=True)

def cargar_inventario():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def guardar_inventario(datos):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/productos", methods=["GET"])
def obtener_productos():
    return jsonify(cargar_inventario())

@app.route("/api/productos", methods=["POST"])
def agregar_producto():
    datos = request.json
    inventario = cargar_inventario()
    nuevo_id = max([p["id"] for p in inventario], default=0) + 1
    producto = {
        "id": nuevo_id,
        "nombre": datos["nombre"],
        "categoria": datos["categoria"],
        "cantidad": int(datos["cantidad"]),
        "precio": float(datos["precio"]),
        "descripcion": datos.get("descripcion", ""),
        "fecha": datetime.now().strftime("%Y-%m-%d")
    }
    inventario.append(producto)
    guardar_inventario(inventario)
    return jsonify(producto), 201

@app.route("/api/productos/<int:pid>", methods=["PUT"])
def actualizar_producto(pid):
    datos = request.json
    inventario = cargar_inventario()
    for p in inventario:
        if p["id"] == pid:
            p["nombre"] = datos["nombre"]
            p["categoria"] = datos["categoria"]
            p["cantidad"] = int(datos["cantidad"])
            p["precio"] = float(datos["precio"])
            p["descripcion"] = datos.get("descripcion", "")
            guardar_inventario(inventario)
            return jsonify(p)
    return jsonify({"error": "No encontrado"}), 404

@app.route("/api/productos/<int:pid>", methods=["DELETE"])
def eliminar_producto(pid):
    inventario = cargar_inventario()
    inventario = [p for p in inventario if p["id"] != pid]
    guardar_inventario(inventario)
    return jsonify({"ok": True})

@app.route("/api/stats")
def stats():
    inventario = cargar_inventario()
    total_productos = len(inventario)
    total_items = sum(p["cantidad"] for p in inventario)
    valor_total = sum(p["cantidad"] * p["precio"] for p in inventario)
    bajo_stock = len([p for p in inventario if p["cantidad"] < 5])
    return jsonify({
        "total_productos": total_productos,
        "total_items": total_items,
        "valor_total": round(valor_total, 2),
        "bajo_stock": bajo_stock
    })

@app.route("/api/exportar/csv")
def exportar_csv():
    inventario = cargar_inventario()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID","Nombre","Categoría","Cantidad","Precio","Valor Total","Descripción","Fecha"])
    for p in inventario:
        writer.writerow([p["id"],p["nombre"],p["categoria"],p["cantidad"],p["precio"],round(p["cantidad"]*p["precio"],2),p["descripcion"],p["fecha"]])
    output.seek(0)
    fecha = datetime.now().strftime("%Y-%m-%d")
    return send_file(io.BytesIO(output.getvalue().encode("utf-8-sig")),mimetype="text/csv",as_attachment=True,download_name=f"inventario_junos_store_{fecha}.csv")

@app.route("/api/exportar/json")
def exportar_json():
    inventario = cargar_inventario()
    fecha = datetime.now().strftime("%Y-%m-%d")
    contenido = json.dumps(inventario, ensure_ascii=False, indent=2).encode("utf-8")
    return send_file(io.BytesIO(contenido),mimetype="application/json",as_attachment=True,download_name=f"inventario_junos_store_{fecha}.json")

@app.route("/api/backup/local", methods=["POST"])
def backup_local():
    if not os.path.exists(DATA_FILE):
        return jsonify({"error": "No hay inventario"}), 400
    fecha = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nombre = f"backup_{fecha}.json"
    shutil.copy2(DATA_FILE, os.path.join(BACKUP_DIR, nombre))
    backups = sorted(os.listdir(BACKUP_DIR))
    while len(backups) > 10:
        os.remove(os.path.join(BACKUP_DIR, backups.pop(0)))
    return jsonify({"ok": True, "archivo": nombre})

@app.route("/api/backup/lista")
def lista_backups():
    if not os.path.exists(BACKUP_DIR):
        return jsonify([])
    archivos = sorted(os.listdir(BACKUP_DIR), reverse=True)
    return jsonify([{"nombre":a,"fecha":datetime.fromtimestamp(os.path.getmtime(os.path.join(BACKUP_DIR,a))).strftime("%d/%m/%Y %H:%M")} for a in archivos])

@app.route("/api/backup/descargar/<nombre>")
def descargar_backup(nombre):
    ruta = os.path.join(BACKUP_DIR, nombre)
    if not os.path.exists(ruta):
        return jsonify({"error": "No encontrado"}), 404
    return send_file(ruta, as_attachment=True, download_name=nombre)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
