import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

años = int(input("Cuantos años de datos quieres generar? "))
inicio = int(input("A partir de que año quieres generar los datos? "))
meses = 12*años

print("Que componente quieres generar? (1 - Tendencia, 2 - Estacionalidad)")
comp = int(input("Ingresa el número del componente: "))

if comp not in [1, 2]:
    print("Componente inválido. Por favor ingresa un número entre 1 y 2.")
    exit()
elif comp == 1:
    print("Generando Tendencia...")
    comienzo = int(input("Ingresa el valor inicial de la tendencia: "))
    fin = int(input("Ingresa el valor final de la tendencia: "))
    valores = np.linspace(comienzo, fin, meses)

elif comp == 2:
    print("Generando Estacionalidad...")
    i = np.arange(meses)

    # Componente cíclico (oscila alrededor de 0)
    amplitud = int(input("Ingresa la amplitud de la estacionalidad: "))
    periodo = int(input("Ingresa el periodo de la estacionalidad (en meses): "))
    ciclo = amplitud * np.sin(2 * np.pi * i / periodo)

    # Componente de tendencia (crece linealmente)
    base = 100000
    crecimiento_mensual = 800  # cuánto sube el "piso" cada mes
    tendencia = base + crecimiento_mensual * i

    # Combinar: la tendencia es el "piso" que sube, el ciclo oscila sobre ese piso
    valores = tendencia + ciclo

    ruido = np.random.normal(1.0, 0.03, meses)
    valores = (valores * ruido).round(2)
    


fechas = pd.date_range(start=f'{inicio}-01-01', periods=meses, freq='MS')

df = pd.DataFrame({
    'fecha': fechas.strftime('%Y-%m'),  # formatea como "2025-01" en vez de fecha completa
    'valores': valores
})
print(df)
df.to_csv('historial_financiero.csv', index=False)


df.plot(x='fecha', y='valores', kind='line', figsize=(12, 5))
plt.title('Historial Financiero')
plt.xlabel('Fecha')
plt.ylabel('Ingresos')
plt.xticks(rotation=45)  # rota las fechas para que no se encimen
plt.tight_layout()
plt.show()
#plt.savefig('grafica.png')