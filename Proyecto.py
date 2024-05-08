from flask_mysqldb import MySQL
from flask import Flask, render_template, request, redirect, url_for,session, make_response
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib
import matplotlib.pyplot as plt
from flask import send_file
from flask import flash
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__, static_folder='static', template_folder='template')




# Configura la conexión a la base de datos MySQL
app.config['MYSQL_HOST'] = "localhost"
app.config['MYSQL_USER'] = "root"
app.config['MYSQL_PASSWORD'] = ""
app.config['MYSQL_DB'] = "proyecto"
mysql = MySQL(app)

# Inicializar sesion
app.secret_key = 'mysecretkey'

# Ruta para el panel del Usuario
@app.route('/')
def Usuario():
    return render_template('Usuario.html')

# Ruta para el panel de nosotros
@app.route('/NOSOTROS')
def NOSOTROS():
    return render_template('NOSOTROS.html')

# Ruta para el panel de contactos
@app.route('/CONTACTOS')
def CONTACTOS():
    return render_template('CONTACTOS.html')



@app.route('/Ocupacional', methods=['GET', 'POST'])
def Ocupacional():

    if request.method == 'POST':
        # Obtener los datos del formulario
        Frecuencia = float(request.form['Frecuencia'])
        Altura_irradiacion = float(request.form['Altura_irradiacion'])
        Potencia = float(request.form['Potencia'])
        Ganancia = float(request.form['Ganancia'])
        accesibilidad = request.form['accesibilidad']
        Nombre = request.form['Nombre']

        # Verificar si la frecuencia está fuera del rango permitido
        if Frecuencia < 30 or Frecuencia > 300000:
            flash('Frecuencia fuera de rango. Debe estar entre 30 y 300000 MHz.', 'warning')
            return redirect(url_for('Ocupacional'))
        
        # Agregar lógica de exposición ocupacional
        if 30 <= Frecuencia <= 400:
            resultado = 0.143 * (Ganancia + Potencia) ** 0.5
            resultado = round(resultado, 2)
        elif 400 < Frecuencia <= 2000:
            resultado = 2.92 * (Ganancia + Potencia) ** 0.5 / Frecuencia ** 0.5
            resultado = round(resultado, 2)
        elif 2000 < Frecuencia <= 300000:
            resultado = 0.0638 * (Ganancia + Potencia) ** 0.5
            resultado = round(resultado, 2)

        Altura_irradiacion_formula = Altura_irradiacion - 2  # Altura menos 2 metros

        # Calcular la distancia horizontal
        if resultado >= Altura_irradiacion_formula:
            distancia_horizontal = (resultado ** 2 - Altura_irradiacion_formula ** 2) ** 0.5
            distancia_horizontal = round(distancia_horizontal, 2)
        else:
            distancia_horizontal = 0  

        # Crear los puntos para el gráfico
        x = [0, 0, distancia_horizontal, 0] 
        y = [0, Altura_irradiacion_formula, 0, 0]

        matplotlib.use('Agg')

        # Graficar 
        plt.figure(figsize=(8, 6))  # Ajustar el tamaño del gráfico
        plt.plot(x, y, 'r-', linewidth=2)  # Ajustar el grosor de la línea
        plt.scatter(x, y, color='blue', s=50, label='Puntos')  # Añadir puntos para mayor claridad y atractivo visual
        plt.xlabel('Distancia Horizontal', fontsize=12)  # Ajustar tamaño de etiquetas y título
        plt.ylabel('Altura', fontsize=12)
        plt.title('', fontsize=14)
        plt.legend()

        # Mostrar los valores de cada punto
        for i in range(len(x)):
            plt.text(x[i], y[i], f'({x[i]}, {y[i]})', 
                    verticalalignment='bottom', 
                    horizontalalignment='left', 
                    color='blue', 
                    fontweight='bold',
                    fontsize=10)  # Ajustar tamaño del texto

        plt.grid(True, linestyle='--', alpha=0.5)  # Añadir cuadrícula con transparencia
        plt.tight_layout()  # Ajustar el diseño del gráfico
        imagen_path = 'static/triangulo.png'  # Definir la ruta donde se guardará la imagen
        plt.savefig(imagen_path)  # Guardar la imagen del gráfico
        plt.show()  # Mostrar el gráfico

        # Redirigir a la página de resultados con los datos y la ruta de la imagen como argumentos de la URL
        return redirect(url_for('mostrar_resultados_2', resultado=resultado, distancia_horizontal=distancia_horizontal,
                        Altura_irradiacion_formula=Altura_irradiacion_formula, imagen_path=imagen_path, 
                        accesibilidad=accesibilidad, Nombre=Nombre))
    
    return render_template('Ocupacional.html')

# Ruta para el panel de exposicion Poblacional
@app.route('/Poblacional', methods=['POST', 'GET'])
def Poblacional():

    if request.method == 'POST':
        # Obtener los datos del formulario
        Frecuencia = float(request.form['Frecuencia'])
        Altura_irradiacion = float(request.form['Altura_irradiacion'])
        Potencia = float(request.form['Potencia'])
        Ganancia = float(request.form['Ganancia'])
        accesibilidad = request.form['accesibilidad']
        Nombre = request.form['Nombre']
       
       # Verificar si la frecuencia está fuera del rango permitido
        if Frecuencia < 30 or Frecuencia > 300000:
            flash('Frecuencia fuera de rango. Debe estar entre 30 y 300000 MHz.', 'warning')
            return redirect(url_for('Poblacional'))
        
        # Agregar lógica de exposicion Poblacional
        if Frecuencia >= 30 and Frecuencia <= 400:
            resultado = 0.319 * (Ganancia + Potencia) ** 0.5 #Raiz cuadrada
            resultado = round(resultado, 2)
        elif Frecuencia > 400 and Frecuencia <= 2000:
            resultado = 6.38 * (Ganancia + Potencia) ** 0.5 / Frecuencia ** 0.5
            resultado = round(resultado, 2)
        elif Frecuencia > 2000 and Frecuencia <= 300000:
            resultado = 0.143 * (Ganancia + Potencia) ** 0.5
            resultado = round(resultado, 2)

        Altura_irradiacion_formula = Altura_irradiacion - 2  # Altura menos 2 metros

        # Calcular la distancia horizontal
        if resultado >= Altura_irradiacion_formula:
            distancia_horizontal = (resultado ** 2 - Altura_irradiacion_formula ** 2) ** 0.5
            distancia_horizontal = round(distancia_horizontal, 2)
        else:
            distancia_horizontal = 0  # O cualquier otro manejo de error que consideres apropiado

        # Crear los puntos para el gráfico
        x = [0, 0, distancia_horizontal, 0] 
        y = [0, Altura_irradiacion_formula, 0, 0]

        matplotlib.use('Agg')

        # Graficar 
        plt.figure(figsize=(8, 6))  # Ajustar el tamaño del gráfico
        plt.plot(x, y, 'r-', linewidth=2)  # Ajustar el grosor de la línea
        plt.scatter(x, y, color='blue', s=50, label='Puntos')  # Añadir puntos para mayor claridad y atractivo visual
        plt.xlabel('Distancia Horizontal', fontsize=12)  # Ajustar tamaño de etiquetas y título
        plt.ylabel('Altura', fontsize=12)
        plt.title('', fontsize=14)
        plt.legend()

        # Mostrar los valores de cada punto
        for i in range(len(x)):
            plt.text(x[i], y[i], f'({x[i]}, {y[i]})', 
                    verticalalignment='bottom', 
                    horizontalalignment='left', 
                    color='blue', 
                    fontweight='bold',
                    fontsize=10)  # Ajustar tamaño del texto

        plt.grid(True, linestyle='--', alpha=0.5)  # Añadir cuadrícula con transparencia
        plt.tight_layout()  # Ajustar el diseño del gráfico
        imagen_path = 'static/triangulo.png'  # Definir la ruta donde se guardará la imagen
        
        plt.savefig(imagen_path)  # Guardar la imagen del gráfico
        plt.show()  # Mostrar el gráfico

        # Redirigir a la página de resultados con los datos y la ruta de la imagen como argumentos de la URL
        return redirect(url_for('mostrar_resultados_1', resultado=resultado, distancia_horizontal=distancia_horizontal,
                                Altura_irradiacion_formula=Altura_irradiacion_formula, imagen_path=imagen_path, 
                                accesibilidad=accesibilidad, Nombre=Nombre))

    return render_template('Poblacional.html')

@app.route('/Resultados_pob', methods=['POST', 'GET'])
def mostrar_resultados_1():
    # Obtener los datos necesarios para mostrar en la plantilla
    resultado = request.args.get('resultado')
    distancia_horizontal = request.args.get('distancia_horizontal')
    Altura_irradiacion_formula = request.args.get('Altura_irradiacion_formula')
    imagen_path = request.args.get('imagen_path')  # Obtener la ruta de la imagen
    accesibilidad = request.args.get('accesibilidad')
    Nombre = request.args.get('Nombre')

    # Verificar si distancia_horizontal es igual a cero para mostrar el mensaje de alerta
    if distancia_horizontal == '0':
        flash('Altura mayor a distancia. No se puede medir', 'warning')

    if accesibilidad == '0':
        flash('No hay acceso de personas hacia la torre', 'warning')

    #PDF
    pdf_path = 'static/resultados.pdf'
    with PdfPages(pdf_path) as pdf:
        # Cargar la imagen generada del gráfico de resultados
        imagen = plt.imread(imagen_path)

        # Crear una nueva figura de matplotlib para el PDF
        fig, ax = plt.subplots(figsize=(8, 6))

        # Mostrar la imagen en la figura del PDF
        ax.imshow(imagen)
        ax.axis('off')  # Desactivar los ejes para la imagen

        texto = f'Distancia irradiante: {resultado}\n' \
                f'Distancia Horizontal: {distancia_horizontal}\n' \
                f'Altura de la antena: {Altura_irradiacion_formula}\n' \
                f'Resultados: Requiere medir y colocar el aviso correspondiente a {distancia_horizontal} metros de su antena'

        
        texto_obj = ax.text(0.05, 0.05, texto, transform=ax.transAxes, fontsize=10, verticalalignment='top')
        texto_obj.set_position((0.05, 0.000000009))

        # Guardar la figura en el PDF
        pdf.savefig(fig)
            
        # Renderizar la plantilla de resultados y pasar los datos como argumentos
        return render_template('resultados_pob.html', resultado=resultado, distancia_horizontal=distancia_horizontal, Altura_irradiacion_formula=Altura_irradiacion_formula, 
                           imagen_path=imagen_path, accesibilidad=accesibilidad, Nombre=Nombre )


@app.route('/Resultados_ocup', methods=['POST', 'GET'])
def mostrar_resultados_2():
    # Obtener los datos necesarios para mostrar en la plantilla
    resultado = request.args.get('resultado')
    distancia_horizontal = request.args.get('distancia_horizontal')
    Altura_irradiacion_formula = request.args.get('Altura_irradiacion_formula')
    imagen_path = request.args.get('imagen_path')  # Obtener la ruta de la imagen
    accesibilidad = request.args.get('accesibilidad')
    Nombre = request.args.get('Nombre')

    # Verificar si distancia_horizontal es igual a cero para mostrar el mensaje de alerta
    if distancia_horizontal == '0':
        flash('Altura mayor a distancia. No se puede medir', 'warning')

    if accesibilidad == '0':
        flash('No hay acceso de personas hacia la torre', 'warning')

    #PDF
    pdf_path = 'static/resultados.pdf'
    with PdfPages(pdf_path) as pdf:
        # Cargar la imagen generada del gráfico de resultados
        imagen = plt.imread(imagen_path)

        # Crear una nueva figura de matplotlib para el PDF
        fig, ax = plt.subplots(figsize=(8, 6))

        # Mostrar la imagen en la figura del PDF
        ax.imshow(imagen)
        ax.axis('off')  # Desactivar los ejes para la imagen

        texto = f'Distancia irradiante: {resultado}\n' \
                f'Distancia Horizontal: {distancia_horizontal}\n' \
                f'Altura de la antena: {Altura_irradiacion_formula}\n' \
                f'Resultados: Requiere medir y colocar el aviso correspondiente a {distancia_horizontal} metros de su antena'

        
        texto_obj = ax.text(0.05, 0.05, texto, transform=ax.transAxes, fontsize=10, verticalalignment='top')
        texto_obj.set_position((0.05, 0.000000009))

        # Guardar la figura en el PDF
        pdf.savefig(fig)
        
    # Renderizar la plantilla de resultados y pasar los datos como argumentos
    return render_template('resultados_ocup.html', resultado=resultado, distancia_horizontal=distancia_horizontal, Altura_irradiacion_formula=Altura_irradiacion_formula, 
                           imagen_path=imagen_path, accesibilidad=accesibilidad, Nombre=Nombre )

def generar_pdf():
    # Definir la ruta donde se guardará el PDF
    pdf_path = 'static/resultados.pdf'

    # Crear un objeto de documento PDF
    doc = SimpleDocTemplate(pdf_path, pagesize=letter)

    # Obtener los estilos de texto predefinidos
    styles = getSampleStyleSheet()

    # Crear una lista de elementos para el PDF
    elementos = []

    # Agregar párrafos de texto al PDF
    texto1 = """
    NO NECESITA MEDICIONES.\n
    Para las estaciones que cumplan con las distancias "r" (mínima distancia a la antena) 
    y "d" (mínima distancia horizontal), es decir, que no haya acceso de las personas a
    una distancia menor a "r" y "d", son declaradas Normalmente Conformes; esta condición también
    se presenta cuando la "a" (distancia vertical de la antena) es mayor que r, razón por la cual no se puede calcular d.
    \n
    """
    elementos.append(Paragraph(texto1, styles['Normal']))
    elementos.append(Spacer(1, 12))  # Espacio entre párrafos

    texto2 = """
    Aviso correspondiente:
    """
    elementos.append(Paragraph(texto2, styles['Normal']))

    # Agregar la imagen al PDF
    imagen_path = 'https://normograma.mintic.gov.co/mintic/graficas/resolucion_ane_0774_2018_obj_43.gif'
    imagen = Image(imagen_path, width=300, height=300)
    elementos.append(imagen)

    # Construir el PDF con los elementos proporcionados
    doc.build(elementos)

    # Retornar la ruta del PDF generado
    return pdf_path

@app.route('/generar_pdf')
def generar_pdf_route():
    # Llamar a la función para generar el PDF
    pdf_path = generar_pdf()
    
    # Devolver el PDF generado al usuario para descargarlo
    return send_file(pdf_path, as_attachment=True)


@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        apellido = request.form['apellido']
        username = request.form['username']
        password = request.form['password']
        pregunta = request.form['pregunta']
        respuesta = request.form['respuesta']
        
        
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO usuarios (nombre, apellido, correo, clave, pregunta_seguridad, respuesta) VALUES (%s, %s, %s, %s, %s, %s)', (nombre, apellido, username, password, pregunta, respuesta))
        mysql.connection.commit()
        cursor.close()
        return redirect('/login')
    return render_template('registro.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        cursor = mysql.connection.cursor()
        cursor.execute('SELECT * FROM usuarios WHERE correo = %s AND clave = %s', (username, password))
        user = cursor.fetchone()
        cursor.close()
        
        if user:
            session['username'] = user[6]
            # Redirigir al usuario a la página desde la que inició sesión
            next_url = session.get('next_url')
            print("Next URL:", next_url)  
            if next_url and next_url != 'http://127.0.0.1:5000/registro':
                return redirect(next_url)
            else:
                return redirect('/')
        else:
            error_message = 'Usuario o contraseña incorrectos'
            return render_template('login.html', error=error_message)
    
    # Guardar la URL de la página anterior en la sesión
    session['next_url'] = request.referrer
    return render_template('login.html')

#función para la creación de comentarios
@app.route('/comentarios', methods=['GET', 'POST'])
def comentarios():
    if request.method == 'POST' and 'username' in session:
        comment_text = request.form['comentario']
        user_id = session['username']
        
        print(user_id)
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO comentarios (comentario, usuario_id, fecha_creacion) VALUES (%s, %s, %s)', (comment_text, user_id, current_date))
        mysql.connection.commit()
        cursor.close()
        
        return redirect('/comentarios')
    
    
    comentarios_list = []
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT usu.nombre, comentario FROM comentarios inner join usuarios usu on comentarios.usuario_id = usu.Id')
    comentarios = cursor.fetchall()
    
    cursor.close()

    for comentario in comentarios:
        
        comentario_info = {
            'id': comentario[0],  
            'contenido': comentario[1]
        }

        comentarios_list.append(comentario_info)

    return render_template('comentarios.html', comentarios=comentarios_list)

@app.route('/logout')
def logout():
    # Guardar la URL actual en la sesión
    session['logout_redirect'] = request.referrer
    
    # Eliminar el nombre de usuario de la sesión
    session.pop('username', None)
    
    # Redirigir al usuario a la página en la que estaba antes de cerrar sesión
    return redirect(session.get('logout_redirect', url_for('comentarios')))


if __name__ == '__main__':
    app.run(debug=True, threaded=False)