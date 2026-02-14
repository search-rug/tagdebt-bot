# Contributing to TagDebt Bot

Welcome! This document provides guidelines for contributing to the TagDebt Bot project.

## General Guidelines

-   **Code Style**: Follow PEP 8 for Python code.
-   **Architecture**: The project is split into two main services: `Bot` (webhook receiver) and `ModelsBackend` (ML model serving).
-   **Environment**: Most development is done via Docker Compose. Ensure you have Docker installed.

## Development Setup

1.  **Clone and Configure**: Follow the `README.md` instructions to set up your secrets and keys.
2.  **Run with Watch**: Use `docker compose up` and `docker compose watch` to have your changes automatically synchronized into the containers.
3.  **Local Testing**: You can run the Python files locally if you install the dependencies from `requirements.txt` in a virtual environment.

---

## Service Specifics

### 1. Bot Service (`/Bot`)

The Bot service handles GitHub events and coordinates the classification logic.

-   **Adding Commands**: Commands are parsed in `Bot/app.py` within `handle_issue_comment_event`.
-   **Event Handling**: Webhook events are processed in `bot()` and routed to specific handlers like `handle_issue_creation_event`.
-   **Email Templates**: Email logic is in `Bot/emailSender.py`. Templates are configured via `config.json`.
-   **Lingering Issues**: The background processing for inactive issues is in `Bot/lingeringIssuesProcessor.py`.

### 2. Models Backend Service (`/ModelsBackend`)

The Models Backend uses a plugin-based architecture to allow easy addition of new Machine Learning models or classification logic. It is designed as a **Shared Service**, meaning a single deployment can host multiple different models simultaneously.

#### Design Rationale: Why Multiple Plugins/Models?

-   **A/B Testing**: Run and compare the performance of different model versions (e.g., Deep Learning vs. LLM) in real-time.
-   **Multi-Tenancy**: Serve different classification needs for different GitHub repositories or external tools from a single backend instance.
-   **Ensemble Logic**: Allow clients to aggregate results from multiple models for higher precision.
-   **Zero-Downtime Migration**: Test a new plugin version alongside the old one before switching.

#### Architecture Overview

The system distinguishes between **Plugins** (Blueprints) and **Models** (Instances).

##### Plugins (The Blueprints)
A plugin is a Python module that defines a model implementation. 
- **Location**: Typically placed in `plugins/`.
- **Requirement**: Must have an `initialize()` function that calls `model.factory.register_model(type_name, class_reference)`.
- **Registration**: The module path (e.g., `plugins.satd_li_2022.model`) must be added to the `"plugins"` list in `config.json`.

##### Models (The Instances)
Models are specific configurations of a plugin.
- **Registration**: Defined in the `"models"` list in `config.json`.
- **Properties**:
    - `type`: Must match a registered `type_name` from a plugin.
    - `name`: The unique identifier for this instance. This name becomes part of the API endpoint: `/models/{name}`.
    - `parameters`: A dictionary of arguments passed to the class constructor (`__init__`).

#### Example Workflow: Adding a New Model

1. **Implement**: Create `plugins/my_plugin/model.py`.
    ```python
    from model import factory

    class MyClassifier:
        def __init__(self, threshold):
            self.threshold = threshold
        def label(self, text):
            return "SATD" if len(text) > self.threshold else "non-SATD"

    def initialize():
        factory.register_model("MySimpleClassifier", MyClassifier)
    ```
2. **Configure**: Update `config.json`.
    ```json
    {
        "plugins": ["plugins.my_plugin.model"],
        "models": [
            {
                "type": "MySimpleClassifier",
                "name": "Length_Classifier_50",
                "parameters": { "threshold": 50 }
            }
        ]
    }
    ```
3. **Use**: The model is now available at `POST /models/Length_Classifier_50`.
