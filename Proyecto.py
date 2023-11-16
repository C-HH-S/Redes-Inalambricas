from flask_mysqldb import MySQL
from flask import Flask, session ,jsonify, render_template, request, redirect, url_for, flash
import mysql.connector
from werkzeug.security import check_password_hash

app = Flask(__name__, static_folder='static', template_folder='template')


# Configura la conexión a la base de datos MySQL
app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = ""
app.config['MYSQL_DB'] = "bd_gimnasio1"
mysql = MySQL(app)

# Inicializar sesion
app.secret_key = 'mysecretkey'


# Base de datos ficticia para usuarios
users_db = [{'nombre': 'maria', 'apellido': 'lopez', 'edad': '23', 'correo': 'maria@lopez', 'telefono': '2345678765', 'contraseña': '000'},
            {'nombre': 'jose', 'apellido': 'torres', 'edad': '22',
                'correo': 'jose@torres', 'telefono': '89765756876', 'contraseña': '001'},
            {'nombre': 'ana', 'apellido': 'cruz', 'edad': '45', 'correo': 'ana@cruz', 'telefono': '5678908767', 'contraseña': '002'}]


# Ruta para la página de inicio de sesiónfrom werkzeug.security import check_password_hash

@app.route('/login', methods=['POST'])
def login():
    identificacion = request.form['identificacion']
    contrasena = request.form['contrasena']

    # Consulta para buscar en ambas tablas
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT 'miembro' AS tipo, IDENTIFICACION, INFO_ACCESO, ROL
        FROM login_miembro
        WHERE IDENTIFICACION = %s
        UNION
        SELECT 'empleado' AS tipo, IDENTIFICACION_EMPLEADO, INFO_ACCESO, ROL
        FROM login_empleado
        WHERE IDENTIFICACION_EMPLEADO = %s
    """, (identificacion, identificacion))
    
    # Obtener resultados de la primera consulta
    resultados = cur.fetchall()

    # Verificar si se encontraron resultados
    if resultados:
        # Se encontró el usuario en alguna tabla, ahora obtenemos la contraseña
        tipo_usuario, identificacion, info_acceso, rol = resultados[0]

        # Segunda consulta para obtener la contraseña
        if tipo_usuario == 'miembro':
            cur.execute("SELECT CONTRASENA FROM miembros WHERE IDENTIFICACION = %s", (identificacion,))
        elif tipo_usuario == 'empleado':
            cur.execute("SELECT CONTRASENA FROM empleados WHERE IDENTIFICACION_EMPLEADO = %s", (identificacion,))

        # Obtener la contraseña
        resultado_contraseña = cur.fetchone()

        # Verificar la contraseña
        if resultado_contraseña and resultado_contraseña[0] == contrasena:
            # Contraseña válida, redireccionar según el rol
            if rol == 'administrador':
                return redirect(url_for('vista_administrador'))
            elif rol == 'miembro':
                return redirect(url_for('vista_miembro'))
            elif rol == 'instructor':
                return redirect(url_for('vista_instructor'))
        
    # Si no se cumple ninguna condición anterior, redireccionar a una página de error o mostrar un mensaje
    return redirect(url_for('pagina_de_error'))




# Función para autenticar al usuario
def authenticate_user(nombre, contraseña):
    for user in users_db:
        if user['nombre'] == nombre and user['contraseña'] == contraseña:
            return user
    return None


# Ruta para el panel del administrador (administrador)
@app.route('/administrador')
def administrador():
    for user in users_db:
        print(user)
    return render_template('administrador.html')

@app.route('/gestion_usuarios')
def gestion_usuarios():
     return render_template('gestion_usuarios.html')

@app.route('/gestion_maquinas')
def gestion_maquinas():
     return render_template('gestion_maquinas.html')

@app.route('/gestion_membresias')
def gestion_membresias():
     return render_template('gestion_membresias.html')



# Ruta para el panel del miembro (miembro)
@app.route('/miembro')
def miembro():
    return render_template('miembro.html')

@app.route('/perfil')
def perfil():
    return render_template('perfil.html')

@app.route('/info_personal_user')
def info_personal_user():
    return render_template('info_personal_user.html')

@app.route('/cambio_contrasena_user')
def cambio_contrasena_user():
    return render_template('cambio_contrasena_user.html')

@app.route('/membresia_user')
def membresia_user():
    return render_template('membresia_user.html')

# Ruta para el panel del entrenador (entrenador)
@app.route('/entrenador')
def entrenador():
    return render_template('entrenador.html')

# Ruta para el panel de añadir maquina
@app.route('/agregar_maquina')
def añadir_maquina():
    return render_template('agregar_maquina.html')

# Ruta para el panel de ver historial de maquinaria
@app.route('/vista_historial_maquinaria')
def ver_historial():
    return render_template('vista_historial_maquinaria.html')

# Ruta para el panel de nosotros
@app.route('/NOSOTROS')
def NOSOTROS():
    return render_template('NOSOTROS.html')

@app.route('/CONTACTOS')
def CONTACTOS():
    return render_template('CONTACTOS.html')



#estado membresia administrador
@app.route('/estado_membresia')
def estado_membresia():
        #cur = mysql.connection.cursor()
        #cur.execute("SELECT * FROM clientes")  
        #rows = cur.fetchall()
        #cur.close()
        #return render_template('membresia.html', data=rows)
    return render_template('estado_membresia.html')

#listado membresia administrador
@app.route('/listado_membresia')
def listado_membresia():
        #cur = mysql.connection.cursor()
        #cur.execute("SELECT * FROM clientes")  
        #rows = cur.fetchall()
        #cur.close()
        #return render_template('membresia.html', data=rows)
    return render_template('listado_membresia.html')

#editar membresia administrador
@app.route('/editar_membresia')
def editar_membresia():
        #cur = mysql.connection.cursor()
        #cur.execute("SELECT * FROM clientes")  
        #rows = cur.fetchall()
        #cur.close()
        #return render_template('membresia.html', data=rows)
    return render_template('editar_membresia.html')

#vista editar membresia
@app.route('/vista_editar_membresia')
def vista_editar_membresia():
        #cur = mysql.connection.cursor()
        #cur.execute("SELECT * FROM clientes")  
        #rows = cur.fetchall()
        #cur.close()
        #return render_template('membresia.html', data=rows)
    return render_template('vista_editar_membresia.html')

#vista principal de asignar membresia
@app.route('/asignar_membresia')
def asignar_membresia():
        #cur = mysql.connection.cursor()
        #cur.execute("SELECT * FROM clientes")  
        #rows = cur.fetchall()
        #cur.close()
        #return render_template('membresia.html', data=rows)
    return render_template('asignar_membresia.html')

#vista secundaria de asignar membresia
@app.route('/vista_asignar_membresia')
def vista_asignar_membresia():
        #cur = mysql.connection.cursor()
        #cur.execute("SELECT * FROM clientes")  
        #rows = cur.fetchall()
        #cur.close()
        #return render_template('membresia.html', data=rows)
    return render_template('vista_asignar_membresia.html')

#vista estdo de membresia desde miembro
@app.route('/miembro_estado_membresia')
def miembro_estado_membresia():
        #cur = mysql.connection.cursor()
        #cur.execute("SELECT * FROM clientes")  
        #rows = cur.fetchall()
        #cur.close()
        #return render_template('membresia.html', data=rows)
    return render_template('miembro_estado_membresia.html')

#vista de reservas desde miembro
@app.route('/reservas_miembro')
def reservas_miembro():
        #cur = mysql.connection.cursor()
        #cur.execute("SELECT * FROM clientes")  
        #rows = cur.fetchall()
        #cur.close()
        #return render_template('membresia.html', data=rows)
    return render_template('reservas_miembro.html')

#reservar clase desde miembro
@app.route('/reservar_clase')
def reservar_clase():
        #cur = mysql.connection.cursor()
        #cur.execute("SELECT * FROM clientes")  
        #rows = cur.fetchall()
        #cur.close()
        #return render_template('membresia.html', data=rows)
    return render_template('reservar_clase.html')

#reservar maquina desde miembro
@app.route('/reservar_maquina')
def reservar_maquina():
        #cur = mysql.connection.cursor()
        #cur.execute("SELECT * FROM clientes")  
        #rows = cur.fetchall()
        #cur.close()
        #return render_template('membresia.html', data=rows)
    return render_template('reservar_maquina.html')

#plan de trabado de miembro
@app.route('/plan_de_trabajo_miembro')
def plan_de_trabajo_miembro():
        #cur = mysql.connection.cursor()
        #cur.execute("SELECT * FROM clientes")  
        #rows = cur.fetchall()
        #cur.close()
        #return render_template('membresia.html', data=rows)
    return render_template('plan_de_trabajo_miembro.html')
       
# Vista para eliminar usuario
@app.route('/listado_usuarios', methods=['GET', 'POST'])
def listado_usuarios():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM miembros')
    data = cur.fetchall()
    mysql.connection.commit()
    return render_template('listado_usuarios.html', miembros=data)

# Vista para cambiar el estado de un usuario
@app.route('/estado_usuario', methods=['GET', 'POST'])
def estado_usuario():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM miembros')
    data = cur.fetchall()
    mysql.connection.commit()
    return render_template('estado_usuario.html', miembros=data)


#accion de cambiar el estado de un miembro
@app.route('/cambiar_estado_miembro', methods=['POST'])
def cambiar_estado_miembro():
    if request.method == 'POST':
        miembro_id=None
        estado_actual=None
        miembro_id = request.form.get('miembro_id')
        # Realiza una consulta para obtener el estado actual del miembro
        cur = mysql.connection.cursor()
        cur.execute("SELECT estado FROM miembros WHERE id = %s", (miembro_id,))
        estado_actual = cur.fetchone()
        print(estado_actual)
        # Cambia el estado (por ejemplo, de True a False o viceversa)
        nuevo_estado = not estado_actual[0]
        # Realiza la actualización en la base de datos
        cur.execute("UPDATE miembros SET estado = %s WHERE id = %s", (nuevo_estado, miembro_id))
        mysql.connection.commit()
        cur.close()
        flash('Estado actualizado correctamente')
    return redirect(url_for('estado_usuario') ) # Renderiza la plantilla con los datos actualizados


# Vista para editar usuario
@app.route('/editar_miembro', methods=['GET', 'POST'])
def editar_miembro():
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM miembros')
    data = cur.fetchall()
    mysql.connection.commit()

    return render_template('editar_miembro.html', miembros=data)

# accion de buscar usuario
@app.route("/edit/<string:id>")
def buscarid(id):
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM miembros WHERE IDENTIFICACION = %s', (id,))
    data = cur.fetchall()
   # mysql.connection.commit()
   # flash ('miembro editado correctamente')
    return render_template('vista_editar.html', miembro=data[0])


# accion de editar usuario
@app.route("/update/<id>", methods=['POST'])
def getid(id):
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        edad = request.form['edad']
        correo = request.form['correo']
        telefono = request.form['telefono']
        contraseña = request.form['contraseña']

    cur = mysql.connection.cursor()
    cur.execute('UPDATE miembros SET NOMBRE = %s, APELLIDO = %s, EDAD = %s, CORREO = %s, TELEFONO = %s, CONTRASENA = %s WHERE IDENTIFICACION = %s',
                (nombre, apellido, edad, correo, telefono, contraseña, id))
    mysql.connection.commit()
    flash('miembro editado correctamente')
    return redirect(url_for('editar_miembro'))


# Vista para agregar usuario
@app.route('/admin/agregar_usuario', methods=['GET', 'POST'])
def agregar_usuario():
    if request.method == 'POST':
        # Obtener los datos del formulario
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        edad = request.form['edad']
        correo = request.form['correo']
        telefono = request.form['telefono']
        contraseña = request.form['contraseña']
        estado = request.form['estado']
        identificacion = request.form['identificacion']
       
        # Agregar el usuario a la base de datos
        cur = mysql.connection.cursor()

        cur.execute('SET foreign_key_checks = 0;')

        cur.execute('INSERT INTO miembros (IDENTIFICACION, NOMBRE, APELLIDO, EDAD, CORREO, TELEFONO, CONTRASENA, ESTADO) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)',
            (identificacion, nombre, apellido, edad, correo, telefono, contraseña, estado))

        
        
        mysql.connection.commit()
        flash('Usuario agregado correctamente')

        # Redirigir a la página de administración o mostrar un mensaje de éxito
        # return redirect(url_for('administrador'))

    return render_template('agregar_usuario.html')


# Vista buscar miembro
@app.route('/buscar_miembro', methods=['GET', 'POST'])
def buscar_miembro():
    data = None
    if request.method == 'POST':
        # Obtén el término de búsqueda del formulario
        identificacion = request.form.get('identificacion')
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM miembros WHERE IDENTIFICACION = %s", (identificacion,))
        data = cur.fetchall()
        cur.close()
        if data:
            flash('Miembro encontrado.')
            return render_template('buscar_miembro.html', resultados=data)
        else:
            flash('No se encontraron miembros con ese nombre.')
    return render_template('buscar_miembro.html')


# Vista para agregar máquina
@app.route('/agregar_maquina', methods=['GET', 'POST'])
def agregar_maquina():
    if request.method == 'POST':
        # Obtener los datos del formulario
        #registro = request.form['registro']
        nombre = request.form['nombre']
        estado = request.form['estado']
        proveedor = request.form['proveedor']
        precio = request.form['precio']
        fechaCompra = request.form['fechaCompra']
        disponibilidad = request.form['disponibilidad']

# Agregar el usuario a la base de datos
    cur = mysql.connection.cursor()
    cur.execute('SET foreign_key_checks = 0;')
    cur.execute('INSERT INTO maquina (NOMBRE, ID_ESTADO_MAQUINA, ID_DISPONIBILIDAD_MAQUINARIA) VALUES (%s, %s, %s)',
                (nombre, estado, disponibilidad))
    cur.execute('SELECT LAST_INSERT_ID()')
    id_maquina = cur.fetchone()[0]

    cur.execute('INSERT INTO proveedor_maquinaria (NOMBRE) VALUES (%s)',
                (proveedor,))
    cur.execute('SELECT LAST_INSERT_ID()')
    id_proveedor = cur.fetchone()[0]

    cur.execute('INSERT INTO historial_maquinaria (FECHA_COMPRA, PRECIO, ID_PROVEEDOR, ID_MAQUINA) VALUES (%s, %s, %s, %s)',
                (fechaCompra, precio, id_proveedor, id_maquina))


    mysql.connection.commit()
    flash('Máquina agregada correctamente')
    return render_template('agregar_maquina.html')


# Vista mirar el listado de maquinas
@app.route('/lista_maquinas', methods=['GET', 'POST'])
def lista_maquinas():
    data = None
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM maquina')
    data = cur.fetchall()
    mysql.connection.commit()
    return render_template('lista_maquinas.html', miembros=data)

# Vista del estado de máquinas
@app.route('/estado_maquinas', methods=['GET', 'POST'])
def estado_maquinas():
    data = None
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM maquinas')
    data = cur.fetchall()
    mysql.connection.commit()
    return render_template('estado_maquinas.html', maquinas=data)

# accion de editar estado de máquina
@app.route('/cambiar_estado_maquina', methods=['POST'])
def cambiar_estado():
    if request.method == 'POST':
        maquina_id = None
        maquina_id = request.form.get('maquina_id')
        print("maquina_id:", maquina_id)
        # Realiza una consulta para obtener el estado actual del atributo booleano
        cur = mysql.connection.cursor()
        cur.execute("SELECT estado FROM maquinas WHERE IdMaquina = %s", (maquina_id,))
        estado_actual = cur.fetchone()
        print(estado_actual)
        # Cambia el estado (por ejemplo, de True a False o viceversa)
        nuevo_estado = not estado_actual[0]

        # Realiza la actualización en la base de datos
        cur.execute("UPDATE maquinas SET estado = %s, disponibilidad = %s WHERE IdMaquina = %s", (nuevo_estado, nuevo_estado, maquina_id))
        mysql.connection.commit()

        cur.close()
        flash('Estado actualizado correctamente')
        return redirect(url_for('estado_maquinas'))  # Renderiza la plantilla con los datos actualizados

# Traer el historial de la máquina
@app.route("/historial/<id>")
def gethistorial(id):
        cur = mysql.connection.cursor()
        cur.execute("""
        SELECT historial_maquinaria.*, proveedor_maquinaria.NOMBRE AS NombreProveedor
        FROM historial_maquinaria
        LEFT JOIN proveedor_maquinaria ON historial_maquinaria.ID_PROVEEDOR = proveedor_maquinaria.ID_PROVEEDOR
        WHERE historial_maquinaria.ID_MAQUINA = %s
        """, (id,))
        data = cur.fetchall()
        cur.close()
        flash('Historial de máquina encontrado correctamente')
        return render_template('vista_historial_maquina.html', resultados=data) # Renderiza la plantilla con los datos actualizados


#vista de buscar maquina
@app.route('/buscar_maquina', methods=['GET', 'POST'])
def buscar_maquina():
    data = None
    if request.method == 'POST':
        # Obtén el término de búsqueda del formulario
        nombre = request.form.get('nombre')
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM maquina WHERE LOWER(nombre) = %s", (nombre,))
        data = cur.fetchall()
        cur.close()
        if data:
            flash('Máquina encontrado.')
            return render_template('buscar_maquina.html', resultados=data)
        else:
            flash('No se encontraron máquinas con ese nombre.')
    return render_template('buscar_maquina.html')


# Vista mantenimiento de maquinas
@app.route('/mantenimiento_maquinas', methods=['GET', 'POST'])
def mantenimiento_maquinas():
    data = None
    cur = mysql.connection.cursor()
    cur.execute('SELECT * FROM maquinas WHERE estado = 0')
    data = cur.fetchall()
    mysql.connection.commit()
    return render_template('mantenimiento_maquinas.html', miembros=data)

# Traer el historial de la máquina
@app.route("/mantenimiento/<maquina_id>")
def getmantenimiento(maquina_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM maquinas WHERE IdMaquina = %s", (maquina_id,))
    maquina = cur.fetchone()
    cur.close()

    if request.method == 'POST':
        # Aquí puedes capturar los datos de fecha y hora seleccionados por el usuario
        fecha = request.form.get('fecha')
        hora = request.form.get('hora')
        # Luego, puedes guardar esta información en tu base de datos o realizar otras acciones necesarias.

        flash(f'Cita agendada para {fecha} a las {hora}')
    return render_template('vista_mantenimiento.html', maquina=maquina) # Renderiza la plantilla con los datos actualizados



if __name__ == '__main__':
    app.run(debug=True)
