import sys
import os

# Agrega src/ al sys.path para que los tests puedan importar los módulos correctamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))