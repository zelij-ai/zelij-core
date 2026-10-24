# Zelij Core

[English](README.en.md) · [简体中文](README.zh-CN.md) · [繁體中文](README.zh-TW.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Türkçe](README.tr.md) · [Русский](README.ru.md) · [Tiếng Việt](README.vi.md) · [ไทย](README.th.md) · [Deutsch](README.de.md) · **Español** · [Français](README.md) · [Українська](README.uk.md) · [Polski](README.pl.md) · [Português (Brasil)](README.pt-BR.md) · [العربية](README.ar.md) · [فارسی](README.fa.md) · [Bahasa Indonesia](README.id.md) · [Italiano](README.it.md) · [Ελληνικά](README.el.md) · [മലയാളം](README.ml.md) · [Roman Urdu](README.ur.md) · [Română](README.ro.md)

[![ci](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml/badge.svg)](https://github.com/zelij-ai/zelij-core/actions/workflows/ci.yml) [![version](https://img.shields.io/github/v/release/zelij-ai/zelij-core?label=version)](https://github.com/zelij-ai/zelij-core/releases) [![license](https://img.shields.io/badge/license-AGPL--3.0-1c1917)](LICENSE)

**Monte su startup 100 % nativa en IA.** Una oficina donde cuatro agentes trabajan para usted: ellos proponen, usted decide. Su máquina, su clave Claude, sus datos; nada llama a casa.

![El acuario de Zelij Core: el fundador y cuatro agentes conversan, proponen decisiones y ejecutan lo aprobado](docs/img/aquarium.gif)

*El acuario en un día simulado (aquí en francés). En su instalación, cada tarjeta es una acción real de sus agentes, en directo y reproducible durante veinticuatro horas. El oro es usted: nada vinculante ocurre antes de su decisión. Los rostros son personajes ficticios.*

## Qué hace el núcleo

- **La oficina**: una página. Las decisiones pendientes, una petición al jefe de gabinete, las últimas ejecuciones con su coste, el diario, los agentes, los módulos instalados.
- **El paquete de decisión**: objetivo, propuesta, por qué ahora, opciones, recomendación, riesgos, reversibilidad, plan, marcha atrás, impacto. Un paquete incompleto no se abre. Aprobar, rechazar o pedir cambios con una consigna obligatoria transmitida al agente.
- **Las reglas de la casa**: nada que comprometa (dinero, exposición pública, borrado, irreversible) se hace sin decisión; un hecho lleva fecha y fuente o se marca «no verificado»; el diario no se borra.
- **La pasarela**: la clave Claude del fundador, el coste de cada llamada calculado a partir del uso y de las tarifas públicas fechadas, un tope mensual que bloquea.
- **El ejecutor**: un bucle de llamadas acotado (presupuesto de turnos por agente), herramientas sobrias, una negativa del modelo tratada como un resultado.
- **Los módulos**: la única forma de extender el núcleo. Interfaz estable, manifiesto `pack.json` firmado con Ed25519 por el editor, huella de cada fichero cubierta por la firma, verificación antes de instalar. Los destinos de despliegue y los agentes adicionales pasan por aquí.
- **Finanzas**: ventas confirmadas (importación de Stripe en solo lectura o registro con justificante), gastos declarados que se repiten cada mes, coste de los agentes medido, diario del mes, exportación CSV para el contable. Nada se declara ni se factura.
- **Contactos**: una ficha por persona, base legal obligatoria, plazo de conservación, intercambios, derechos ejercidos; un contacto que se opone no recibe nada más, un contacto vencido se olvida y solo queda el diario de derechos.
- **Publicación**: una página redactada por el agente de marketing se convierte en borrador, luego en decisión; aprobada, se propone al sitio como pull request de GitHub o borrador de WordPress. El último gesto, fusionar o publicar, es suyo.
- **En el bolsillo**: cada decisión llega a su teléfono, por correo con dos enlaces firmados de un solo uso, o por Telegram con tres botones. Usted aprueba desde la cola del metro; el acuario se mueve en cuanto responde. La misma puerta, el mismo diario que desde el escritorio.
- **Acuario**: vea trabajar a sus agentes; cada burbuja es una acción real de las últimas 24 horas, los anillos punteados son puestos libres. Una página pública compartible, con insignia «by zelij.ai».
- **Catálogo**: lo que la edición libre no contiene, nombrado con honestidad; un módulo comprado al editor se instala aquí, firmado y verificado. Ningún pago pasa por la oficina.
- **Software factory**: el Constructor lee y propone sobre un único repositorio, mediante pull requests que pasan la puerta de seguridad (300 líneas, solo texto, ningún secreto, ningún fichero de infraestructura, dependencias sin vulnerabilidad conocida según OSV); puesta en línea en un servidor Linux por SSH o en OVH (dominio y DNS por la API) con conmutación atómica, prueba de humo y marcha atrás; sonda del dominio; copia de seguridad diaria de la oficina. Nunca fusiona, nunca paga, nunca toca la oficina.
- **Los agentes**: una carpeta por agente, un `agent.md` con una cabecera simple y consignas en francés. Cuatro agentes: Camille Aubert (jefa de gabinete), Élise Tanguy (crecimiento, marketing y productos), Nour Bellamy (finanzas y clientes), Sacha Ferrand (constructor, software factory). El fundador se dirige a cada uno desde la oficina; un paquete aprobado que designa un agente y una tarea se ejecuta de inmediato, dentro de los límites del plan.

## Probar en un minuto, sin clave

```bash
git clone https://github.com/zelij-ai/zelij-core.git && cd zelij-core
docker compose -f docker-compose.demo.yml up --build
```

Abra `http://localhost:8000` y entre en la demostración: una empresa ficticia, cuatro agentes simulados, decisiones que aprobar, el acuario que reproduce su jornada. Ninguna clave, ninguna cuenta, ningún coste; nada se envía a un modelo y todo desaparece al parar. Cuando esté convencido, pase a la instalación real más abajo. La oficina en sí está en francés.

## Arrancar

```bash
cp .env.example .env     # clave Claude, tope, SECRET_KEY, contraseña de la base
docker compose up -d --build
```

La oficina responde en `http://localhost:8000`. Sin SMTP, el enlace de conexión se escribe en los registros del contenedor (`docker compose logs core-app`).

Guías completas (en inglés): **[Instalación](docs/INSTALLATION.en.md)** (máquina vacía → oficina en https, SMTP, software factory, copias de seguridad, resolución de problemas), **[Manual de uso](docs/MODE-D-EMPLOI.en.md)** (cada página, los agentes, las decisiones, el coste). Las fotos del fundador y de los agentes se dejan en [`portraits/`](portraits/README.md) (descripción en francés).

Desde la imagen publicada, sin construcción local (`CORE_IMAGE_TAG=v…` en `.env` fija la versión):

```bash
docker compose -f docker-compose.yml -f docker-compose.image.yml up -d
```

En local sin Docker:

```bash
pip install -r requirements-dev.txt
uvicorn core.bureau.app:app --reload
```

## Clave pública del editor

Los módulos del catálogo están firmados por zelij.ai. La clave pública que hay que poner en `ZELIJ_CLE_PUBLIQUE` (ya rellenada en `.env.example`):

```
8da6c92455558c15a1566b333cef22fb5fc60aad9ffbf811f372e4bb7eacc42a
```

## Seguridad

Lo que el núcleo garantiza, y que está probado (`tests/test_securite.py`):

- **Módulos**: un módulo solo se instala y se ejecuta firmado por el editor (Ed25519), y la firma cubre la huella SHA-256 de cada fichero de código: un fichero modificado, añadido o retirado después de la firma deja el módulo fuera de juego.
- **Conexión**: enlaces de un solo uso de 20 minutos, con hash en la base; frenos por dirección, por IP y global sobre las peticiones de enlace, para que la oficina nunca sirva de relé de correo; sin SMTP configurado en producción, no se crea ni se registra ningún enlace.
- **Formularios**: cookie de sesión HMAC `HttpOnly` `SameSite=Strict`, control de origen y token anti-CSRF por sesión en cada POST.
- **Páginas**: política de seguridad de contenido estricta (`default-src 'self'`, ningún script en línea, ningún marco), `nosniff`, `X-Frame-Options`, `Referrer-Policy`, HSTS cuando el origen es https.
- **Agentes**: lo que un agente lee (página web, fichero del repositorio) le llega enmarcado como contenido externo, nunca como consigna; un agente solo ejecuta las herramientas de su ficha y, en cuanto ha leído un dato privado, solo puede llamar al sitio de la empresa; solo lee direcciones https públicas (direcciones privadas, de bucle local, de enlace local y nombres internos rechazados en cada salto de redirección, respuesta acotada); la puerta de seguridad bloquea secretos, ficheros de infraestructura, scripts de terceros, marcos y llamadas de red.
- **Contenedor**: usuario sin privilegios, sistema de ficheros en solo lectura, ninguna capacidad, sin elevación; la clave del servidor SSH puede fijarse (`SSH_CLE_HOTE`).
- **Exportación contable**: las celdas que parecen una fórmula de hoja de cálculo se neutralizan.

Para informar de una vulnerabilidad: `securite@zelij.ai`, sin publicarla antes de la corrección. Antes de cada versión, `pip-audit -r requirements.txt` y `bandit -r core scripts -ll` deben estar vacíos.

## Contribuir y seguir las versiones

`CONTRIBUTING.md` (en francés) explica cómo una contribución llega a una versión, incluida la regla: un destino de despliegue contribuido vale el pack correspondiente gratis de por vida. `SECURITY.md` explica cómo informar de una vulnerabilidad. `CHANGELOG.md` dice qué cambia cada versión y qué le queda por hacer al fundador.

## Pruebas y control de publicación

```bash
python -m pytest -q
python scripts/controle_publication.py
```

El control de publicación rechaza claves, direcciones IP, códigos internos, direcciones personales, contraseñas en claro y los términos de una lista privada (`ZELIJ_CORE_INTERDITS`) que nunca forma parte del repositorio.

## Licencia

GNU AGPL v3. Copyright (C) 2026 zelij.ai. Puede usar, modificar y redistribuir el núcleo, a condición de publicar sus modificaciones bajo la misma licencia. La edición completa que hace funcionar zelij.ai sigue siendo la del editor.

by zelij.ai — https://zelij.ai/
