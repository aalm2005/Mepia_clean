# Continuidad del chatbot de MEPIA

Estas instrucciones aplican a cualquier trabajo relacionado con el chatbot de
MEPIA dentro de este repositorio.

## Lectura obligatoria

Antes de analizar, diseñar, implementar o validar cualquier cambio del chatbot,
leer completos y en este orden:

1. `docs/chatbot_corrections.md`
2. `docs/mepia_v4_metricas_diseno.md`
3. `.kiro/specs/mepia/n15_chat_consulta.md`

`docs/chatbot_corrections.md` es la fuente de verdad del avance. Se debe continuar
desde el primer trabajo obligatorio marcado como pendiente. No se deben deshacer,
repetir ni presentar como pendientes las correcciones ya terminadas, salvo que una
prueba nueva demuestre una regresión y esta quede registrada en la bitácora.

## Clasificación del trabajo

Mantener separadas las siguientes categorías:

- Correcciones de defectos encontradas durante la revisión del Paso 1.
- Trabajo obligatorio de robustez necesario para cerrar el Paso 1.
- Mejoras adicionales de robustez y validación.
- Preparación y controles para producción.
- Fases posteriores del chatbot.

Una “corrección” numerada no equivale a un “paso” o fase del chatbot. No adelantar
trabajo de una categoría distinta sin registrarlo y justificarlo.

## Actualización de la bitácora

Después de cada cambio, actualizar `docs/chatbot_corrections.md` con información
obtenida del repositorio y de las ejecuciones reales:

- Rama actual.
- Commit que contiene el cambio, o `sin commit` si todavía no existe.
- Archivos modificados.
- Pruebas o verificaciones ejecutadas, con su resultado exacto.
- Estado del trabajo y siguiente acción pendiente.

No inventar commits, pruebas, resultados, despliegues ni validaciones. No afirmar
que una prueba pasó si no se ejecutó o si su resultado no está disponible. Cuando
una prueba encuentre un defecto nuevo, agregarlo a la categoría correspondiente de
la bitácora; las cuatro correcciones iniciales no son un límite.

## Seguridad y producción

- No desplegar ni modificar producción sin autorización explícita del usuario.
- Distinguir siempre entre validación local, entorno `MEPIA - PRUEBAS`, consultas
  de solo lectura en producción y despliegue real.
- Mantener el chatbot en modo de solo lectura hasta implementar autenticación y
  autorización que demuestren que el usuario puede consultar el `business_id`.
- Conservar todos los cambios existentes y no revertir trabajo ajeno o terminado.

