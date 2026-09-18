# Evidencia AA2-EV03 · Analítica de datos con IA generativa

Kit para grabar la evidencia **AA2-EV03 · Video configuración de analítica de datos**
usando **Gemini** como herramienta de analítica.

Programa de formación: *Aplicación de la inteligencia artificial en la integración de datos*
· Resultado de aprendizaje **220501115-02**.

## Qué hay aquí

| Archivo | Para qué sirve |
|---|---|
| `datos/ventas_tienda_tecnologia.csv` | El archivo que subes a Gemini. 511 registros, 11 columnas, sucio a propósito. |
| `guion/prompts-gemini.md` | Los nueve prompts en orden, listos para copiar y pegar. |
| `guion/guion-video.md` | Qué mostrar y qué decir minuto a minuto, y cómo cumple cada criterio. |
| `guion/resultados-esperados.md` | Cifras de referencia para verificar que Gemini responde bien. |
| `entrega/AA2-EV03-guia-para-grabar.mp4` | Video guía de 3:40 (4 MB) con los prompts y los valores esperados. |
| `entrega/AA2-EV03-entrega.pdf` | Documento de entrega, con los campos y las capturas por completar. |

> El video guía **no es la evidencia**. La evidencia es tu propia grabación de pantalla,
> con tu voz y tu cuenta de Gemini. La guía existe para que esa grabación te salga bien
> en el primer intento.

## Cómo grabar

1. Abre una conversación nueva en [gemini.google.com](https://gemini.google.com).
2. Empieza a grabar la pantalla (`Win + G` en Windows, `Cmd + Shift + 5` en Mac, u OBS).
3. Sube `datos/ventas_tienda_tecnologia.csv` y sigue `guion/prompts-gemini.md` en orden.
4. Narra según `guion/guion-video.md`, apoyándote en las cifras que aparecen en pantalla.
5. Sube el video, pega el enlace en el PDF y verifícalo en una ventana de incógnito.

## El conjunto de datos

Ventas de una tienda de tecnología con imperfecciones deliberadas, para que la limpieza
tenga algo real que corregir:

- 31 registros duplicados (doble registro en caja)
- 69 celdas vacías en `precio_unitario`, `total` y `calificacion_cliente`
- 9 registros con `unidades` negativas
- 3 formatos de fecha mezclados
- 106 montos escritos como texto (`$ 1.234.500`)
- 14 variantes de escritura para 7 ciudades y 10 para 5 categorías
- Atípicos de `total` inflados 12 veces

La relación que debe encontrar la regresión: el descuento impulsa las unidades vendidas
(`unidades ≈ 2,04 + 0,221 · descuento_pct`, R² = 0,796 tras la limpieza).

## Reproducir los archivos generados

```bash
npm install
npm run dataset      # regenera el CSV (determinista, misma semilla)
npm run referencia   # imprime las cifras de referencia
npm run video        # regraba el video guía y lo comprime bajo 10 MB
npm run pdf          # regenera el PDF desde entrega/informe.html
```

El video se graba con el Chromium de Playwright sobre `video/guia.html` y se comprime con
`ffmpeg`; el script sube el CRF automáticamente si el archivo supera los 10 MB.
