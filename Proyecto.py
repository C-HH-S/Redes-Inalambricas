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


# Ruta para la página de inicio de sesiónfrom werkzeug.security import check_password_hash
@app.route('/', methods=['GET', 'POST'])
def login():
    identificacion = None
    contrasena = None
    if request.method == 'POST':
        identificacion = request.form['identificacion']
        contrasena = request.form['contrasena']

        # Consulta para buscar en la tabla miembro
        cur = mysql.connection.cursor()
        cur.execute("SELECT IDENTIFICACION, CONTRASENA FROM miembros WHERE IDENTIFICACION = %s", (identificacion,))
        miembro = cur.fetchone()
        cur.close()

        # Consulta para buscar en la tabla empleado
        cur = mysql.connection.cursor()
        cur.execute("SELECT IDENTIFICACION_EMPLEADO, CONTRASENA, ID_SALARIO_EMPLE FROM empleado WHERE IDENTIFICACION_EMPLEADO = %s", (identificacion,))
        empleado = cur.fetchone()
        cur.close()

        if miembro and contrasena == miembro[1]:
            # Iniciar sesión como miembro
            session['identificacion'] = miembro[0]
            session['rol'] = 'miembro'
            # Almacena información del miembro en la sesión
            session['info_usuario'] = obtener_info_miembro(miembro[0])
            return redirect(url_for('miembro'))

        elif empleado and contrasena == empleado[1]:
            # Obtener el rol del empleado
            cur = mysql.connection.cursor()
            cur.execute("SELECT CARGO FROM salario_empleado WHERE ID_SALARIO_EMPLE = %s", (empleado[2],))
            cargo = cur.fetchone()
            cur.close()

            if cargo:
                # Iniciar sesión como administrador o instructor según el cargo
                session['identificacion'] = empleado[0]
                session['rol'] = 'administrador' if cargo[0] == 'administrador' else 'instructor'
                # Almacena información del empleado en la sesión
                session['info_usuario'] = obtener_info_empleado(empleado[0])
                # Redirige a la vista correspondiente
                if cargo[0] == 'Administrador':
                    return redirect(url_for('administrador'))
                elif cargo[0] == 'Instructor':
                    return redirect(url_for('entrenador'))

        flash('Credenciales incorrectas. Intenta de nuevo.')

    return render_template('login.html')

def obtener_info_miembro(identificacion):
    cur = mysql.connection.cursor()
    cur.execute("SELECT IDENTIFICACION, NOMBRE, APELLIDO, EDAD, CORREO, TELEFONO, CONTRASENA, ESTADO FROM miembros WHERE IDENTIFICACION = %s", (identificacion,))
    info_miembro = cur.fetchone()
    cur.close()
    return info_miembro

def obtener_info_empleado(identificacion):
    cur = mysql.connection.cursor()
    cur.execute("SELECT IDENTIFICACION_EMPLEADO, NOMBRE, APELLIDO, EDAD, CORREO, GENERO, CONTRASENA, ESPECIALIDAD, HORARIO, ESTADO FROM empleado WHERE IDENTIFICACION_EMPLEADO = %s", (identificacion,))
    info_empleado = cur.fetchone()
    cur.close()
    return info_empleado

# Ruta para el panel del miembro
@app.route('/miembro')
def miembro():
    identificacion = session.get('identificacion')
    info_miembro = obtener_info_miembro(identificacion)

    if info_miembro:
        # Obtener las reservas del miembro actual
        cur = mysql.connection.cursor()
        cur.execute('''
    SELECT c.*, r.ID_RESERVA, e.NOMBRE AS NOMBRE_INSTRUCTOR
    FROM clase c
    JOIN reserva_clase r ON c.ID_CLASE = r.ID_CLASE
    JOIN empleado e ON c.INSTRUCTOR = e.IDENTIFICACION_EMPLEADO
    WHERE r.IDENTIFICACION_MIEMBRO = %s
''', (identificacion,))
        reservas = cur.fetchall()
        cur.close()

        return render_template('miembro.html', info_miembro=info_miembro, reservas=reservas)
    else:
        # Manejar el caso en que no se encuentre la información del miembro
        flash('Error al obtener la información del miembro.')
        return redirect(url_for('login'))


# Ruta para el panel del administrador (administrador)
@app.route('/administrador')
def administrador():
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

#plan de trabajo
@app.route('/planes_trabajo_ins')
def planes_trabajo_ins():
    cur = mysql.connection.cursor()
    cur.execute("""SELECT *
                FROM miembros
                WHERE IDENTIFICACION_EMPLEADO = 0
                AND ID_MEMBRESIA != 0;
                """)
    data = cur.fetchall()
    mysql.connection.commit()
    return render_template('planes_trabajo_ins.html', miembros=data)

#vista de asignar plan de trabajo
@app.route('/vista_asignar_plan_trabajo/<idm>')
def vista_asignar_plan_trabajo(idm):
    cur = mysql.connection.cursor()
    cur.execute("""SELECT *
                FROM planes_trabajo
                """)
    data = cur.fetchall()
    idm = idm
    mysql.connection.commit()
    print(data)
    return render_template('vista_asignar_plan_trabajo.html', planes=data, idm=idm)

# accion de asignar plan de trabajo
@app.route("/asignar/<id>/<idm>", methods=['POST'])
def getidclase(id, idm):
    identificacion = session.get('identificacion')
    idm = request.args.get('idm')
    if request.method == 'POST':
        fechainicio = request.form['fecha_inicio']
        fechafin = request.form['fecha_fin']
        cur = mysql.connection.cursor()
        cur.execute("""INSERT INTO asignacion_pla_trabajo (ID_MIEMBRO_PLAN, ID_PLAN, 
                    IDENTIFICACION_EMPLEADO, FECHA_INICIO, FECHA_FIN) VALUES (%s, %s, %s, %s, %s)""",
                        (idm, id, identificacion,fechainicio,fechafin))
        flash('Información editada correctamente')
        return redirect(url_for('info_personal_user'))
    

# perfil de miembro
@app.route('/perfil')
def perfil():
    identificacion = session.get('identificacion')
    info_miembro = obtener_info_miembro(identificacion)
    if info_miembro:
        return render_template('perfil.html', info_miembro=info_miembro)
    else:
        # Manejar el caso en el que no se encuentre la información del miembro
        flash('Error al obtener la información del miembro.')

# perfil de instructor
@app.route('/perfil_instructor')
def perfil_instructor():
    identificacion = session.get('identificacion')
    info_empleado = obtener_info_empleado(identificacion)
    if info_empleado:
        return render_template('perfil_instructor.html', info_empleado=info_empleado)
    else:
        # Manejar el caso en el que no se encuentre la información del miembro
        flash('Error al obtener la información del miembro.')
    
# formulario de edicion datos personales de miembro
@app.route('/info_personal_user')
def info_personal_user():
    identificacion = session.get('identificacion')
    info_miembro = obtener_info_miembro(identificacion)
    if info_miembro:
        return render_template('info_personal_user.html', info_miembro=info_miembro)
    else:
        flash('Error al obtener la información del miembro.')
        return redirect(url_for('perfil'))

# formulario de edicion datos personales de instructor
@app.route('/editar_info_personal_ins')
def editar_info_personal_ins():
    identificacion = session.get('identificacion')
    info_empleado = obtener_info_empleado(identificacion)
    if info_empleado:
        return render_template('editar_info_personal_ins.html', info_empleado=info_empleado)
    else:
        flash('Error al obtener la información del instructor.')
        return redirect(url_for('perfil_instructor'))

# accion de editar datos miembro desde rol miembro
@app.route("/actualizar/<id>", methods=['POST'])
def getidentificacion(id):
    identificacion = session.get('identificacion')
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        edad = request.form['edad']
        correo = request.form['correo']
        telefono = request.form['telefono']

        cur = mysql.connection.cursor()
        cur.execute('UPDATE miembros SET NOMBRE = %s, APELLIDO = %s, EDAD = %s, CORREO = %s, TELEFONO = %s WHERE IDENTIFICACION = %s',
                    (nombre, apellido, edad, correo, telefono, id))
        mysql.connection.commit()
        info_empleado = obtener_info_empleado(identificacion)
        flash('Información editada correctamente')
        return redirect(url_for('info_personal_user'))
    
# accion de editar datos instructor desde rol instructor
@app.route("/actualizar_ins/<id>", methods=['POST'])
def getidentificacion_ins(id):
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        edad = request.form['edad']
        correo = request.form['correo']
        genero = request.form['genero']

        cur = mysql.connection.cursor()
        cur.execute('UPDATE empleado SET NOMBRE = %s, APELLIDO = %s, EDAD = %s, CORREO = %s, GENERO = %s WHERE IDENTIFICACION_EMPLEADO = %s',
                    (nombre, apellido, edad, correo, genero, id))
        mysql.connection.commit()
        flash('Información editada correctamente')
        return redirect(url_for('editar_info_personal_ins'))

# cambiar contraseña rol miembro
@app.route('/cambio_contrasena_user')
def cambio_contrasena_user():
    identificacion = session.get('identificacion')
    info_miembro = obtener_info_miembro(identificacion)
    if info_miembro:
        return render_template('cambio_contrasena_user.html', info_miembro=info_miembro)
    else:
        # Manejar el caso en el que no se encuentre la información del miembro
        flash('Error al obtener la información del miembro.')

# cambiar contraseña rol instructor
@app.route('/cambio_contrasena_ins')
def cambio_contrasena_ins():
    identificacion = session.get('identificacion')
    info_empleado = obtener_info_empleado(identificacion)
    if info_empleado:
        return render_template('cambio_contrasena_ins.html', info_empleado=info_empleado)
    else:
        # Manejar el caso en el que no se encuentre la información del miembro
        flash('Error al obtener la información del miembro.')

# accion de editar contraseña miembro desde rol miembro
@app.route("/actualizarcontrasena/<id>", methods=['POST'])
def actualizar_contrasena(id):
    info_miembro = obtener_info_miembro(id)
    if request.method == 'POST':
        # Obtener las contraseñas del formulario
        current_password = request.form['currend_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        print('CONTRASEÑA ACTUAL:' + info_miembro[6])
        # Validar que la contraseña actual sea correcta
        if current_password != info_miembro[6]:
            flash('La contraseña actual no es correcta.')
            return redirect(url_for('cambio_contrasena_user'))

        # Validar que la nueva contraseña y la confirmación coincidan
        if new_password != confirm_password:
            flash('La nueva contraseña y la confirmación no coinciden.')
            return redirect(url_for('cambio_contrasena_user'))

        # Realizar la actualización de la contraseña en la base de datos
        cur = mysql.connection.cursor()
        cur.execute('UPDATE miembros SET CONTRASENA = %s WHERE IDENTIFICACION = %s',
                    (new_password, id))
        mysql.connection.commit()
        flash('Contraseña actualizada correctamente.')
        info_miembro = obtener_info_miembro(id)

    return redirect(url_for('cambio_contrasena_user'))

# accion de editar contraseña miembro desde rol miembro
@app.route("/actualizarcontrasenains/<id>", methods=['POST'])
def actualizar_contrasena_ins(id):
    info_empleado = obtener_info_empleado(id)
    if request.method == 'POST':
        # Obtener las contraseñas del formulario
        current_password = request.form['currend_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']
        print('CONTRASEÑA ACTUAL:' + info_empleado[6])
        # Validar que la contraseña actual sea correcta
        if current_password != info_empleado[6]:
            flash('La contraseña actual no es correcta.')
            return redirect(url_for('cambio_contrasena_ins'))

        # Validar que la nueva contraseña y la confirmación coincidan
        if new_password != confirm_password:
            flash('La nueva contraseña y la confirmación no coinciden.')
            return redirect(url_for('cambio_contrasena_ins'))

        # Realizar la actualización de la contraseña en la base de datos
        cur = mysql.connection.cursor()
        cur.execute('UPDATE empleado SET CONTRASENA = %s WHERE IDENTIFICACION_EMPLEADO = %s',
                    (new_password, id))
        mysql.connection.commit()
        flash('Contraseña actualizada correctamente.')
        info_empleado = obtener_info_empleado(id)

    return redirect(url_for('cambio_contrasena_ins'))

@app.route('/membresia_user')
def membresia_user():
    return render_template('membresia_user.html')

# Ruta para el panel del entrenador (entrenador)
@app.route('/entrenador')
def entrenador():
    identificacion = session.get('identificacion')
    info_empleado = obtener_info_empleado(identificacion)

    if info_empleado:
        # Obtener las reservas del miembro actual
        cur = mysql.connection.cursor()
        cur.execute('''
                    SELECT asignacion_pla_trabajo.*, planes_trabajo.NOMBRE AS NOMBRE_PLAN, planes_trabajo.DESCRIPCION AS DESCRIPCION_PLAN
                    FROM asignacion_pla_trabajo
                    JOIN planes_trabajo ON asignacion_pla_trabajo.ID_PLAN = planes_trabajo.ID_PLAN
                    WHERE asignacion_pla_trabajo.IDENTIFICACION_EMPLEADO = %s;

                ''', (identificacion,))
        planestrabajo = cur.fetchall()
        cur.close()

        return render_template('entrenador.html', info_empleado=info_empleado, planestrabajo=planestrabajo)
    else:
        # Manejar el caso en que no se encuentre la información del miembro
        flash('Error al obtener la información del miembro.')
        return redirect(url_for('login'))


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

#vista de reservas desde miembro
@app.route('/reservas_miembro')
def reservas_miembro():
    identificacion = session.get('identificacion')
    info_miembro = obtener_info_miembro(identificacion)
    if info_miembro:
        return render_template('reservas_miembro.html', info_miembro=info_miembro)
    else:
        # Manejar el caso en el que no se encuentre la información del miembro
        flash('Error al obtener la información del miembro.')

#reservar clase desde miembro
@app.route('/reservar_clase')
def reservar_clase():
        cur = mysql.connection.cursor()
        cur.execute("SELECT clase.*, empleado.NOMBRE AS NOMBRE_INSTRUCTOR FROM clase INNER JOIN empleado ON clase.INSTRUCTOR = empleado.IDENTIFICACION_EMPLEADO")  
        rows = cur.fetchall()
        cur.close()
        return render_template('reservar_clase.html', rows=rows)


#accion de reservar clase desde miembro
@app.route("/accion_reservar_clase/<id>", methods=['GET', 'POST'])
def accion_reservar_clase(id):
    identificacion = session.get('identificacion')

    try:
        # Verificar si el usuario ya ha reservado la clase
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM reserva_clase WHERE ID_CLASE = %s AND IDENTIFICACION_MIEMBRO = %s',
                    (id, identificacion))
        existing_reservation = cur.fetchone()

        if existing_reservation:
            flash('Ya has reservado esta clase anteriormente.')
        else:
            # Iniciar la transacción
            cur.execute('START TRANSACTION')

            # Realizar la inserción en la tabla reserva_clase
            cur.execute('INSERT INTO reserva_clase (ID_CLASE, IDENTIFICACION_MIEMBRO) VALUES (%s, %s)',
                        (id, identificacion))

            # Confirmar la transacción
            cur.execute('COMMIT')

            flash('Clase agendada correctamente.')

    except Exception as e:
        # Manejar cualquier excepción que pueda ocurrir durante la transacción
        cur.execute('ROLLBACK')
        flash(f'Error al agendar la clase: {str(e)}')

    finally:
        # Cerrar el cursor después de realizar la operación
        if cur:
            cur.close()

    return redirect(url_for('reservar_clase'))

  

#reservar maquina desde miembro
@app.route('/reservar_maquina')
def reservar_maquina():
        cur = mysql.connection.cursor()
        cur.execute("SELECT clase.*, empleado.NOMBRE AS NOMBRE_INSTRUCTOR FROM clase INNER JOIN empleado ON clase.INSTRUCTOR = empleado.IDENTIFICACION_EMPLEADO")  
        rows = cur.fetchall()
        cur.close()
        return render_template('reservar_maquina.html', rows=rows)

#mostrar plan de trabajo de miembro
@app.route('/plan_de_trabajo_miembro')
def plan_de_trabajo_miembro():
        identificacion = session.get('identificacion')
        info_miembro = obtener_info_miembro(identificacion)
        cur = mysql.connection.cursor()
        cur.execute("""SELECT asignacion_pla_trabajo.*, planes_trabajo.NOMBRE AS NOMBRE_PLAN, planes_trabajo.DESCRIPCION AS DESCRIPCION_PLAN, empleado.NOMBRE AS NOMBRE_EMPLEADO
                FROM asignacion_pla_trabajo
                JOIN planes_trabajo ON asignacion_pla_trabajo.ID_PLAN = planes_trabajo.ID_PLAN
                JOIN empleado ON asignacion_pla_trabajo.IDENTIFICACION_EMPLEADO = empleado.IDENTIFICACION_EMPLEADO
                WHERE asignacion_pla_trabajo.ID_MIEMBRO_PLAN = %s;
                """, (identificacion,))  
        rows = cur.fetchall()
        cur.close()
        return render_template('plan_de_trabajo_miembro.html', rows=rows, info_miembro=info_miembro)

#vista estdo de membresia desde miembro
@app.route('/miembro_estado_membresia')
def miembro_estado_membresia():
        identificacion = session.get('identificacion')
        info_miembro = obtener_info_miembro(identificacion)
        cur = mysql.connection.cursor()
        cur.execute("""SELECT m.* FROM miembros AS mi JOIN 
                    membresia_miembros AS m ON mi.ID_MEMBRESIA = 
                    m.ID_MEMBRESIA WHERE mi.IDENTIFICACION = %s;
                """, (identificacion,))  
        rows = cur.fetchall()
        cur.close()
        return render_template('miembro_estado_membresia.html', rows=rows, info_miembro=info_miembro)

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
