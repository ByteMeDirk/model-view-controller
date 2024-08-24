# Model-View-Controller (MVC) Database Schema Manager

This WORK IN PROGRESS project provides a command-line interface (CLI) tool for managing database schemas using a
Model-View-Controller (MVC) architecture. It allows users to define database models using YAML files and automatically
build or drop database tables based on these configurations.

Future features would :

- Development of a more robust template system for generating database-related code and scripts based on the defined
  models.
- Expansion of database support beyond PostgreSQL to include other popular databases like MySQL, SQLite, and Oracle.
- Generation of schema change reports for auditing and documentation purposes.
- Addition of new CLI commands for tasks such as data seeding, schema comparison, and generating migration scripts.
- Implementation of a dry-run mode to preview schema changes without applying them.

## Purpose

The main purpose of this tool is to simplify database schema management by:

1. Allowing developers to define database models using easy-to-read YAML files.
2. Automatically creating and updating database tables based on model definitions.
3. Providing a simple CLI interface for building and dropping database schemas.
4. Supporting schema versioning and migrations through file-based model definitions.

## Key Components

The solution consists of several Python modules:

1. `controller.py`: Handles the logic for creating, updating, and dropping database tables.
2. `config.py`: Manages configuration file reading and model file discovery.
3. `model.py`: Defines the base Model class and provides utilities for creating SQLAlchemy models from YAML
   configurations.
4. `view.py`: Contains a simple View class for rendering templates (not extensively used in the current implementation).
5. `__init__.py`: Defines the main CLI commands and orchestrates the overall process.

## How It Works

1. The user defines database models using YAML files (e.g., `users.yml`).
2. The user creates a `config.yaml` file with database connection details.
3. The CLI tool reads the configuration and model files.
4. When building the schema, the tool:
    - Creates new tables if they don't exist.
    - Updates existing tables by adding new columns, removing deleted columns, and updating column types.
5. When dropping the schema, the tool removes all tables defined in the models.

## Usage

### Prerequisites

- Python 3.6+
- SQLAlchemy
- PyYAML
- Click

### Installation

1. Clone the repository or download the source code.
2. Install the required dependencies:

```bash
pip install sqlalchemy pyyaml click
```

### Defining Models

Create YAML files for each database model in the project directory. For example, `users.yml`:

```yaml
columns:
  - name: id
    type: integer
    primary_key: true
    auto_increment: true
  - name: name
    type: string
    length: 100
  - name: email
    type: string
    length: 100
  - name: password
    type: string
    length: 100
  - name: created_at
    type: timestamp
description: "Users table"
```

### Configuration

Create a `config.yaml` file in the project directory:

```yaml
database:
  connection: "postgresql://postgres:postgres@localhost:5432/postgres"
  schema: "public"
```

### Building the Schema

To build the database schema based on the model definitions, run:

```bash
python -m model_view_controller build ./mvc_customer
```

This command will:

1. Read the `config.yaml` file for database connection details.
2. Discover all YAML model files in the specified directory.
3. Create or update database tables based on the model definitions.
4. Log the actions taken for each table.

### Dropping the Schema

To drop all tables defined in the models, run:

```bash
python -m model_view_controller drop ./mvc_customer
```

This command will:

1. Read the `config.yaml` file for database connection details.
2. Drop all tables in the specified schema.
3. Log the action.

## Example Workflow

1. Create a directory called `mvc_customer`.
2. Add the `users.yml` and `config.yaml` files to this directory.
3. Run the build command:

```bash
python -m model_view_controller build ./mvc_customer
```

4. The tool will create the `users` table in the specified database.
5. To drop the schema, run:

```bash
python -m model_view_controller drop ./mvc_customer
```

6. The tool will drop the `users` table from the database.

## Limitations and Future Improvements

1. Currently supports a limited set of column types and options.
2. Does not handle complex relationships between models.
3. Lacks support for index creation and management.
4. Could benefit from more robust error handling and validation.
5. May need additional features for managing database migrations and versioning.

## Conclusion

This Model-View-Controller Database Schema Manager provides a simple and flexible way to manage database schemas using
YAML configurations. It's particularly useful for projects that require frequent schema changes or need to maintain
multiple database environments with consistent schemas.


