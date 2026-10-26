## Purpose

Hacer que la vista previa interna ejercite el mismo envío de contexto visible
que se espera de una integración real del widget en un dashboard.

## ADDED Requirements

### Requirement: Preview dashboard context

La vista previa SHALL montar el widget con un selector de contexto explícito
que apunte solo al tablero de demostración. Cada consulta desde la vista previa
SHALL enviar el texto visible de ese tablero a través del campo REST
`page_context`, aplicando los mismos límites y exclusiones del widget externo.

#### Scenario: Preview question about a KPI

- **WHEN** el visitante pregunta por un valor visible del tablero de demostración
- **THEN** la solicitud incluye dicho valor en `page_context` y no incluye controles, navegación ni el propio panel del chat

#### Scenario: Preview selector is unavailable

- **WHEN** el selector configurado no encuentra el tablero de demostración
- **THEN** la consulta se envía sin `page_context` y el widget permanece utilizable

### Requirement: Current page context per turn

El widget SHALL volver a recopilar el contexto visible seleccionado en cada
consulta. Un cambio del tablero entre turnos SHALL reemplazar el contexto de la
página anterior y no reutilizarlo como si fuera actual.

#### Scenario: Dashboard value changes

- **WHEN** cambia un valor visible del tablero antes de una consulta posterior
- **THEN** la nueva solicitud contiene el valor actualizado y no el valor visible en la consulta anterior
