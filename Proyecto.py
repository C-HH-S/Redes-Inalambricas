import datetime
from flask_mysqldb import MySQL
from flask import Flask, session ,jsonify, render_template, request, redirect, url_for, flash
import mysql.connector
from werkzeug.security import check_password_hash

app = Flask(__name__, static_folder='static', template_folder='template')


# Configura la conexión a la base de datos MySQL
app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = ""
app.config['MYSQL_DB'] = "bd_gimnasio2"
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
        cur.execute('''
    SELECT rm.*, m.NOMBRE AS nombre_maquina
    FROM reserva_maquina rm
    JOIN maquina m ON rm.ID_MAQUINA = m.ID_MAQUINA
    WHERE rm.IDENTIFICACION_MIEMBRO = %s
''', (identificacion,))
        reservasm = cur.fetchall()
        cur.close()


        return render_template('miembro.html', info_miembro=info_miembro, reservas=reservas, reservasm=reservasm)
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
                WHERE ID_PLAN IS NULL
                AND ID_MEMBRESIA <> 0
                AND ESTADO <> 0
                AND ID_ESTADO_MEM <> 0;
                ;
                """)
    data = cur.fetchall()
    mysql.connection.commit()
    return render_template('planes_trabajo_ins.html', miembros=data)

# progreso plan de trabajo 
@app.route('/proceso_plan_trabajo')
def proceso_plan_trabajo():
    identificacion = session.get('identificacion')
    cur = mysql.connection.cursor()
    cur.execute("""
        SELECT asignacion.*, empleado.NOMBRE AS nombre_empleado 
                FROM asignacion_pla_trabajo asignacion 
                JOIN empleado ON asignacion.IDENTIFICACION_EMPLEADO = 
                empleado.IDENTIFICACION_EMPLEADO 
                WHERE asignacion.ID_MIEMBRO_PLAN = %s;
            """, (identificacion,))
    
    data = cur.fetchall()
    cur.execute("""
    SELECT *
    FROM progreso_plan_trabajo
    WHERE IDENTIFICACION_MIEMBRO = %s;
    """, (identificacion,))
    dataprogreso = cur.fetchall()
    cur.close()
    print(data)
    # Verificar si hay datos en 'data'
    if not data:
        flash ('No hay plan trabajo para este miembro.')
        return render_template('proceso_plan_trabajo.html', )

    mysql.connection.commit()
    return render_template('proceso_plan_trabajo.html', rows=data, progreso=dataprogreso)

# Ruta para ingresar el progreso del plan de trabajo
@app.route('/ingresar_progreso/<id>', methods=['GET', 'POST'])
def ingresar_progreso(id):
    identificacion = session.get('identificacion')

    # Verifica si se encontró el ID_ASIG_PLAN
    if id is None:
        flash('No se encontró el plan de trabajo para ingresar progreso.', 'danger')
        return redirect(url_for('miembro'))

    if request.method == 'POST':
        fecha_avance = request.form.get('fecha_avance')
        descripcion_avance = request.form.get('descripcion_avance')
        horas_trabajadas = request.form.get('horas_trabajadas')

        # Insertar en la base de datos
        try:
            cur = mysql.connection.cursor()
            cur.execute("""
                INSERT INTO progreso_plan_trabajo (ID_ASIG_PLAN, IDENTIFICACION_MIEMBRO, FECHA_AVANCE, DESCRIPCION_AVANCE, HORAS_TRABAJADAS)
                VALUES (%s, %s, %s, %s, %s)
            """, (id, identificacion, fecha_avance, descripcion_avance, horas_trabajadas))
            
            mysql.connection.commit()
            cur.close()
            flash('Progreso registrado correctamente.', 'success')
            return redirect(url_for('proceso_plan_trabajo'))
        except Exception as e:
            flash(f'Error al registrar el progreso: {str(e)}', 'danger')

    return render_template('ingresar_progreso.html', id=id )


#vista de asignar plan de trabajo
@app.route('/vista_asignar_plan_trabajo/<idm>')
def vista_asignar_plan_trabajo(idm):
    cur = mysql.connection.cursor()
    cur.execute("""SELECT *
                FROM planes_trabajo
                """)
    data = cur.fetchall()
    global idmiembro 
    idmiembro = idm
    mysql.connection.commit()
    return render_template('vista_asignar_plan_trabajo.html', planes=data)

# accion de asignar plan de trabajo
@app.route("/asignar/<id>", methods=['POST'])
def getidclase(id):
    identificacion = session.get('identificacion')

    if request.method == 'POST':
        fechainicio = request.form['fecha_inicio']
        fechafin = request.form['fecha_fin']
        try:
            cur = mysql.connection.cursor()
            cur.execute('SET foreign_key_checks = 0;')
            cur.execute("""UPDATE miembros SET ID_PLAN = %s WHERE IDENTIFICACION = %s""", (id, idmiembro))
            cur.execute("""INSERT INTO asignacion_pla_trabajo (ID_MIEMBRO_PLAN, ID_PLAN, 
                        IDENTIFICACION_EMPLEADO, FECHA_INICIO, FECHA_FIN) VALUES (%s, %s, %s, %s, %s)""",
                        (idmiembro, id, identificacion, fechainicio, fechafin))
            mysql.connection.commit()
            flash('Plan de trabajo asignado correctamente')
            return redirect(url_for('planes_trabajo_ins'))
        except Exception as e:
            # Si hay algún error, puedes imprimirlo para depuración
            print(f"Error al insertar en la base de datos: {str(e)}")
            flash('Error al asignar plan de trabajo')
            mysql.connection.rollback()  # Revertir la transacción
        finally:
            cur.close()

    # Agrega un retorno para el caso en que la solicitud no sea POST
    return "Algo para mostrar si la solicitud no es POST"

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

            cur.execute("SELECT COUNT(*) FROM reserva_clase WHERE IDENTIFICACION_MIEMBRO = %s", (identificacion,))
            cantidad_reservas = cur.fetchone()[0]
            LIMITE_RESERVAS = 5

            if cantidad_reservas >= LIMITE_RESERVAS:
                flash('No se pueden hacer más de 5 reservas.')
                # Puedes redirigir al usuario a una página de error o a donde prefieras
            else:
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
@app.route("/reservar_maquina", methods=['GET', 'POST'])
def reservar_maquina():
        cur = mysql.connection.cursor()
        cur.execute("""SELECT m.*, e.NOMBRE AS estado_nombre FROM maquina m 
                    JOIN estado_maquinaria e ON m.ID_ESTADO_MAQUINA = e.ID_ESTADO_MAQUINA WHERE e.NOMBRE = 1
                    """)  
        rows = cur.fetchall()
        cur.close()
        return render_template('reservar_maquina.html', rows=rows)

from MySQLdb import IntegrityError

# ...

# Reservar máquina desde miembro
@app.route('/vista_reservar_maquina/<id>', methods=['GET', 'POST'])
def vista_reservar_maquina(id):
        
    identificacion = session.get('identificacion')

    if request.method == 'POST':
        identificacion = session.get('identificacion')
        fecha = request.form.get('fecha')
        horainicio = request.form.get('horainicio')
        horafin = request.form.get('horafin')

        try:
            # Verificar si el usuario ya ha reservado la máquina
            cur = mysql.connection.cursor()
            cur.execute('SELECT * FROM reserva_maquina WHERE ID_MAQUINA = %s AND IDENTIFICACION_MIEMBRO = %s',
                        (id, identificacion))
            existing_reservations = cur.fetchall()

            if existing_reservations:
                flash('Ya has reservado esta máquina anteriormente.')
                return redirect(url_for('reservar_maquina'))
            else:
                cur.execute("SELECT COUNT(*) FROM reserva_maquina WHERE IDENTIFICACION_MIEMBRO = %s", (identificacion,))
                cantidad_reservas = cur.fetchone()[0]
                LIMITE_RESERVAS = 5

                if cantidad_reservas >= LIMITE_RESERVAS:
                    flash('No se pueden hacer más de 5 reservas.')
                    return redirect(url_for('reservar_maquina'))
                else:
                    cur = mysql.connection.cursor()
                    cur.execute(
                        'INSERT INTO reserva_maquina (ID_MAQUINA, IDENTIFICACION_MIEMBRO, FECHA, HORA_INICIO, HORA_FIN) VALUES (%s, %s, %s, %s, %s)',
                        (id, identificacion, fecha, horainicio, horafin)
                    )
                    mysql.connection.commit()
                    cur.close()
                    flash('Reserva realizada correctamente.')
                    return redirect(url_for('reservar_maquina'))
        except IntegrityError as e:
            flash('Error: Ya has reservado esta máquina anteriormente.')
            return redirect(url_for('reservar_maquina'))
        except Exception as e:
            flash(f'Error al realizar la reserva: {str(e)}')
            return redirect(url_for('reservar_maquina'))
    else:
        fecha = None
        horainicio = None
        horafin = None
        cur = mysql.connection.cursor()
        cur.execute("""SELECT m.*, e.NOMBRE AS estado_nombre 
                    FROM maquina m 
                    JOIN estado_maquinaria e ON m.ID_ESTADO_MAQUINA = e.ID_ESTADO_MAQUINA 
                    WHERE m.ID_MAQUINA = %s 
                    """, (id,))
        rows = cur.fetchall()
        cur.close()
        return render_template('vista_reservar_maquina.html', rows=rows)

# Acción de reservar máquina desde miembro
@app.route("/accion_reservar_maquina/<id>", methods=['GET', 'POST'])
def accion_reservar_maquina(id):
    identificacion = session.get('identificacion')

    if request.method == 'POST':
        identificacion = session.get('identificacion')
        fecha = request.form.get('fecha')
        horainicio = request.form.get('horainicio')
        horafin = request.form.get('horafin')

    try:
        # Verificar si el usuario ya ha reservado la máquina
        cur = mysql.connection.cursor()
        cur.execute('SELECT * FROM reserva_maquina WHERE ID_MAQUINA = %s AND IDENTIFICACION_MIEMBRO = %s',
                    (id, identificacion))
        existing_reservations = cur.fetchall()

        if existing_reservations:
            flash('Ya has reservado esta máquina anteriormente.')
        else:
            cur.execute("SELECT COUNT(*) FROM reserva_maquina WHERE IDENTIFICACION_MIEMBRO = %s", (identificacion,))
            cantidad_reservas = cur.fetchone()[0]
            LIMITE_RESERVAS = 5

            if cantidad_reservas >= LIMITE_RESERVAS:
                flash('No se pueden hacer más de 5 reservas.')
            else:
                cur = mysql.connection.cursor()
                cur.execute(
                'INSERT INTO reserva_maquina (ID_MAQUINA, IDENTIFICACION_MIEMBRO, FECHA, HORA_INICIO, HORA_FIN) VALUES (%s, %s, %s, %s, %s)',
                (id, identificacion, fecha, horainicio, horafin)
            )
            mysql.connection.commit()
            cur.close()
            flash('Reserva realizada correctamente.')
            return redirect(url_for('reservas_miembro'))
    except Exception as e:
                flash(f'Error al realizar la reserva: {str(e)}')
                return redirect(url_for('reservar_maquina'))


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
        cur.execute("""SELECT mi.*, m.*, em.FECHA_INICIO, em.FECHA_FIN
                FROM miembros AS mi
                JOIN membresia_precios AS m ON mi.ID_MEMBRESIA = m.ID_MEMBRESIA
                JOIN estado_membresia AS em ON mi.ID_MEMBRESIA = em.ID_MEMBRESIA
                WHERE mi.IDENTIFICACION  = %s;
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
        cur.execute("SELECT estado FROM miembros WHERE IDENTIFICACION = %s", (miembro_id,))
        estado_actual = cur.fetchone()
        print(estado_actual)
        # Cambia el estado (por ejemplo, de True a False o viceversa)
        nuevo_estado = not estado_actual[0]
        # Realiza la actualización en la base de datos
        cur.execute("UPDATE miembros SET estado = %s WHERE IDENTIFICACION = %s", (nuevo_estado, miembro_id))
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
            flash('¡Miembro encontrado!.')
            return render_template('buscar_miembro.html', resultados=data)
        else:
            flash('No se encontraron miembros con esa identificación.')
    return render_template('buscar_miembro.html')


# Vista para agregar máquina
@app.route('/agregar_maquina', methods=['GET', 'POST'])
def agregar_maquina():
    if request.method == 'POST':
        nombre = request.form['nombre']
        estado = request.form['estado']
        proveedor = request.form['proveedor']
        precio = request.form['precio']
        fechaCompra = request.form['fechaCompra']
        disponibilidad = request.form['disponibilidad']

        cur = mysql.connection.cursor()

        # Verificar si el proveedor ya existe
        cur.execute('SELECT ID_PROVEEDOR FROM proveedor_maquinaria WHERE NOMBRE = %s', (proveedor,))
        resultado = cur.fetchone()

        if resultado:
            # Si el proveedor existe, obtén el ID_PROVEEDOR
            id_proveedor = resultado[0]
        else:
            # Si el proveedor no existe, inserta y obtén el ID_PROVEEDOR
            cur.execute('INSERT INTO proveedor_maquinaria (NOMBRE) VALUES (%s)', (proveedor,))
            mysql.connection.commit()
            cur.execute('SELECT LAST_INSERT_ID()')
            id_proveedor = cur.fetchone()[0]
        
        cur.execute('INSERT INTO disponibilidad_maquinaria (DISPONIBILIDAD) VALUES (%s)', (disponibilidad,))
        cur.execute('SELECT LAST_INSERT_ID()')
        id_dispo = cur.fetchone()[0]
        cur.execute('INSERT INTO estado_maquinaria (NOMBRE) VALUES (%s)', (estado,))
        cur.execute('SELECT LAST_INSERT_ID()')
        id_estado = cur.fetchone()[0]

        # Insertar en la tabla maquina
        cur.execute('SET foreign_key_checks = 0;')
        cur.execute('INSERT INTO maquina (NOMBRE, ID_ESTADO_MAQUINA, ID_DISPONIBILIDAD_MAQUINARIA) VALUES (%s, %s,%s)',
                    (nombre, id_dispo, id_estado))
        cur.execute('SELECT LAST_INSERT_ID()')
        id_maquina = cur.fetchone()[0]

        # Insertar en la tabla historial_maquinaria
        cur.execute('INSERT INTO historial_maquinaria (FECHA_COMPRA, PRECIO, ID_PROVEEDOR, ID_MAQUINA) VALUES (%s, %s, %s, %s)',
                    (fechaCompra, precio, id_proveedor, id_maquina))

        mysql.connection.commit()
        cur.close()

        flash('Máquina agregada correctamente')

    return render_template('agregar_maquina.html')


# Vista mirar el listado de maquinas
@app.route('/lista_maquinas', methods=['GET', 'POST'])
def lista_maquinas():
    data = None
    cur = mysql.connection.cursor()
    cur.execute('SELECT m.ID_MAQUINA, m.NOMBRE, m.ID_ESTADO_MAQUINA, m.ID_DISPONIBILIDAD_MAQUINARIA, em.NOMBRE AS estado_nombre, dm.DISPONIBILIDAD AS disponibilidad_nombre FROM maquina m JOIN estado_maquinaria em ON m.ID_ESTADO_MAQUINA = em.ID_ESTADO_MAQUINA JOIN disponibilidad_maquinaria dm ON m.ID_DISPONIBILIDAD_MAQUINARIA = dm.ID_DISPONIBILIDAD_MAQUINARIA')
    data = cur.fetchall()
    mysql.connection.commit()
    return render_template('lista_maquinas.html', maquinas=data)

# Vista del estado de máquinas
@app.route('/estado_maquinas', methods=['GET', 'POST'])
def estado_maquinas():
    data = None
    cur = mysql.connection.cursor()

    # Obtén los datos de la tabla maquina, incluyendo la llave foránea para estado y disponibilidad
    cur.execute('SELECT m.ID_MAQUINA, m.NOMBRE, m.ID_ESTADO_MAQUINA, m.ID_DISPONIBILIDAD_MAQUINARIA, em.NOMBRE AS estado_nombre, dm.DISPONIBILIDAD AS disponibilidad_nombre FROM maquina m JOIN estado_maquinaria em ON m.ID_ESTADO_MAQUINA = em.ID_ESTADO_MAQUINA JOIN disponibilidad_maquinaria dm ON m.ID_DISPONIBILIDAD_MAQUINARIA = dm.ID_DISPONIBILIDAD_MAQUINARIA')
    data = cur.fetchall()

    mysql.connection.commit()
    return render_template('estado_maquinas.html', maquinas=data)


# accion de editar estado de máquina
@app.route('/cambiar_estado_maquina', methods=['POST'])
def cambiar_estado():
    if request.method == 'POST':
        estado_id = request.form.get('estado_id')
        dispo_id = request.form.get('dispo_id')

        cur = mysql.connection.cursor()

        # Obtén el nombre actual del estado en estado_maquinaria
        cur.execute("SELECT NOMBRE FROM estado_maquinaria WHERE ID_ESTADO_MAQUINA = %s", (estado_id,))
        estado_actual = cur.fetchone()

        # Obtén la disponibilidad actual en disponibilidad_maquinaria
        cur.execute("SELECT DISPONIBILIDAD FROM disponibilidad_maquinaria WHERE ID_DISPONIBILIDAD_MAQUINARIA = %s", (dispo_id,))
        disponibilidad_actual = cur.fetchone()

        if estado_actual is not None and disponibilidad_actual is not None:
            # Cambia el nombre de 'Activo' a 'Inactivo' y viceversa
            nuevo_estado = 1 if estado_actual[0] == 0 else 0
            nuevo_disponibilidad = 1 - disponibilidad_actual[0]  # Cambia 0 por 1 y viceversa

            # Actualiza el nombre en estado_maquinaria
            cur.execute("UPDATE estado_maquinaria SET NOMBRE = %s WHERE ID_ESTADO_MAQUINA = %s", (nuevo_estado, estado_id))

            # Actualiza la disponibilidad en disponibilidad_maquinaria
            cur.execute("UPDATE disponibilidad_maquinaria SET DISPONIBILIDAD = %s WHERE ID_DISPONIBILIDAD_MAQUINARIA = %s", (nuevo_disponibilidad, dispo_id))

            mysql.connection.commit()
            flash('Estado actualizado correctamente')
        else:
            flash('Error: Estado o disponibilidad no encontrados')

        cur.close()
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
        print(data)
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
    # traer solo las maquinas que estan en mal estado
    cur.execute('''
    SELECT maquina.*, estado_maquinaria.NOMBRE AS estado_nombre
    FROM maquina
    JOIN estado_maquinaria ON maquina.ID_ESTADO_MAQUINA = estado_maquinaria.ID_ESTADO_MAQUINA
    WHERE estado_maquinaria.NOMBRE = 0
    ''')
    data = cur.fetchall()
    mysql.connection.commit()
    return render_template('mantenimiento_maquinas.html', miembros=data)

# agendar cita mantenimiento
@app.route("/mantenimiento/<maquina_id>", methods=['GET', 'POST'])
def getmantenimiento(maquina_id):
    cur = mysql.connection.cursor()
    cur.execute('SET foreign_key_checks = 0;')
    cur.execute("SELECT * FROM maquina WHERE ID_MAQUINA = %s", (maquina_id,))
    maquina = cur.fetchone()
    cur.close()

    if request.method == 'POST':
        fecha = request.form.get('fecha')
        hora = request.form.get('hora')
        observacion = request.form.get('observacion')

        cur = mysql.connection.cursor()

        cur.execute("INSERT INTO proceso_citas (TIPO_ESTADO) VALUES (%s)", (str('En proceso'),))
        cur.execute("SELECT LAST_INSERT_ID()")
        last_inserted_id = cur.fetchone()[0]

        # Insertar la cita de mantenimiento en la tabla citas_mantenimiento
        cur.execute("INSERT INTO citas_mantenimiento (ID_MAQUINA, FECHA_CITA, HORA, OBSERVACION, ID_ESTADO_CITA) VALUES (%s, %s, %s, %s, %s)",
                    (maquina_id, fecha, hora, observacion, last_inserted_id))


        mysql.connection.commit()
        cur.close()

        flash(f'Cita agendada para {fecha} a las {hora}')

    return render_template('vista_mantenimiento.html', maquina=maquina)



if __name__ == '__main__':
    app.run(debug=True)
