# GitHub Actions - Compilación Automática Multi-plataforma

## Descripción

Este repositorio está configurado con **GitHub Actions** para compilar automáticamente ejecutables de PROCOME Qt para **Linux y Windows** cada vez que:

- Haces push a las ramas `main` o `master`
- Creas una Pull Request
- Creas un Release
- Lo ejecutas manualmente desde la pestaña "Actions"

---

## 📦 Descargar Ejecutables Compilados

### Desde GitHub Actions

1. Ve a la pestaña **"Actions"** en GitHub
2. Selecciona el workflow **"Build Executables"**
3. Clickea en el run más reciente (con ✅ verde)
4. En la sección **"Artifacts"**, descarga:
   - `PROCOME-Linux-x64` - Ejecutable para Linux
   - `PROCOME-Windows-x64` - Ejecutable para Windows

### Desde Releases

Si se crea un Release en GitHub, los ejecutables se adjuntan automáticamente:

1. Ve a la pestaña **"Releases"**
2. Descarga el ejecutable para tu plataforma
3. También descarga `PROCOME.cfg`

---

## 🚀 Cómo Funciona

### Workflow de GitHub Actions

El archivo [`.github/workflows/build.yml`](.github/workflows/build.yml) define:

1. **Matrix Strategy**: Compila en paralelo para Linux y Windows
2. **Instalación automática**: Python, dependencias y PyInstaller
3. **PyInstaller**: Crea ejecutables standalone (--onefile)
4. **Artifacts**: Sube ejecutables a GitHub (90 días de retención)
5. **Releases**: Adjunta automáticamente ejecutables a releases

### Plataformas Soportadas

| Plataforma | Runner | Ejecutable | Tamaño Aprox. |
|------------|--------|------------|---------------|
| Linux x64  | `ubuntu-latest` | `PROCOME-Linux` | ~266 MB |
| Windows x64 | `windows-latest` | `PROCOME-Windows.exe` | ~280 MB |

---

## 🛠️ Compilación Local

### Linux

```bash
./build.sh
```

El ejecutable se creará en `dist/PROCOME`

### Windows

```batch
build_windows.bat
```

El ejecutable se creará en `dist\PROCOME.exe`

---

## 📋 Requisitos Previos (solo para compilación local)

### Linux
- Python 3.12+
- Dependencias del sistema: `libxcb-cursor0`

### Windows
- Python 3.12+
- Ninguna dependencia adicional

---

## ⚙️ Ejecutar Workflow Manualmente

1. Ve a **Actions** → **Build Executables**
2. Click en **"Run workflow"**
3. Selecciona la rama
4. Click en **"Run workflow"** verde
5. Espera ~5-10 minutos
6. Descarga los artifacts generados

---

## 📝 Crear un Release con Ejecutables

```bash
# Crear un tag
git tag v1.0.0
git push origin v1.0.0

# Crear release desde GitHub UI
# Los ejecutables se adjuntarán automáticamente
```

O desde la línea de comandos con GitHub CLI:

```bash
gh release create v1.0.0 --title "PROCOME v1.0.0" --notes "Descripción del release"
```

---

## 🔧 Personalizar el Build

Edita [`.github/workflows/build.yml`](.github/workflows/build.yml) para:

- Cambiar versiones de Python
- Añadir más plataformas (macOS)
- Modificar opciones de PyInstaller
- Cambiar retención de artifacts
- Añadir tests antes del build

---

## 📂 Estructura de Archivos

```
.github/
└── workflows/
    └── build.yml          # Workflow de GitHub Actions

build.sh                   # Script de compilación Linux
build_windows.bat          # Script de compilación Windows
requirements.txt           # Dependencias Python
PROCOME_Arranque_Qt.py    # Entrada principal de la app
```

---

## ✅ Estado del Build

El badge del estado del build:

```markdown
![Build Status](https://github.com/TU_USUARIO/TU_REPO/workflows/Build%20Executables/badge.svg)
```

Reemplaza `TU_USUARIO` y `TU_REPO` con tus valores reales.

---

## 🐛 Solución de Problemas

### El workflow falla en Linux
- Verifica que todas las dependencias estén en `requirements.txt`
- Asegúrate que `libxcb-cursor0` esté instalada en el workflow

### El workflow falla en Windows
- Revisa la sintaxis de PowerShell (backticks `` ` `` en vez de `\`)
- Verifica la sintaxis de `--add-data` (usa `;` en Windows, `:` en Linux)

### Los artifacts no se suben
- Verifica los permisos del repositorio
- Asegúrate que el workflow tenga permisos de escritura

---

## 📚 Documentación Adicional

- [Documentación de PyInstaller](https://pyinstaller.org/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Executable Usage Guide](EJECUTABLE.md)
