## Purpose

Permitir que cada chatbot seleccione de forma segura un modelo Vertex AI
validado, sin depender de un único modelo de entorno ni modificar el historial.

## ADDED Requirements

### Requirement: Explicit Vertex model catalogue

El sistema SHALL obtener los modelos Vertex seleccionables de una configuración
explícita y validada. `VERTEX_MODEL` SHALL conservarse como modelo
predeterminado compatible durante la transición. El catálogo SHALL contener solo
identificadores autorizados para el proyecto y ubicación configurados.

#### Scenario: Multiple enabled models

- **WHEN** se configuran varios modelos Vertex válidos
- **THEN** el editor muestra esos modelos bajo el proveedor Vertex AI y permite guardar uno para un chatbot

#### Scenario: Invalid configured model

- **WHEN** un identificador Vertex configurado no cumple la validación o no está disponible
- **THEN** el sistema no lo publica como seleccionable y explica la indisponibilidad sin sustituir otro modelo automáticamente

### Requirement: Historical model identity

El sistema SHALL conservar la identidad del modelo registrado en consultas
anteriores cuando cambie el modelo actual de un chatbot o cuando se retire una
opción del catálogo.

#### Scenario: Change chatbot model

- **WHEN** un administrador cambia un chatbot de un modelo Vertex a otro modelo habilitado
- **THEN** las consultas posteriores usan el nuevo modelo y las anteriores conservan el modelo con el que se ejecutaron
