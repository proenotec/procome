# Ejecutable PROCOME Qt - Guía de Uso

## Compilación Exitosa ✅

Se ha compilado exitosamente PROCOME Qt en un ejecutable standalone de **266 MB**.

## Ubicación del Ejecutable

```
dist/PROCOME
```

## Cómo Ejecutar

### Método 1: Desde el directorio del proyecto
```bash
./dist/PROCOME
```

### Método 2: Copiar a cualquier ubicación
```bash
# Copiar el ejecutable y configuración
cp dist/PROCOME /ruta/destino/
cp PROCOME.cfg /ruta/destino/

# Ejecutar desde la nueva ubicación
cd /ruta/destino
./PROCOME
```

## Distribución

Para distribuir PROCOME, necesitas incluir:

1. **PROCOME** - El ejecutable compilado (266 MB)
2. **PROCOME.cfg** - Archivo de configuración

No es necesario instalar Python ni dependencias en el sistema destino.

## Recompilar

Para recompilar la aplicación después de hacer cambios:

```bash
./build.sh
```

Esto:
- Limpia las compilaciones anteriores
- Compila nuevamente con PyInstaller
- Genera un nuevo ejecutable en `dist/PROCOME`

## Características

- ✅ Ejecutable standalone (no requiere Python)
- ✅ Todas las dependencias incluidas (PySide6, pyserial, etc.)
- ✅ Interfaz gráfica Qt completa
- ✅ 266 MB de tamaño
- ✅ Compatible con Linux x86_64

## Compatibilidad

- **SO**: Linux (64-bit)
- **Arquitectura**: x86_64
- **Dependencias del sistema**: Solo las bibliotecas estándar de Linux y Qt

## Notas

- Los warnings sobre bibliotecas Qt opcionales durante la compilación son normales y no afectan la funcionalidad
- El ejecutable es un binario ELF que puede ejecutarse directamente
- La primera ejecución puede tardar unos segundos mientras extrae los recursos empaquetados
